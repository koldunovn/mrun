from jinja2 import Environment, FileSystemLoader
import os
import nsub
import time
import datetime
import calendar
from subprocess import Popen, PIPE
from rmodel import diff_month, forcing_present, restart_present, preprocessing, generate_INPUT, postprocessing



PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

#initial date for the whole simmulation
inidate = datetime.datetime(1960,1,1,0)

#start date for this concrete simulation
sdate = datetime.datetime(1960,10,1,0)

#end date for this concrete simulation (not including this date)
edate = datetime.datetime(1960,12,1,0)

USER  = '055'
EXP   = '004'
BUSER = '055'
BEXP  = '003' 
#local place for tar forcing files (will be untared during preprocessing)

DIR = '/lustre/jwork/hhh24/hhh242/model_run/'
PFADFRC = '/lustre/jwork/hhh24/hhh242/FORCING/'
PFADRES = '/lustre/jwork/hhh24/hhh242/results/'
MYWRKSHR = '/lustre/jwork/hhh24/hhh242/'

#difference in hours
KSA_ini = (sdate-inidate).total_seconds()/3600
#print(str(KSA_ini))
KSE_ini =  calendar.monthrange(sdate.year,sdate.month)[1]*24

#def diff_month(d1, d2):
#    return (d1.year - d2.year)*12 + d1.month - d2.month

#number of months
nmonths = diff_month(edate, sdate)  

#timedelta
#tdiff = 12
KSA = KSA_ini
KSE = KSA_ini + KSE_ini

date_centered = sdate+datetime.timedelta(14)
tdiff = KSE_ini

print('First KSA = '+str(KSA))
print('First KSE = '+str(KSE))

for i in range(nmonths):

    print("Date centered:"+str(date_centered))
    mon_plus = date_centered + datetime.timedelta(tdiff/24)
    
    forcing_present(PFADFRC ,BUSER, BEXP, date_centered, KSA)
    
    restart_present(DIR, USER, EXP, date_centered, KSA)
    
    preprocessing(PFADFRC, DIR, BUSER, BEXP, date_centered, mon_plus)
    
    generate_INPUT(KSA, KSE)
    
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
    
    postprocessing(MYWRKSHR, PFADFRC, PFADRES, DIR, USER, EXP,  date_centered, jobid) 
    
    
    print("Next centered date will be: "+str(mon_plus))
    tdiff = calendar.monthrange(mon_plus.year,mon_plus.month)[1]*24
    print('Number of days in the next month: '+str(tdiff))
    KSA=KSE
    print('New KSA: '+str(KSA))
    KSE=KSA+tdiff
    print('New KSE: '+str(KSE))

    date_centered = mon_plus




