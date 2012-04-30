#!/usr/bin/env python

# '''
# Any time a folder is added to the monitored parent directory, that folder needs
# to be monitored as well [recursive monitoring is not fully supported]. This
# script will add to incrontab when a new folder is added.
# This script will also convert any files uploaded to a monitored folder
# to a VP8 [webm] and mobile version to be put into an .alternates folder.
# This script will also handle arbitrary file/folder renaming, at any depth.
# '''

import os,sys,pwd,subprocess, time
from datetime import datetime

# CFG Variables
scriptPath = '/var/www/soundtrack/update.py' # the path to THIS script.
changed = sys.argv[1].strip().replace(' ','\\ ') # spaces.
if len(sys.argv) > 4:
    workingDir = '\\ '.join(sys.argv[2:-1]) # spaces
else:
    workingDir = sys.argv[2] # no spaces
event = sys.argv[-1]
incrontemp = workingDir + '/temp'
curUser = 'thang' # ensure this runs under the correct user, for incrontab
os.setuid(pwd.getpwnam(curUser)[2])

# Log to a timestamped log file
def log(out, err, cmd):
    curTime = datetime.time(datetime.now()).isoformat()
    f = open(workingDir + '/error.%s.log' % curTime , 'w')
    f.write('Could not update incrontab for %s' % changed + '\n')
    f.write('Failed output: \n')
    f.write('Attempted: %s \n' % cmd)
    f.write(out + '\n')
    f.write(err + '\n')
    f.write('Parameters: %s, %s, %s' % (changed,workingDir,event) + '\n')
    f.close()

# Execute a list of shell commands, return the output as a list.
def runCmd(cmdList):
    outList = []
    for cmd in cmdList:
        o = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = o.communicate()
        outList += [out]
        if o.returncode != 0:
            log(out,err,cmd)
            sys.exit('Process failed..' )

    return outList

# Update Incrontab after modifying the current incrontab.
def updateIncron(cmdList):
    # Copy the current incrontab, & modify the copy accordingly.
    cmdList = ['/usr/bin/incrontab -l > %s' % incrontemp] + cmdList
    # Replace with the changed incrontemp.
    cmdList += ['/usr/bin/incrontab %s' % incrontemp]
    runCmd(cmdList)
    os.remove(incrontemp)

# Process an uploaded file.
def processFile():
    # full path to the file..
    in_file = workingDir + '/' + changed
    # Pop off the extension.
    out_file = '.'.join(changed.split('.')[:-1])
    # Put the file in the .alternates folder in the watched directory
    out_file = workingDir+'/.alternates/' + out_file

    # Make an iOS & Firefox playable version.
    cmds = ["HandBrakeCLI -i %s -o %s --preset=\"iPad\"" % ( in_file, out_file + '_ipad.mov' )]
    cmds += ["ffmpeg -y -i %s -threads 4 -f webm -vcodec libvpx  -deinterlace -g 120 -level 216 -profile 0 -qmax 42 -qmin 10 -rc_buf_aggressivity 0.95 -vb 2M -acodec libvorbis -aq 70 -ac 2 %s" % (in_file, out_file + '_ffox.webm' )]
    runCmd(cmds)

def main():
    # A Sub-Directory is added.
    if 'IN_CREATE,IN_ISDIR' in event:
        cmds = ["echo '%s IN_CREATE,IN_DELETE,IN_CLOSE_WRITE,IN_MOVED_TO %s $# $@ $%%' >> %s" % (workingDir+'/'+changed, scriptPath, incrontemp)]
        # Add the .alternates folder, but don't monitor it.
        cmds += ["mkdir %s" % (workingDir+'/'+changed+'/.alternates/')]
        # update incrontab to add/remove watches on the changed Directory
        updateIncron(cmds)

    # A Sub-Directory is deleted.
    elif 'IN_DELETE,IN_ISDIR' in event:
        deletions = (workingDir+'/'+changed).replace('\\','\\\\').replace('/','\\/')
        # First we remove the exact entry, so something like foo/testx doesn't
        # get removed when foo/test is deleted.
        # Then, we remove instances of foo/test/ to take care of subdirs.

        cmds = ["sed -i '/%s\\ /d' %s" % (deletions,incrontemp)]
        cmds += ["sed -i '/%s\//d' %s" % (deletions, incrontemp)]
        updateIncron(cmds)

    # A File is added.
    elif 'IN_CLOSE_WRITE' in event:
        ext = changed.split('.')[-1]
        # Only process valid movie files.
        if 'mov' in ext:
            processFile()

    # A directory was renamed.
    elif 'IN_MOVED_TO,IN_ISDIR' in event:

        # Find the original name of the directory.
        # Compare with the directories in incrontab
        cmds = ['/usr/bin/incrontab -l']
        cmdOut = runCmd(cmds)[0]
        oldName = ''

        for x in cmdOut.split('\n')[:-1]:
            tempDir = x.split(' IN_CREATE,')[0]
            # Ensure the basepath matches, and then check if it exists.
            # If it doesn't, we can assume that it was the renamed directory.
            # This does introduce a race condition, if a folder is deleted
            # while this script is running for a MOVED_TO event.
            # This race condition should be very rare.
            # I am not a doctor. Use at your own risk.

            if workingDir in tempDir and not os.path.exists(tempDir.replace('\\ ', ' ')):
                oldName = tempDir
                break

        # Now we need to pass this to sed, and {forward|back}slashes need to be
        # escaped.
        # Python needs backslashes escaped, and sed is weird about backslashes.
        # So I'm pretty sure this is the right amount of backslashes.

        oldName = oldName.replace('\\','\\\\').replace('/','\\/')
        newName = (workingDir+'/'+changed).replace('\\','\\\\').replace('/','\\/')
        cmds = ["sed -i 's/%s /%s /g' %s" % (oldName,newName,incrontemp)]
        updateIncron(cmds)

    # A file was renamed.
    elif 'IN_MOVED_TO' in event:
        changed = ''.join(sys.argv[1].split('.')[:-1]) # remove the extension
        wd = workingDir.replace('\\ ', ' ')
        altFolder = wd + '/.alternates/'
        files = os.walk(altFolder).next()[2]
        # Pop off extensions & remove dupes.
        files = list(set(map(lambda x: '_'.join(x.split('_')[:-1]),files)))
        moved = ''
        for f in files:
            if not os.path.exists(wd+'/'+f+'.*'):
                moved = f
                break

        try:
            os.rename(altFolder + moved + '_ffox.webm',altFolder + changed + '_ffox.webm')
            os.rename(altFolder + moved + '_ipad.mov',altFolder + changed + '_ipad.mov')

        # If we can't rename the files, so either one of these happened:
        # 1 - Only one of the alternates was created, in which case we still
        # need to make the alternates again
        # 2 - The file was deleted while this script was running, and we still
        # need to make the alternates again.
        except:
            processFile()


    # A file was removed.
    elif 'IN_DELETE' in event:
        altFolder = workingDir + '/.alternates/'

        # Delete the alternates
        try:
            os.remove(altFolder + changed + '_ffox.webm')
            os.remove(altFolder + changed + '_ipad.webm')
        # Don't sweat if they don't exist.
        except:
            pass

if __name__ == "__main__":
    main()
