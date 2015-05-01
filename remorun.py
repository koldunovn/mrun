from jinja2 import Environment, FileSystemLoader
import os
import nsub
import time
import datetime
import calendar
from subprocess import Popen, PIPE
from rmodel import diff_month, forcing_present, restart_present, preprocessing, generate_INPUT, postprocessing, check_exitcode, generate_batch_moab



PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

#initial date for the whole simmulation
inidate = datetime.datetime(1960,1,1,0)

#start date for this concrete simulation
sdate = datetime.datetime(1960,1,1,0)

#end date for this concrete simulation (not including this date)
edate = datetime.datetime(1960,2,1,0)

DT='120'

USER  = '055'
EXP   = '006'
BUSER = '055'
BEXP  = '005' 
#local place for tar forcing files (will be untared during preprocessing)

MYWRKSHR  = '/lustre/jhome15/hhh24/hhh242/TEST/mrun/'
DIR       = MYWRKSHR+'/'+'tmp_'+USER+EXP
PFADFRC   = MYWRKSHR+'/FORCING/'
PFADRES   = MYWRKSHR+'/results/'
PFL       = '/lustre/jhome15/hhh24/hhh242/sven_remo2008_gletscher_Lake_nk/libs/'

model_exe = 'sven_remo2008'  
INPUT_file = 'INPUT_'+USER+EXP

xfolders = ['xa', 'xe', 'xf', 'xm', 'xn', 'xt']
firstrun = True


#difference in hours
KSA_ini = (sdate-inidate).total_seconds()/3600
#print(str(KSA_ini))
KSE_ini =  calendar.monthrange(sdate.year,sdate.month)[1]*24

#def diff_month(d1, d2):
#    return (d1.year - d2.year)*12 + d1.month - d2.month

#number of months
nmonths = diff_month(edate, sdate)  

#timedelta

#KSA = KSA_ini
#KSE = KSA_ini + KSE_ini
KSA = 0
KSE = 10

date_centered = sdate+datetime.timedelta(14)
tdiff = KSE_ini

print('First KSA = '+str(KSA))
print('First KSE = '+str(KSE))

for i in range(nmonths):

    print("\nDate centered:"+str(date_centered)+'\n')
    mon_plus = date_centered + datetime.timedelta(tdiff/24)
    
    forcing_present(PFADFRC ,BUSER, BEXP, date_centered, mon_plus)
    
    restart_present(DIR, USER, EXP, date_centered, KSA)
    
    preprocessing(MYWRKSHR, PFADFRC, DIR, PFADRES, BUSER, BEXP, date_centered, mon_plus, firstrun, xfolders )
    
    generate_INPUT(INPUT_file, KSA, KSE, DT, DIR, MYWRKSHR, USER, EXP, BUSER, BEXP )

    generate_batch_moab(MYWRKSHR , PFL, model_exe)
    
    jobid, stout, sterr = nsub.submit_job('moab_remo_sub.sh')
    
    print('Job ID:'+jobid)

    complete = False
    #print(complete)
    while complete==False:
        #print(complete)
        a = nsub.get_job_state(int(jobid))
        print("Job state:"+a['EState'])
        complete = nsub.is_job_done(int(jobid))
        time.sleep(100)
    #jobid=11  

    check_exitcode('my-error.txt')
    postprocessing(MYWRKSHR, PFADFRC, PFADRES, DIR, USER, EXP,  date_centered, jobid) 
    
    
    print("Next centered date will be: "+str(mon_plus))
    tdiff = calendar.monthrange(mon_plus.year,mon_plus.month)[1]*24
    print('Number of days in the next month: '+str(tdiff))
    KSA=KSE
    print('New KSA: '+str(KSA))
    KSE=KSA+tdiff
    print('New KSE: '+str(KSE))

    date_centered = mon_plus




