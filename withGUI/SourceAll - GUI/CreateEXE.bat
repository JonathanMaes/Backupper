@echo off
pyinstaller --onedir --add-data icon.ico;. main.pyw --noconsole
pause