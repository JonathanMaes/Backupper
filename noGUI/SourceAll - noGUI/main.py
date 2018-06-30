import os
import sys
import shutil
import win32api
from colorama import Fore, Back, Style, init
init(autoreset=True)


##############################################################################
class Language:
    EN = {
        'Copied file ' : 'Copied file ',
        'to ' : 'to ',
        'Drag and drop the folder that you want to backup ' : 'Drag and drop the folder that you want to backup ',
        'Drag and drop the folder where you want your backup to be placed ' : 'Drag and drop the folder where you want your backup to be placed ',
        'here' : 'here',
        ' and press enter.' : ' and press enter.',
        'You are about to backup' : 'You are about to backup',
        'If these are not the folders you want, type ' : 'If these are not the folders you want, type ',
        'CHANGE' : 'CHANGE',
        ' to change them.' : ' to change them.',
        'If the above information is correct, type ' : 'If the above information is correct, type ',
        'START' : 'START',
        ' to start the backup.' : ' to start the backup.',
        'Process aborted.' : 'Process aborted.\nPress any key to close this program...',
        ' does not exist, so can not be backupped.' : ' does not exist, so can not be backupped.',
        'Copying folder ' : 'Copying folder ',
        'Backup complete.' : 'Backup complete.',
        'Copied %d files, equal to %s.' : 'Copied %d files, equal to %s.',
        'Press enter to finish the backup.' : 'Press enter to finish the backup.'
    }
    NL = {
        'Copied file ' : 'Bestand gekopiëerd: ',
        'to ' : 'naar ',
        'Drag and drop the folder that you want to backup ' : 'Sleep de map die u wilt backuppen naar ',
        'Drag and drop the folder where you want your backup to be placed ' : 'Sleep de map waar u naartoe wilt backuppen naar ',
        'here' : 'hier',
        ' and press enter.' : ' en duw op enter.',
        'You are about to backup' : 'U staat op het punt om de volgende map te backuppen:',
        'If these are not the folders you want, type ' : 'Indien dit niet de correcte mappen zijn die u wenst te gebruiken, typ dan ',
        'CHANGE' : 'WIJZIG',
        ' to change them.' : '.',
        'If the above information is correct, type ' : 'Indien deze wel correct zijn, typ dan ',
        'START' : 'START',
        ' to start the backup.' : ' om de backup te starten.',
        'Process aborted.' : 'Proces afgebroken.\nDruk op een toets om dit programma te sluiten...',
        ' does not exist, so can not be backupped.' : ' bestaat niet, dus kan niet gebackupt worden.',
        'Copying folder ' : 'Map kopiëren: ',
        'Backup complete.' : 'Backup compleet.',
        'Copied %d files, equal to %s.' : '%d bestanden gekopiëerd, in totaal %s.',
        'Press enter to finish the backup.' : 'Druk op enter om de backup af te ronden.'
    }

Lang = Language.NL


def clearConsole():
    os.system('cls')


def readableBytes(size):
    power, n = 2**10, 0
    Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + ' ' + Dic_powerN[n]+'B'


def copyfile(fromPath, toPath, showInfo=True):
    shutil.copyfile(fromPath, toPath)
    if showInfo:
        print(Style.BRIGHT + Lang['Copied file '] + Fore.BLACK + fromPath)
        print(Style.BRIGHT + Lang['to '] + Fore.BLACK + toPath + Fore.BLUE + '\n(' + str(os.path.getsize(fromPath)) + ' bytes)\n')


def specifyDirectories(directoriesFile):
    os.system('mode con: cols=90 lines=4')   # Resizes cmd
    print(Style.BRIGHT + Fore.YELLOW + Lang['Drag and drop the folder that you want to backup '] + Fore.RED + Lang['here'] + Fore.YELLOW + Lang[' and press enter.'])
    fromDirectory = input()
    print(Style.BRIGHT + Fore.YELLOW + Lang['Drag and drop the folder where you want your backup to be placed '] + Fore.RED + Lang['here'] + Fore.YELLOW + Lang[' and press enter.'])
    toDirectory = input()
    with open(directoriesFile, 'w') as outFile:
        outFile.write(fromDirectory + '\n')
        outFile.write(toDirectory)
    backup(directoriesFile)


def backup(directoriesFile):
    '''Initialize the cmd window, get the directories if no errors while reading file'''
    os.system('title Jonathan\'s Backupper')  # Title of cmd screen
    os.system('mode con: cols=90 lines=9')   # Resizes cmd
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
    confirmString = Lang['START']
    enterDirectoriesString = Lang['CHANGE']
    print(Style.BRIGHT + Lang['You are about to backup'] + '\n ' + Fore.GREEN + fromDirectory)
    print(Style.BRIGHT + Lang['to '] + '\n ' + Fore.GREEN + toDirectory)
    print(Style.BRIGHT + '\n' + Lang['If these are not the folders you want, type '] + Fore.YELLOW + enterDirectoriesString + Fore.RESET + Lang[' to change them.'])
    print(Style.BRIGHT + Lang['If the above information is correct, type '] + Fore.YELLOW + confirmString + Fore.RESET + Lang[' to start the backup.'] + '\n')
    inp = input('> ')
    clearConsole()
    if inp == enterDirectoriesString:
        specifyDirectories(directoriesFile)
    elif inp != confirmString:
        sys.exit(Lang['Process aborted.'])
    
    
    '''Make sure all directories from before actually exist'''
    if not os.path.exists(fromDirectory):
        sys.exit(Style.BRIGHT + Fore.YELLOW + fromDirectory + Fore.RED + Lang[' does not exist, so can not be backupped.'])
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
                print(Style.BRIGHT + Lang['Copying folder '] + Fore.BLACK + os.path.join(path, dir))
        
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
    print(Style.BRIGHT + Fore.GREEN + Lang['Backup complete.'])
    print(Style.BRIGHT + Fore.GREEN + Lang['Copied %d files, equal to %s.'] % (stats['filesCopied'], readableBytes(stats['bytesCopied'])))
    print(Style.DIM + Fore.GREEN + Lang['Press enter to finish the backup.'])
    input()
    sys.exit()
##############################################################################


backup('BackupDirectories.txt')