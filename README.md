# Backupper
This is an incremental backupping program.
You specify the folder that you want to backup, and the folder you want the place the backup in.
The program will then check for files that are different (i.e., have been changed since last backup) in both directories and copy only those.

The .exe is quite a bit slower than the .bat file in the Distributable folder.

It is recommended to **use the Distributable/Backup.bat file instead of backup.exe if python is installed** since the .exe is quite a bit slower.
If python is not installed, the .bat file will obviously not work, while the .exe file will.
