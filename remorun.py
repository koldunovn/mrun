# Example of the REMO run script, that use rmodel module
#
# Now the assumption is that REMO is calculated for one month on every batch job submission.
#
# Nikolay Koldunov, 2016
#

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

# Setupt junja 2 templates
PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment( 
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

# Setup logging. Change "level" to "logging.DEBUG" if you need more detailed information.
logging.basicConfig(filename='log.log', filemode="w", level=logging.INFO, \
                    format='%(asctime)s %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler())

# Print out initial information
logging.info('Start script')
logging.info('First KSA = '+str(cn['KSA']))
logging.info('First KSE = '+str(cn['KSE']))

# Set this flag to True for the first iteration of the model
cn['firstrun'] = True

# Enter the main loop. Number of iterations is equal to number of months between sdate and edate
for i in range(cn['nmonths']):

    logging.info("\nMonth of the simulation: "+cn['date_present'].strftime('%Y-%m')+'\n')

    # Calculate the next starting date (needed for forcing files untaring and so on...)
    cn['date_next']  = cn['date_present'] + datetime.timedelta(cn['tdiff']/24)

    forcing_present(cn) # checks if 'a' files are in place
    restart_present(cn) # checks if 'f' and 'g' files are in place

    # Generate and execute shell script that create 'xfolders' is nessesary,
    # remove model results from previous run if needed and unpack forcing files (a-files)
    # in to 'xa' directory.
    preprocessing(cn)   

    # Dynamical glacier model specific (copy lake file)
    cphclake(cn)

    # Generates REMO INPUT file for current month
    generate_INPUT(cn) 
    
    # Pause in case the IO is slow
    time.sleep(1)

    # Generates slurm batch script (e.g. slurm_remo_sub.sh)
    generate_batch_slurm(cn) # generate batch script
    
    # Pause in case the IO is slow
    time.sleep(1)

 #   jobid = '12345' # only if we testing

 ############### job submission and monitoring #################   
    jobid, stout, sterr = submit_job('slurm_remo_sub.sh')
    
    logging.info('Job ID:'+jobid)

    complete = False
    # counter of failed attempts to get the job info
    failedjob = 0
    # monitoring loop, has to run while the job is running
    while complete==False:
        # request information about the job status every ?? seconds
        time.sleep(10)
        try:
            jobstate = get_job_state(int(jobid))
            failedjob = 0 #reset counter of failed attempts to get the job info              
        except:
            if failedjob <= 7:
                logging.info("Can\'t get information about the job, retrying")
                failedjob = failedjob + 1
            else:
                logging.info("No information about the job, give up")
                raise NameError('No information about the job, give up')
        # draw progress bar
        progressbar(cn, jobstate)
        
        complete = is_job_done(int(jobid))
    
    print('\n')    
 ################################################################


    final_status(cn, jobid)  #check final status of the job

    generate_INPUT_press_interp(cn) # generate INPUT file for pressure interpolation
    
    #Postprocessing call
    # Generate and run postrpocessing shell script. 
    # This script usually will:
    # - copy STDOUT and STDERR output files to log directory
    # - run pressure interpolation (druintzr)
    # - run monthly averaging for pressure interpolated fields (mitzrpe)
    # - pack results for one month to tarballs
    # - upload tarballs to archive
    # - remove tarballs from srcatch
    postprocessing(cn, jobid, execute=cn['post_execution'], rmyear=True, endmon = cn['endmon'])

    
    #os.system('mkdir {}'.format(cn['MONDIR']))

    # convert monthly file to net cdf
    m2netcdf(cn)

    # Parce STDOUT file and save it to .json format for monitoring
    save_log_values(cn)

    # Copy configuration file with experiment number to monitoring folder
    os.system('cp config.py {}/monitor/config_{}.py'.format(cn['HOME'],cn['EXP']))
    
    # convert to netCDF last a and t file for the month
    at2netcdf(cn)

    #Prepare for the next month, update configuration
    logging.debug("Next month will be: "+mon_plus.strftime('%Y-%m'))
    cn['tdiff'] = calendar.monthrange(mon_plus.year,mon_plus.month)[1]*24
    logging.debug('Number of days in the next month: '+str(cn['tdiff']))
    cn['KSA']=cn['KSE']
    logging.debug('New KSA: '+str(cn['KSA']))
    cn['KSE']=cn['KSA']+cn['tdiff']
    logging.debug('New KSE: '+str(cn['KSE']))

    cn['date_present'] = cn['date_next']

    firstrun=False

# after the end of the run copy log files to log directory
os.system('cp log.log ./log/log_{}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')))

# If the postprocessing script will be executed in the background, whait for 10 minutes so the script can end.
if cn['post_execution'] == 'back':
    logging.info('wait for 10 minutes while background processing is over')
    time.sleep(600)



