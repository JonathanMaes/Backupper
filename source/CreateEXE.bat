@echo off
pyinstaller --onedir --add-data icon.ico;. main.pyw --noconsole --icon=icon.ico --clean
pause