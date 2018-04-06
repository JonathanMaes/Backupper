import os
import sys
import random
import string
import shutil
import win32api
from colorama import Fore, Back, Style, init
init(autoreset=True)


##############################################################################
def clearConsole():
    os.system('cls')


def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def readableBytes(size):
    power, n = 2**10, 0
    Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /=  power
        n += 1
    return str(round(size, 2)) + ' ' + Dic_powerN[n]+'B'


def copyfile(fromPath, toPath, showInfo=True):
    shutil.copyfile(fromPath, toPath)
    if showInfo:
        print(Style.BRIGHT + 'Copied file ' + Fore.BLACK + fromPath)
        print(Style.BRIGHT + 'to ' + Fore.BLACK + toPath + Fore.BLUE + '\n(' + str(os.path.getsize(fromPath)) + ' bytes)\n')


def specifyDirectories(directoriesFile):
    os.system('mode con: cols=90 lines=4')   # Resizes cmd
    print(Style.BRIGHT + Fore.YELLOW + 'Drag and drop the folder that you want to backup ' + Fore.RED + 'here' + Fore.YELLOW + ' and press enter.')
    fromDirectory = input()
    print(Style.BRIGHT + Fore.YELLOW + 'Drag and drop the folder where you want your backup to be placed ' + Fore.RED + 'here' + Fore.YELLOW + ' and press enter.')
    toDirectory = input()
    with open(directoriesFile, 'w') as outFile:
        outFile.write(fromDirectory + '\n')
        outFile.write(toDirectory)
    backup(directoriesFile)


def backup(directoriesFile):
    '''Initialize the cmd window, get the directories if no errors while reading file'''
    os.system('title Jonathan\'s Backupper')  # Title of cmd screen
    os.system('mode con: cols=70 lines=9')   # Resizes cmd
    os.system('color 0f')                     # Make sure the backgrond is black
    clearConsole()
    try:
        with open(directoriesFile, 'r') as inFile:
            lines = [line for line in inFile]
        fromDirectory = lines[0].strip().replace('/', '\\').strip('/\\')               # Replace / by \ and remove trailing / or \
        toDirectory = lines[1].strip().replace('/', '\\').strip('/\\')                 # Replace / by \ and remove trailing / or \
    except:
        specifyDirectories(directoriesFile)
    
    
    '''Ask if the directories are correct, and act accordingly'''
    confirmString = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    enterDirectoriesString = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    print(Style.BRIGHT + 'You are about to backup\n ' + Fore.GREEN + fromDirectory)# + Style.DIM + ' (' + str(get_size(fromDirectory)) + ' bytes)')
    print(Style.BRIGHT + 'to\n ' + Fore.GREEN + toDirectory)# + Style.DIM + ' (' + str(get_size(toDirectory)) + ' bytes)')
    print(Style.BRIGHT + '\nIf these are not the folders you want, type ' + Fore.YELLOW + enterDirectoriesString + Fore.RESET + ' to change them.')
    print(Style.BRIGHT + 'If the above information is correct, type '+ Fore.YELLOW + confirmString + Fore.RESET + ' to start the backup.\n')
    inp = input('> ')
    clearConsole()
    if inp == enterDirectoriesString:
        specifyDirectories(directoriesFile)
    elif inp != confirmString:
        sys.exit('Process aborted.\nPress any key to close this program...')
    
    
    '''Make sure all directories from before actually exist'''
    if not os.path.exists(fromDirectory):
        sys.exit(Style.BRIGHT + Fore.YELLOW + fromDirectory + Fore.RED + ' does not exist, so can not be backupped.')
    # If the directory to backup to does not exist, make it.
    if not os.path.exists(toDirectory):
        os.makedirs(toDirectory)
    
    
    '''Backup the directory to some other directory'''
    os.system('mode con: lines=' + str(win32api.GetSystemMetrics(1)//24))   # Resizes cmd (GetSystemMetrics(1) is screen height)
    #############################################
    ## Here is the actual backupping happening ##
    #############################################
    
    stats = {'filesCopied':0, 'bytesCopied':0}
    for path,dirs,files in os.walk(fromDirectory):
        # If the directories in this directory's backup do not exist already, make them
        directoryToWriteTo = toDirectory + path.split(fromDirectory)[-1]  # The toDirectory location of this particular directory
        for dir in dirs:
            toDir = os.path.join(directoryToWriteTo, dir)
            if not os.path.exists(toDir):
                os.makedirs(toDir)
                print(Style.BRIGHT + 'Copying folder ' + Fore.BLACK + os.path.join(path, dir))
        
        # And now the files
        for filename in files:
            pathName = os.path.join(path,filename)
            backupPathName = toDirectory + pathName.split(fromDirectory)[-1]
            
            # If the files in the backup are older than the ones in the original, or if the file does not even exist in the backup yet, copy it
            if not os.path.exists(backupPathName):
                copyfile(pathName, backupPathName, False)
                stats['filesCopied'] += 1
                stats['bytesCopied'] += os.path.getsize(pathName)
            elif os.path.getmtime(pathName) > os.path.getmtime(backupPathName):
                copyfile(pathName, backupPathName)
                stats['filesCopied'] += 1
                stats['bytesCopied'] += os.path.getsize(pathName)
    
    
    '''Print a last message'''
    os.system('mode con: lines=4')   # Resizes cmd
    print(Style.BRIGHT + Fore.GREEN + 'Backup complete.')
    print(Style.BRIGHT + Fore.GREEN + 'Copied ' + str(stats['filesCopied']) + ' files, equal to ' + readableBytes(stats['bytesCopied']) + '.')
    print(Style.DIM + Fore.GREEN + 'Press enter to finish the backup.')
    input()
    sys.exit()
##############################################################################


backup('BackupDirectories.txt')