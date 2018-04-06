# Backupper
This is an incremental backupping program.
You specify the folder you want to backup and the folder to backup to.
The program will then check for files that are different in both directories and copy only those.

The .exe is quite a bit slower than the .bat file in the Distributable folder.

It is recommended to **use the Distributable/Backup.bat file instead of backup.exe if python is installed** since the .exe is quite a bit slower.
If python is not installed, the .bat file will obviously not work, while the .exe file will.

* The SourceAll folder is the code used for development.
* The Distributable folder is a folder containing the minimum required files.
* The BackupperDistrib.zip file is the zipped version of the Distributable folder.
* The backup.exe file is a one-click executable of the backupper, but is significantly slower.
