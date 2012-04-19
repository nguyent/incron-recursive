incron-recursive
================

Recursive monitoring with incron, for newly created subdirectories in a parent folder.

My incrontab entry looks something like this: 

/var/www/examplesite/projects IN_CREATE,IN_DELETE /var/www/soundtrack/output.py $# $@ $%

This script will monitor a parent directory, and look for whether a sub-directory has been 
added/removed and update incrontab to add a watch on the new sub-dir.

The idea for this script is to monitor a root folder where several other folders/files will be created, [in my case, video files], and run the appropriate actions on them. I've provided a barebones set up that will add/remove watches to incrontab, leaving the processFile function empty. 

If you want to use this script, be sure to change the variables scriptPath/curUser, chmod +x the script, and ensure you're able to write to the watched folder.

Cheers,
Thang