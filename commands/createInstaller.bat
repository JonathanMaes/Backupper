@echo off
cd ..
echo Compile the installer manually. Opening inno setup compiler...
installer.iss
pause
cd installer
XCOPY "JonathansBackupper_installer_*.exe" "JonathansBackupper_installer.exe" /C /Y /K
echo Finished.
pause >nul