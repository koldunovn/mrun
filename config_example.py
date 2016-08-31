# Example configuration file for rmodel module
#
# Nikolay Koldunov, 2016
#
# The basic idea here is that one have to fill in a python
# dictionary, that is later user to configure model run.
#
import datetime
import calendar
from rmodel import diff_month


cn={}

cn['inidate'] = datetime.datetime(2000,1,1,0) # initial date of the experiment
cn['sdate']   = datetime.datetime(2000,1,1,0) # #start date for this concrete simulation
cn['edate']   = datetime.datetime(2041,1,1,0) #end date for this concrete simulation (not including this date)

cn['USER']  = '055' # user number of the user who run the experiment
cn['EXP']   = '026' # experiment number
cn['BUSER'] = '055' # user number of the user who have created REMO forcing files (a-files)
cn['BEXP']  = '021' # number of the experiment for REMO forcing files (a-files) 

### Here we define values for variables in the REMO INPUT namelist ###

cn['MOIE']   ='181' # number of points in x direction 
cn['MOJE']   ='161' # number of points in y direction
cn['DT']     ='120' # time step

cn['PHILU']=-5.0       # Latitude of the lower left corner
cn['RLALU']=2.9        # Longitude of the lower left corner
cn['POLPHI']=79.95     # Latitude of the rotated North Pole
cn['POLLAM']=-123.34   # Longitude of the rotated North Pole
cn['DLAM']=0.22        # resolution in x-direction
cn['DPHI']=0.22        # resolution in y-direction
cn['LQWR']='.TRUE.'    # switch for liquid water in driving fields
# List of three files describing the yearly vegetation cycle
cn['YBDNAM']=''''vgryear_HN_GLC_022R.srv','vltyear_HN_GLC_022R.srv','albyear_HN_GLC_022R.srv' '''
# Green House Gase filename
cn['YGDNAM']='GHG_rcp85_1850-2101.txt'

cn['druintzr'] = 'druintzr_181x161_M' # name of the program for interpolation on pressure levels
cn['mitzrpe']  = 'mitzrpe_GLAC.exe'   # name of the program for creation of the monthly means for pressure 
                                      # interpolated variables

# Batch job related variables

cn['PROCX']  = 9                               #  Number of processors in x-direction	
cn['PROCY']  = 8                               #  Number of processors in y-direction
cn['slurm_time']     = '00:40:00'              #  max wallclock time
cn['slurm_nodes']    = 3                       #  number of nodes 
cn['slurm_account']  = 'ch00000'               #  valid account/project 
cn['slurm_job_name'] = cn['USER']+cn['EXP']    #  slurm job name
cn['email']          = 'user@mail.de'          #  user email
cn['dkrz_user']      = 'u000000'               #  dkrz user number


#local place for tar forcing files (will be untared during preprocessing)
# Paths to different directories

# Home directory of the user 
cn['HOME']           ='/mnt/lustre01/pf/zmaw/'+cn['dkrz_user']
# Where the the run script is executed, logs are stored and so on (usually in your HOME)
cn['MYWRKHOME'] = cn['HOME']+'/mrun'+cn['EXP']
# Where the model is actually runing (forcing and results stored here), should have a lot of space.
cn['MYWRKSHR']  = '/mnt/lustre01/scratch/u/'+cn['dkrz_user']+'/exp'+cn['EXP']
# Subfolder with xa, xe, xt and so on folders, where forcing data are unpacked and results are stored.
cn['DIR']       = cn['MYWRKSHR']+'/'+'tmp_'+cn['USER']+cn['EXP']
# In this folder tar balls with Forcing files are stored
cn['PFADFRC']   = cn['MYWRKSHR']+'/FORCING/'
# The tarballs with results will be stored in this folder
cn['PFADRES']   = cn['MYWRKSHR']+'/results/'
# Path to the folder with model executable
cn['PFL']       = cn['HOME']+'/model_versions/sven_remo2008_gletscher_Lake_nk_mod5/libs/'
# Path to the folder where netCDF files with monthly means will be stored 
cn['MONDIR']    = cn['MYWRKSHR']+'/monitor/'

# name of the REMO model executable
cn['model_exe']      = 'sven_remo2008_bl'
# Name of the template for REMO model INPUT file (TODO: make universal template)   
cn['INPUT_template'] = 'INPUT_'+cn['USER']+cn['EXP']

# names of the folders where different model and postprocessing output will be writen
# this folders are created at the preprocessing step and will be located in cn['DIR'] 
cn['xfolders']       = ['xa', 'xe', 'xf', 'xm', 'xn', 'xt', 'xpt', 'xm_tmp']


# Names of the templates

# This template is used to generate the shell script that creates 'xfolders' is nessesary,
# removes model results from previous run if needed and unpacks forcing files (a-files)
# in to 'xa' directory.
cn['preprocessing_template']  = 'preprocessing_template'

# Template that will be used to generate slurm batch script
cn['slurm_template']          = 'slurm_remo_sub_template'

# Template that will be used to generate INPUT namelist for pressure interpolation
# programm (druintzr)
cn['INPUT_pressure_iterp']    = 'INPUT_pressure_interp_template'

# Template that will be used to generate postrpocessing shell script. 
# This script usually will:
# - copy STDOUT and STDERR output files to log directory
# - run pressure interpolation (druintzr)
# - run monthly averaging for pressure interpolated fields (mitzrpe)
# - pack results for one month to tarballs
# - upload tarballs to archive
# - remove tarballs from srcatch
cn['postprocessing_template'] = 'postprocessing_template'

#difference in hours between start date and initial date
KSA_ini = (cn['sdate']-cn['inidate']).total_seconds()/3600
KSE_ini =  calendar.monthrange(cn['sdate'].year,cn['sdate'].month)[1]*24


#number of months to calculate
cn['nmonths'] = diff_month(cn['edate'], cn['sdate'])  

cn['KSA'] = int(KSA_ini)
cn['KSE'] = int(KSA_ini + KSE_ini)
# cn['KSA'] = 0
# cn['KSE'] = 10

cn['date_present'] = cn['sdate']+datetime.timedelta(14)
cn['tdiff'] = KSE_ini

cn['endmon'] = 12 # month after wich we make a yearly tar. Usually it's 12

## Glacier model related settings ###

# Switch on dynamical glacier scheme
cn['LDYNGLA'] = '.TRUE.'
# Way of glacier calculation ( ususally 1 )
cn['IGLAAM']  = 1

# Name of the file with initial properties of the glaciers 
cn['YINGNAM'] = 'dyngla_ini_southasia_2000_HM_GLACINDIA_Mask.srv'

# Folder where shading file is located 
cn['YSRFCAT'] = cn['MYWRKHOME']+'/libs/'

# Name of the shading file
cn['YSRFNAM'] = 'SRFAC_HN_New.srv'



