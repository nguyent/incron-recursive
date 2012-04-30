incron-recursive
================

What this script does:
  - Recursive monitoring with incron, for newly created subdirectories in a parent folder.
  - Adds new watches to incrontab for newly created folders
  - Updates incrontab when files/folders are arbitrarily renamed/removed [including folders with spaces]
  - Add a .alternates folder to every newly created folder under the parent folder. 
  - On IN_CREATE events [files are added], HandBrakeCLI & ffmpeg are called to create

My incrontab entry looks something like this: 

/var/www/examplesite/projects IN_CREATE,IN_DELETE,IN_CLOSE_WRITE,IN_MOVED_TO /var/www/examplesite/update.py $# $@ $%

If you want to use this script: 
  - Change the variables scriptPath/curUser
  - chmod +x the script
  - Write access the watched folder.

The use case for this script is to monitor uploaded video files to a (watched) directory, and encode them to a webm and iPad format, for mobile viewing/HTML5 playback in Firefox. 

Cheers,
Thang