from jinja2 import Environment, FileSystemLoader
import os
import sys
import time
import datetime
import calendar
from subprocess import Popen, PIPE
import logging
from rmodel import * 
from config import cn


PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

logging.basicConfig(filename='log.log', filemode="w", level=logging.DEBUG, \
                    format='%(asctime)s %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler())

logging.info('Start script')

logging.info('First KSA = '+str(cn['KSA']))
logging.info('First KSE = '+str(cn['KSE']))

cn['firstrun'] = True

for i in range(cn['nmonths']):

    logging.info("\nMonth of the simulation: "+cn['date_present'].strftime('%Y-%m')+'\n')
    mon_plus  = cn['date_present'] + datetime.timedelta(cn['tdiff']/24)
    
    cn['date_next']    = mon_plus

#    forcing_present(cn) # checks if 'a' files are in place
#    restart_present(cn) # checks if 'f' and 'g' files are in place
#    preprocessing(cn)   # create directories and untar 'a' files
    cphclake(cn)        # GLACINDIA specific
#    generate_INPUT(cn)  # generate REMO INPUT file
    
    time.sleep(1)

    generate_batch_slurm(cn) # generate batch script
    
    time.sleep(1)

 #   jobid = '12345' # only if we testing

 ############### job submission and monitoring #################   
    jobid, stout, sterr = submit_job('slurm_remo_sub.sh')
    
    logging.info('Job ID:'+jobid)

    complete = False

    failedjob = 0

    while complete==False:
        time.sleep(5)
        #print(complete)
        try:
            jobstate = get_job_state(int(jobid))
            failedjob = 0 #reset counter of failed attempts to get the job info              
        except:
            if failedjob <= 3:
                logging.info("Can\'t get information about the job, retrying")
                failedjob = failedjob + 1
            else:
                logging.info("No information about the job, give up")
                raise NameError('No information about the job, give up')
        
        progressbar(cn, jobstate)
        
        complete = is_job_done(int(jobid))
    
    print('\n')    
 ################################################################


#    generate_rm_last_mon(cn) #script to remove latest results
    final_status(cn, jobid)  #check final status of the job

 #   generate_INPUT_press_interp(cn) # generate INPUT file for pressure interpolation
    
    #Postprocessing call
    postprocessing(cn, jobid, execute='shell', rmyear=True, endmon = cn['endmon'])

    #Prepare for the next month, update configuration
    #os.system('mkdir {}'.format(cn['MONDIR']))
#    m2netcdf(cn)
    save_log_values(cn)
#    os.system('cp config.py {}/monitor/config_{}.py'.format(cn['HOME'],cn['EXP']))
#    at2netcdf(cn)

    logging.debug("Next month will be: "+mon_plus.strftime('%Y-%m'))
    cn['tdiff'] = calendar.monthrange(mon_plus.year,mon_plus.month)[1]*24
    logging.debug('Number of days in the next month: '+str(cn['tdiff']))
    cn['KSA']=cn['KSE']
    logging.debug('New KSA: '+str(cn['KSA']))
    cn['KSE']=cn['KSA']+cn['tdiff']
    logging.debug('New KSE: '+str(cn['KSE']))

    cn['date_present'] = cn['date_next']
    firstrun=False

os.system('cp log.log ./log/log_{}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')))



