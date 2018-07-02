# Backupper
This is an incremental backupping program.
You specify the folder that you want to backup, and the folder you want the place the backup in.
**The program will then check for files that differ between both directories (i.e. have been changed since last
backup or simply haven't been backupped yet) and copy only those.**


# How to run
| Manner            | Doubleclick file:               | Important notes                                                |
| ----------------- |-------------------------------- | --------------------------------------------------------------:|
| **Windows Installer** | installer/JonathansBackupper_2-1.exe | Windows only, installs properly in Program Files      |
| Windows: .exe     | dist/main.exe                   | Windows only                                                   |
| Windows: shortcut | dist/Jonathan's Backupper(.lnk) | Windows only                                                   |
| Windows: .bat     | dist_py/run.bat                 | **Python must be installed, windows only**                     |
| Python: .pyw      | dist_py/main.pyw                | **Python must be installed**, run this file however you please |

The source code used for the development can, unsurprisingly, be found in the source/ folder.
