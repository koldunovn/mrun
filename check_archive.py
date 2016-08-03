'''
Checks if the
'''

import pexpect
import glob
import os
from rmodel import send_mail
from config import cn
import logging
import sh 
import sys, math

try:
    year   = sys.argv[1]

except:
    print "Usage:",sys.argv[0], "year or year_rm to remove data if the check is succesful"
    sys.exit(1)


logging.basicConfig(filename='log_check_archive.log', filemode="w", level=logging.INFO, \
                    format='%(asctime)s %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler())

def check_size(fpath, tarline):
    '''
    fpath   - path to the tarfile
    tarline - string that we got from the archive with the file size
    '''
    fname = os.path.split(fpath)[-1]
    orig_size = os.path.getsize(fpath)
    tar_size  = tarline.split()[4]
    if orig_size == int(tar_size):
        logging.debug('{}: Size OK'.format(fname))
        return True
    else:
        logging.info('{}: !!!WRONG SIZE!!!'.format(fname))
        send_mail('Wrong size for the file in the archive','''{} '''.format(fname),cn)
        return False

#process input to the script, remove files if year_rm is provided
splitted = year.split('_')

if len(splitted)==2:
    if splitted[1] == 'rm':
        year = splitted[0]
        move = True
        print move
    else:
        raise ValueError('Extention have to be _rm')
else:
    year = year
    move = False
    print(year)


#read information from configuration file
PFADRES   = cn['PFADRES']
EXP       = cn['EXP']
USER      = cn['USER']
dkrz_user = cn['dkrz_user']
DIR       = cn['DIR']
BEXP      = cn['BEXP']
BUSER     = cn['BUSER']

#login to archive and get listing of the directory
if cn['archive'] == 'mistral':
    logstring = 'sftp  -i {} {}@{}:{}'.format(cn['ssh_key_path'],cn['dkrz_user'], cn['dkrz_computer'],cn['folder_on_dkrz'])
    child = pexpect.spawn(logstring)
    child.expect('sftp>')
    child.sendline('ls -l e*{}*.tar'.format(year))
    child.expect('sftp>')
    a = child.before
    print(a)
elif cn['archive'] == 'dkrz_archive':
  
    child = pexpect.spawn('pftp')
    child.expect('ftp>')
    child.sendline('prompt')
    child.expect('ftp>')
    child.sendline('lcd {}'.format(PFADRES))
    child.expect('ftp>')
    child.sendline('cd ch0636/{}/exp{}/year{}/'.format(dkrz_user,EXP,year))
    child.expect('ftp>')
    child.sendline('dir')
    child.expect('ftp>')
    logging.debug(child.before)
    a = child.before

errors = 0
#loop over all file types
for ftype in ['e','t','f','m','p']:

    if ftype in ['e','t']:
        ll = glob.glob(cn['PFADRES']+'/e{}{}{}{}??.tar'.format(cn['USER'],cn['EXP'],ftype,year))
        ll.sort()
    elif ftype in ['f','m','p']:
        ll = glob.glob(cn['PFADRES']+'/e{}{}{}{}.tar'.format(cn['USER'],cn['EXP'],ftype,year))
        ll.sort()
    

		#send_mail('Wrong file size in the archive','''{} '''.format(fname),cn)

    for l in ll:
		## check if the file is in the archive
        fname = l.split('/')[-1]
        if fname in a:

            logging.info('{}:Uploaded'.format(fname))
            
            for tarline in a.split('\n'):
            
                if fname in tarline:
                    size_is_ok = check_size(l,tarline)
            
                    if size_is_ok and move:
                        logging.debug('We remove {}'.format(l))
                        sh.rm(l)
                        if ftype in ['f','p']:
                            sh.rm(sh.glob(l[:-4]+'??.tar'))
                        elif ftype in ['m']:
                            sh.rm(sh.glob(l[:-4]+'??.tar'))
                            # also remove n files
                            sh.rm(sh.glob(l[:-9]+'n'+l[-8:-4]+'??.tar'))

                        
            
                    elif size_is_ok == False:
                        
                        errors = errors+1
        else:
            logging.info('{}: !!! NOT UPLOADED !!!'.format(fname))
            errors = errors+1
		#child.sendline('put {}'.format(fname))
        #child.expect('ftp>')

            send_mail('File is not in the archive','''{} '''.format(fname),cn)




# rm {{ DIR }}/xa/a{{ USER }}{{ BEXP }}a{{ year }}??????
# rm {{ DIR }}/xt/e{{ USER }}{{ EXP }}t{{ year }}??????
# rm {{ DIR }}/xe/e{{ USER }}{{ EXP }}e_c???_{{ year }}??
# rm {{ DIR }}/xn/e{{ USER }}{{ EXP }}n_c???_{{ year }}??
# rm {{ DIR }}/xpt/e{{ USER }}{{ EXP }}p_c???_????_{{ year }}??

def rm_run_files(wildcard):
    logging.info("rm {}".format(wildcard))
    try:
        sh.rm(sh.glob(wildcard))
    except:
        logging.info("Files do not exist or can't remove")
    
if (errors == 0) and move:
    rm_run_files("{}/xa/a{}{}a{}??????".format(DIR,BUSER,BEXP,year))
    rm_run_files("{}/xt/e{}{}t{}??????".format(DIR,USER,EXP,year))
    rm_run_files("{}/xe/e{}{}e_c???_{}??".format(DIR,USER,EXP,year))
    rm_run_files("{}/xn/e{}{}n_c???_{}??".format(DIR,USER,EXP,year))
    rm_run_files("{}/xpt/e{}{}p_c???_????_{}??".format(DIR,USER,EXP,year))

    
child.close()
os.system('mv log_check_archive.log ./log/log_check_archive{}.log'.format(year))

# for l in a.split('\n'):
#     if "e200701" in l:
#         print('efile is in place')
#         print(l.split()[4])

#     elif "t200701" in l:
#     	print('tfile is in place')
#         print(l.split()[4])
