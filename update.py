#!/usr/bin/env python

# '''
# Any time a folder is added to the monitored parent directory, that folder needs
# to be monitored as well [recursive monitoring is not fully supported]. This
# script will add to incrontab when a new folder is added.
# Be sure to chmod +x this script!
# '''

import os,sys,pwd,subprocess, time
from datetime import datetime

# CFG Variables
scriptPath = '/path/to/this/update.py' # the path to THIS script.
changedDir = sys.argv[1]
workingDir = sys.argv[2]
event = sys.argv[3]
incrontemp = workingDir + '/temp'

curUser = 'thang' # ensure this runs under the correct user, for incrontab
os.setuid(pwd.getpwnam(curUser)[2])

# Log to a timestamped log file
def log(out, err):
    curTime = datetime.time(datetime.now()).isoformat()
    f = open(workingDir + '/error.log' + curTime, 'w')
    f.write('Could not update incrontab for %s' % changedDir + '\n')
    f.write('Failed output: \n')
    f.write(out + '\n')
    f.write(err + '\n')
    f.close()

def processCmd(cmdList):

    # Copy the current incrontab, & modify the copy accordingly.
    cmdList = ['/usr/bin/incrontab -l > %s' % incrontemp] + cmdList
    # Replace with the changed incrontemp.
    cmdList += ['/usr/bin/incrontab %s' % incrontemp]

    for cmd in cmdList:
        o = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = o.communicate()
        if o.returncode != 0:
            log(out,err)
            sys.exit('Process failed..' )
    os.remove(incrontemp)

# Process an uploaded file.
def processFile():
    pass

def main():

    # A Sub-Directory is added.
    if 'IN_CREATE,IN_ISDIR' in event:
        cmds = ["echo '%s IN_CREATE,IN_DELETE,IN_MODIFY %s $# $@ $%%' >> %s" % (workingDir+'/'+changedDir, scriptPath, incrontemp)]
        processCmd(cmds)

    # A Sub-Directory is deleted.
    elif 'IN_DELETE,IN_ISDIR' in event:
        cmds = ["sed -i '/%s/d' %s" % (changedDir.strip('/'), incrontemp)]
        processCmd(cmds)
    
    # A File is added... 
    # We may need to watch when files are moved to the watched directory as well.
    elif 'IN_CREATE' in event or 'IN_MODIFY' in event:
        processFile()
        sys.exit()


if __name__ == "__main__":
    main()
