from jinja2 import Environment, FileSystemLoader
import re, os, time, sys, glob, json
from subprocess import Popen, PIPE
import logging
import calendar
import datetime
import numpy as np


PATH = os.path.dirname(os.path.abspath(__file__))
TEMP_ENV = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../templates')),
    trim_blocks=False)

def diff_month(d1, d2):
    return (d1.year - d2.year)*12 + d1.month - d2.month

################# slurm stuff ##########################


def submit_job(filename):
    '''Either you get a job id, and your job will run, or you don't
    and your job won't run, so you check out and err to see why.'''
    global _submission_script
    process = Popen("sbatch "+filename, shell=True,
                    stdout=PIPE, stderr=PIPE)
    returncode = process.returncode
    (out,err) = process.communicate()
    jobid = out.split()[-1]
    return (jobid, out, err)

def get_job_state(jobid):
    process = Popen('scontrol show jobid %s' % (str(jobid),), shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    status={}
    if out.split()[0].startswith('JobId'):

        for k in out.split():
            status[k.split('=')[0]] = k.split('=')[1]
    else:
        status = None

    return status

def is_job_done(jobid):
    '''Assume job did start, so if the checkjob never heard of this job
    it must already have finished.'''
    state=get_job_state(str(jobid))
    if state:
        if state['JobState']=='COMPLETED':
            return True
        elif state['JobState']=='FAILED':
            return True
        elif state['JobState']=='CANCELED':
            return True
        else:
            return False
    return True

def is_job_failed(jobid):
    state = get_job_state(str(jobid))
    if state:
        if state['JobState']=='FAILED':
            return True, state['Reason']
        else:
            return False, state['Reason']
    #if we can't get job information there is something wrong
    return True, state['Reason']

############### job related ####################


def forcing_present(cn):
#    if KSA > 0:
    ff = '{}/a{}{}a{}{}.tar'.format(cn['PFADFRC'], cn['BUSER'],\
                                    cn['BEXP'], str(cn['date_present'].year),\
                                    str(cn['date_present'].month).zfill(2))

    ff2= '{}/a{}{}a{}{}.tar'.format(cn['PFADFRC'], cn['BUSER'],\
                                    cn['BEXP'], str(cn['date_next'].year),\
                                    str(cn['date_next'].month).zfill(2))

    logging.debug(ff)
    if os.path.isfile(ff):
        logging.debug('Forcing tar file exist')
    else:
        logging.info('Forcing tar file {} do not exist'.format(ff))
        raise NameError('Forcing tar file {} do not exist'.format(ff))

    logging.debug(ff2)
    if os.path.isfile(ff2):
        logging.debug('Forcing tar file for the next month exist')
    else:
        logging.info('Forcing tar file {} do not exist'.format(ff2))
        raise NameError('Forcing tar file {} do not exist'.format(ff2))




def restart_present(cn):
    if cn['KSA'] > 0:
        ffile = '{}/xf/e{}{}f{}{}0100'.format(cn['DIR'], cn['USER'],\
                                              cn['EXP'], str(cn['date_present'].year),\
                                              str(cn['date_present'].month).zfill(2))

        gfile = '{}/xf/e{}{}g{}{}0100'.format(cn['DIR'], cn['USER'],\
                                              cn['EXP'], str(cn['date_present'].year),\
                                              str(cn['date_present'].month).zfill(2))
        logging.debug(ffile)
        logging.debug(gfile)
        isf = os.path.isfile(ffile)
        iss = os.path.isfile(gfile)
        
        if isf and iss:
            logging.debug('Restart files exist')
        else:
            logging.info('Restart files do not exist')
            raise Exception('Restart files do not exist')

def cphclake(cn):
    mon_minus = cn['date_present'] - datetime.timedelta(cn['tdiff']/24)
    year_prev = str(mon_minus.year)
    mon_prev  = str(mon_minus.month)
    fname     = cn['MYWRKSHR']+'/hclake/hclake_'+year_prev+mon_prev+'.srv8'
    #print(fname)

    if os.path.isfile(fname):
        os.system('cp '+fname+' '+cn['MYWRKHOME']+'/hclake.srv8')
        logging.debug(' copy hclake'+fname)


def preprocessing(cn):
    
    ofile = open('preprocessing.sh', 'w')
    
    cn['year'] = str(cn['date_present'].year)
    cn['mon']  = str(cn['date_present'].month).zfill(2)
    cn['nyear'] = str(cn['date_next'].year)
    cn['nmon']  = str(cn['date_next'].month).zfill(2)
    

    out_init = TEMP_ENV.get_template(cn['preprocessing_template']).render(cn)
    ofile.write(out_init)
    ofile.close()

    os.system('chmod +x ./preprocessing.sh')
    logging.info('Begin with preprocessing')
    process = Popen('./preprocessing.sh', shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    logging.debug(out)
    logging.debug(err)
    logging.info('Preprocessing is over')

def generate_INPUT(cn):
    ofile = open('INPUT', 'w')
    cn['YADAT']=cn['inidate'].strftime('%Y%m%d%H')
    out_init = TEMP_ENV.get_template(cn['INPUT_template']).render(cn)

    ofile.write(out_init)
    ofile.close()
    logging.debug("INPUT file is generated")

def generate_INPUT_press_interp(cn):
    
    cn['KSE_small'] = calendar.monthrange(cn['date_present'].year,cn['date_present'].month)[1]*24
    cn['date']      = cn['date_present'].strftime('%Y%m')+'0106'
    
    ofile = open(cn['MYWRKHOME']+'/post/INPUT', 'w')
    out_init = TEMP_ENV.get_template(cn['INPUT_pressure_iterp']).render(cn)

    ofile.write(out_init)
    ofile.close()
    logging.debug("INPUT file for pressure interpolation is generated")

def generate_batch_moab( MYWRKSHR , PFL, model_exe ):
    ofile = open('moab_remo_sub.sh', 'w')
    out_init = TEMP_ENV.get_template('moab_remo_sub_template').render(MYWRKSHR =  MYWRKSHR,\
                                                               PFL=PFL,\
                                                               model_exe=model_exe)

    ofile.write(out_init)
    ofile.close()
    logging.debug("Batch file is generated")

def generate_batch_slurm(cn):
    ofile = open('slurm_remo_sub.sh', 'w')
    out_init = TEMP_ENV.get_template(cn['slurm_template']).render(cn)

    ofile.write(out_init)
    ofile.close()
    logging.debug("Batch file is generated")

    

def postprocessing(cn, jobid, execute='slurm', packyear=True, rmyear=True, endmon = 12):
    '''
    tfile - template file
    '''    
    cn['year']  = str(cn['date_present'].year)
    cn['mon']   = str(cn['date_present'].month).zfill(2)
    cn['day']   = str(calendar.monthrange(cn['date_present'].year,cn['date_present'].month)[1]).zfill(2)
    cn['nyear'] = str(cn['date_next'].year)
    cn['nmon']  = str(cn['date_next'].month).zfill(2)
    cn['jobid'] = str(jobid)
    cn['packyear'] = packyear # if we pack years after endmon ( usually 12)
    cn['rmyear']   = rmyear   # if we have to clean up after endmon (usually 12)
    cn['endmon']   = str(endmon).zfill(2)   # month of the year after wich we pack everything for a year

    ofile = open('postprocessing.sh', 'w')
    out_init = TEMP_ENV.get_template(cn['postprocessing_template']).render(cn)

    ofile.write(out_init)
    ofile.close()
    
    if execute=='shell':
        os.system('chmod +x ./postprocessing.sh')
        logging.info('postprocessing start')
        process = Popen('./postprocessing.sh', shell=True,
                    stdout=PIPE, stderr=PIPE)
        (out,err) = process.communicate()
        logging.info(out)
        logging.info(err)
        logging.info('postprocessing is over')
    elif execute=='slurm':
      submit_job("./postprocessing.sh")
    else:
      pass

def check_exitcode(fname, sendmail=True):
    f = open(fname)
    
    try:
        a = f.readlines()[2].split()[1]
    except:
        logging.info('Can\'t read exit code (something is wrong with stderr file)')
        raise NameError('Exit code is not 0, simulation failed')

    if a == '0':
        logging.info('Exit code is fine')
        return a
    else:
        logging.info('Exit code is not 0, simulation failed')
        raise NameError('Exit code is not 0, simulation failed')

def generate_rm_last_mon(cn):
    cn['year'] = str(cn['date_present'].year)
    cn['mon']  = str(cn['date_present'].month).zfill(2)

    ofile = open('rm_last_mon.sh', 'w')

    out_init = TEMP_ENV.get_template('rm_last_mon_template').render(cn)

    ofile.write(out_init)
    ofile.close()
    logging.debug("File to remoeve last month created")



def ftime(fname):
    fcontent = os.popen('tail -n 100 {}'.format(fname)).read()
    b = []
    for line in fcontent.splitlines():
        if "FORECASTTIME" in line:
            b.append(int(line.split()[4]))
    if b:
        return b[-1]
    else:
        return None


def progressbar(cn, jobstate):

    timepassed =  ftime(cn['MYWRKHOME']+'/my-out.txt')
    if jobstate != None:

        sys.stdout.write('{}\n'.format('State: '+jobstate['JobState']+\
                                       ', Run Time: '+jobstate['RunTime']+\
                                       ', Submited: '+jobstate['SubmitTime']))
        if timepassed:
            tdif    = cn['KSE']-cn['KSA']
            tpassed = timepassed-cn['KSA']
            ratio   = tpassed/float(tdif)
            filled  = '=' * int( ratio * 50)
            rest    = '-' * ( 50 - int( ratio * 50) )
            sys.stdout.write('|' + filled+'>'+rest+ '| {:.2f}%'.format(ratio*100))
            sys.stdout.write('\r\033[1A')
            sys.stdout.flush()
        else:
            sys.stdout.write('Can\'t get the progress bar :(') 
            #sys.stdout.write('FORECASTTIME: {}'.format(str(timepassed)))
            sys.stdout.write('\r\033[1A')
            sys.stdout.flush()
    else:
        logging.info("The jobstate is None, job information is wrong")

def final_status(cn, jobid):

    jobstate = get_job_state(int(jobid))

    if jobstate:
        logging.info('Job State   : '+jobstate['JobState'])
        logging.info('Run Time    : '+jobstate['RunTime'])
        logging.info('Submit time : '+jobstate['SubmitTime'])
        logging.info('Start time  : '+jobstate['StartTime'])
        logging.info('End time    : '+jobstate['EndTime']) 
    #check_exitcode('my-error.txt')
        fail, reason = is_job_failed(jobid)
        if fail:
            logging.info('Job failed')
            logging.info('Reason: '+reason)
            raise NameError('Simulation failed: '+reason)

def m2netcdf(cn):
    ll = glob.glob('{}/xm/*'.format(cn['DIR']))
    ll.sort()
    for fpath in ll:
        fname = fpath.split('/')[-1]
        if os.path.isfile('{}/{}.nc'.format(cn['MONDIR'], fname)) != True:

            process = Popen('cdo -f nc -r copy {} {}/{}.nc'.format(fpath, cn['MONDIR'], fname), shell=True,
                        stdout=PIPE, stderr=PIPE)
            (out,err) = process.communicate()
            print(out)
            print(err)
    
    process = Popen('cdo -O mergetime {0}/e*m??????.nc {0}/months.nc'.format(cn['MONDIR']), shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)

    process = Popen('cdo -O fldmean {}/months.nc {}months_fm_{}.nc'.format(cn['MONDIR'],\
                     cn['HOME']+'/monitor/', cn['EXP']), shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)

    return '{}/months.nc'.format(cn['MONDIR'])

def at2netcdf(cn):
    lla = glob.glob('{}/2d/a??????a*'.format(cn['MONDIR']))
    llt = glob.glob('{}/2d/e??????t*'.format(cn['MONDIR']))
    lla.sort()
    llt.sort()

    process = Popen('cdo -f nc -r sellevel,27 -selcode,130,131,132,133,134 {} {}_{}.nc'.format(lla[-1],\
                     cn['HOME']+'/monitor/a_2d', cn['EXP']), shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)

    process = Popen('cdo -f nc -r sellevel,27 -selcode,130,131,132,133,134 {} {}_{}.nc'.format(llt[-1],\
                     cn['HOME']+'/monitor/t_2d', cn['EXP']), shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)



def get_log_values(a, model_date=np.nan):

    dd = {'submit_date':np.nan,
          'start_time':np.nan,
          'end_time':np.nan,
          'elapsed_time':np.nan,
          'batch_time':np.nan,
          'remo_time':np.nan,
          'date':model_date,
          'jobid':np.nan}
    for line in a:

        if line.startswith('* Submit date'):
            dd['submit_date'] = line.split()[-1]
            #print line.split()[-1]
        elif line.startswith('* Start time'):        
            dd['start_time'] = line.split()[-1]
        elif line.startswith('* JobID'):
            dd['jobid'] = line.split()[-1]
        elif line.startswith('* End time'):
            dd['end_time'] = line.split()[-1]
        elif line.startswith('* Elapsed time'):
            dd['elapsed_time'] = line.split()[-2]
        elif line.startswith('* batch'):
            dd['batch_time'] = float(line.split()[4])
        elif line.startswith('* 0      | sven_remo'):
            dd['remo_time'] = float(line.split()[4])
        
    return dd

def save_log_values(cn):
    files = glob.glob(cn['MYWRKHOME']+'/log/my-out_*_??????.txt')
    files.sort()
    df = []
    for ff in files:
        model_date =ff.split('.')[-2][-6:]
        fl = open(ff)
        a = fl.readlines()
        dd = get_log_values(a, model_date)
        if type(dd['submit_date']) == str:
            df.append(dd)
    ofile = open(cn['HOME']+'/monitor/parced_logs_{}.json'.format(cn['EXP']), 'w')
    json.dump(df, ofile)
    ofile.close()