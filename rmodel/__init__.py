from jinja2 import Environment, FileSystemLoader
import os
from subprocess import Popen, PIPE

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../templates')),
    trim_blocks=False)

def diff_month(d1, d2):
    return (d1.year - d2.year)*12 + d1.month - d2.month

def forcing_present(path, BUSER, BEXP, date, ndate):
#    if KSA > 0:
    ff = '{}/a{}{}a{}{}.tar'.format(path, BUSER, BEXP, str(date.year), str(date.month).zfill(2))
    ff2= '{}/a{}{}a{}{}.tar'.format(path, BUSER, BEXP, str(ndate.year), str(ndate.month).zfill(2))

    print ff
    if os.path.isfile(ff):
        print('Forcing tar file exist')
    else:
        raise NameError('Forcing tar file {} do not exist'.format(ff))

    print ff2
    if os.path.isfile(ff2):
        print('Forcing tar file exist')
    else:
        raise NameError('Forcing tar file {} do not exist'.format(ff2))




def restart_present(path, USER, EXP, date, KSA):
    if KSA > 0:
        ffile = '{}/xf/e{}{}f{}{}0100'.format(path, USER, EXP, str(date.year), str(date.month).zfill(2))
        gfile = '{}/xf/e{}{}g{}{}0100'.format(path, USER, EXP, str(date.year), str(date.month).zfill(2))
        print(ffile)
        print(gfile)
        isf = os.path.isfile(ffile)
        iss = os.path.isfile(gfile)
        
        if isf and iss:
            print('Restart files exist')
        else:
            raise NameError('Restart files do not exist')
def preprocessing(PFADFRC, DIR, PFADRES, BUSER, BEXP, date, ndate, firstrun, xfolders):
    
    ofile = open('preprocessing.sh', 'w')
    out_init = TEMPLATE_ENVIRONMENT.get_template('preprocessing_template').render( year=str(date.year),\
                                                                                   mon=str(date.month).zfill(2),\
                                                                                   nyear=str(ndate.year),\
                                                                                   nmon =str(ndate.month).zfill(2),\
                                                                                   PFADFRC=PFADFRC,\
                                                                                   PFADRES=PFADRES,\
                                                                                   DIR=DIR,\
                                                                                   BUSER=BUSER,\
                                                                                   BEXP=BEXP,\
                                                                                   firstrun=firstrun,\
                                                                                   xfolders=xfolders )
    ofile.write(out_init)
    ofile.close()

    os.system('chmod +x ./preprocessing.sh')
    print('Begin with preprocessing')
    process = Popen('./preprocessing.sh', shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)
    print('Preprocessing is over')


def generate_INPUT(fname, KSA, KSE, DT, DIR, MYWRKSHR, USER, EXP, BUSER, BEXP ):
    ofile = open('INPUT', 'w')
    out_init = TEMPLATE_ENVIRONMENT.get_template(fname).render(KSA=KSA,\
                                                               KSE=KSE,\
                                                               DIR=DIR,\
                                                               MYWRKSHR=MYWRKSHR,
                                                               DT=DT,\
                                                               USER=USER,\
                                                               EXP=EXP,\
                                                               BUSER=BUSER,\
                                                               BEXP=BEXP)

    ofile.write(out_init)
    ofile.close()
    print("INPUT file is generated")

def postprocessing(MYWRKSHR, PFADFRC, PFADRES, DIR, USER, EXP, date, jobid):
    ofile = open('postprocessing.sh', 'w')
    out_init = TEMPLATE_ENVIRONMENT.get_template('postprocessing_template').render( year=str(date.year),\
                                                                                   mon=str(date.month).zfill(2),\
                                                                                   PFADFRC=PFADFRC,\
                                                                                   DIR=DIR,\
                                                                                   USER=USER,\
                                                                                   EXP=EXP,\
                                                                                   MYWRKSHR=MYWRKSHR,\
                                                                                   PFADRES=PFADRES,\
                                                                                   jobid=jobid )
    ofile.write(out_init)

    ofile.close()
    os.system('chmod +x ./postprocessing.sh')
    print('postprocessing start')
    process = Popen('./postprocessing.sh', shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)
    print('postprocessing over')

def check_exitcode(fname, sendmail=True):
    f = open(fname)
    a = f.readlines()[2].split()[1]
    if a == '0':
        print('Exit code is fine')
        return a
    else: 
        raise NameError('Exit code is not 0, simulation failed')


def postprocessing_pure(MYWRKSHR, PFADFRC, PFADRES, DIR, USER, EXP, date, jobid):
    ofile = open('postprocessing_pure.sh', 'w')
    out_init = TEMPLATE_ENVIRONMENT.get_template('postprocessing_pure_template').render( year=str(date.year),\
                                                                                   mon=str(date.month).zfill(2),\
                                                                                   PFADFRC=PFADFRC,\
                                                                                   DIR=DIR,\
                                                                                   USER=USER,\
                                                                                   EXP=EXP,\
                                                                                   MYWRKSHR=MYWRKSHR,\
                                                                                   PFADRES=PFADRES,\
                                                                                   jobid=jobid )
    ofile.write(out_init)

    ofile.close()
    os.system('chmod +x ./postprocessing_pure.sh')
    print('postprocessing start')
    process = Popen('./postprocessing_pure.sh', shell=True,
                    stdout=PIPE, stderr=PIPE)
    (out,err) = process.communicate()
    print(out)
    print(err)
    print('postprocessing over')


