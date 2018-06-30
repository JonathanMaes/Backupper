import os
import shutil
import win32api
import time

try:
    import Tkinter as tk
    import Tkinter.filedialog
except:
    import tkinter as tk
    import tkinter.filedialog
root = tk.Tk()
root.geometry('800x340')
root.title('Jonathan\'s backupper')
root.iconbitmap('icon.ico')
root.resizable(False, False)


##############################################################################
class Language:
    EN = {
        'Browse' : 'Browse',
        'Choose the folder that you want to backup' : 'Choose the folder that you want to backup',
        'Choose folder to place backup in' : 'Choose folder to place backup in',
        'Folder to backup' : 'Folder to backup',
        'Backup to' : 'Backup to',
        'Start backup' : 'Start backup',
        'Choose the folder that you want to backup, and the folder where you want the backup to be placed in.' : 'Choose the folder that you want to backup, and the folder where you want the backup to be placed in.',
        'File updated: ' : 'File updated: ',
        'File copied: ' : 'File copied: ',
        ' does not exist, so can not be backupped.' : ' does not exist, so can not be backupped.',
        'Copying folder ' : 'Copying folder ',
        'Backup complete.' : 'Backup complete.',
        'Copied %d files, equal to %s.' : 'Copied %d files, equal to %s.'
    }
    NL = {
        'Browse' : 'Map kiezen',
        'Choose the folder that you want to backup' : 'Kies de map die u wil backuppen',
        'Choose folder to place backup in' : 'Kies map om backup in te plaatsen',
        'Folder to backup' : 'Te kopiëren map',
        'Backup to' : 'Backuppen naar',
        'Start backup' : 'Start backup',
        'Choose the folder that you want to backup, and the folder where you want the backup to be placed in.' : 'Kies de map die u wil backuppen, en de map waar u de backup in wil plaatsen.',
        'File updated: ' : 'Bestand geüpdatet: ',
        'File copied: ' : 'Bestand gekopieerd: ',
        ' does not exist, so can not be backupped.' : ' bestaat niet, dus kan niet gebackupt worden.',
        'Copying folder ' : 'Map kopiëren: \t\t',
        'Backup complete.' : 'Backup compleet.',
        'Copied %d files, equal to %s.' : '%d bestanden gekopiëerd, in totaal %s.'
    }

Lang = Language.NL


class App:
    def __init__(self, master):
        self.stats = {'filesCopied':0, 'bytesCopied':0}
        
        # create all of the main containers
        self.top_frame = tk.Frame(root, width=450, height=50, pady=3)
        self.center_frame = tk.Frame(root, width=450, height=200, pady=3)
        self.btm_frame = tk.Frame(root, width=450, height=45, pady=3, padx=3)

        # layout all of the main containers
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.top_frame.grid(row=0, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1) # for entry widgets to stretch horizontally
        self.center_frame.grid(row=1, sticky="nsew")
        self.btm_frame.grid(row=2, sticky="ew")

        # create the widgets for the top frame
        self.fromPath_label = tk.Label(self.top_frame, text=Lang['Folder to backup'] + ': ')
        self.toPath_label = tk.Label(self.top_frame, text=Lang['Backup to'] + ': ')
        
        self.fromPathName = tk.StringVar()
        self.fromPath_entry = tk.Entry(self.top_frame, textvariable=self.fromPathName)
        self.fromPathBrowse = tk.Button(self.top_frame, text = Lang['Browse'], command = self.fromPathGet)
        
        self.toPathName = tk.StringVar()
        self.toPath_entry = tk.Entry(self.top_frame, textvariable=self.toPathName)
        self.toPathBrowse = tk.Button(self.top_frame, text = Lang['Browse'], command = self.toPathGet)
        
        # layout the widgets in the top frame
        self.fromPath_label.grid(row=0, column=0, sticky='E')
        self.fromPath_entry.grid(row=0, column=1, sticky='EW')
        self.fromPathBrowse.grid(row=0, column=2, padx=3, pady=3)
        self.toPath_label.grid(row=1, column=0, sticky='E')
        self.toPath_entry.grid(row=1, column=1, sticky='EW')
        self.toPathBrowse.grid(row=1, column=2, padx=3, pady=3)
        
        # create the widgets for the center frame
        self.console_log = tk.Text(self.center_frame, height=10, state='disabled')
        self.console_log.bind('<<Modified>>', self.scrollConsole)
        self.console_log.height = self.console_log.cget('height')
        self.console_log.grid(row=0, column=0, sticky='we')
        self.addMessage(Lang['Choose the folder that you want to backup, and the folder where you want the backup to be placed in.'] + '\n')
        
        
        # create the widgets for the bottom frame
        self.start_button = tk.Button(self.btm_frame, text = Lang['Start backup'], command = self.backup, bg="grey", activebackground="grey")
        self.MB_text = tk.StringVar()
        self.MB_label = tk.Label(self.btm_frame, textvariable = self.MB_text)
        self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        
        # layout the widgets for the bottom frame
        self.start_button.pack(side='left')
        self.MB_label.pack(side='right')
    
    def startBackup(self):
        t = threading.Thread(target=self.backup)
        t.start()
    
    def scrollConsole(self, x):
        self.console_log.see(tk.END)
        self.console_log.edit_modified(0)
        
    def addMessage(self, message, clear=False):
        self.console_log.config(state='normal')
        if clear:
            self.console_log.delete('1.0', tk.END)
        self.console_log.insert(tk.END, message)
        self.console_log.delete('1.0', '%d.0' % (int(self.console_log.index('end-1c').split('.')[0])-self.console_log.height))
        self.console_log.pack()
        self.console_log.config(state='disabled')
    
    def fromPathGet(self, dirName=None):
        fileName = tk.filedialog.askdirectory(title = Lang['Choose the folder that you want to backup'])
        self.fromPathName.set(fileName)
        
    def toPathGet(self, dirName=None):
        fileName = tk.filedialog.askdirectory(title = Lang['Choose folder to place backup in'])
        self.toPathName.set(fileName)
    
    def readableBytes(self, size):
        power, n = 2**10, 0
        Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return '%.2f %sB' % (size, Dic_powerN[n])
        
    def copyfile(self, fromPath, toPath, renewedFile=True):
        shutil.copyfile(fromPath, toPath)
        if renewedFile:
            self.addMessage(Lang['File updated: '] + fromPath + '\n')
        else:
            self.addMessage(Lang['File copied: '] + fromPath + '\n')
    
    def backup(self):
        fromDirectory = self.fromPathName.get()
        toDirectory = self.toPathName.get()
        
        '''Make sure all directories from before actually exist'''
        
        if not os.path.exists(fromDirectory):
            self.addMessage(Lang['Folder to backup'] + ' (%s)' % fromDirectory + Lang[' does not exist, so can not be backupped.'], clear=True)
            return None
        # If the directory to backup to does not exist, make it.
        if not os.path.exists(toDirectory):
            os.makedirs(toDirectory)
        
        self.start_button.config(state='disabled')

        #############################################
        ## Here is the actual backupping happening ##
        #############################################
        
        self.stats = {'filesCopied':0, 'bytesCopied':0}
        lastTime = time.time()
        for path,dirs,files in os.walk(fromDirectory):
            # Copy the files in this directory
            for filename in files:
                pathName = os.path.join(path,filename)
                backupPathName = toDirectory + pathName.split(fromDirectory)[-1]
                
                # If the files in the backup are older than the ones in the original, or if the file does not even exist in the backup yet, copy it
                if not os.path.exists(backupPathName):
                    self.copyfile(pathName, backupPathName, False)
                    self.stats['filesCopied'] += 1
                    self.stats['bytesCopied'] += os.path.getsize(pathName)
                    if time.time() - lastTime > 0.016:
                        lastTime = time.time()
                        self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
                        root.update()
                elif os.path.getmtime(pathName) > os.path.getmtime(backupPathName):
                    self.copyfile(pathName, backupPathName)
                    self.stats['filesCopied'] += 1
                    self.stats['bytesCopied'] += os.path.getsize(pathName)
                    if time.time() - lastTime > 0.016:
                        lastTime = time.time()
                        self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
                        root.update()
            
            
            # If the directories in this directory's backup do not exist already, make them
            directoryToWriteTo = toDirectory + path.split(fromDirectory)[-1]  # The toDirectory location of this particular directory
            for dir in dirs:
                toDir = os.path.join(directoryToWriteTo, dir)
                if not os.path.exists(toDir):
                    os.makedirs(toDir)
                    self.addMessage(Lang['Copying folder '] + os.path.join(path, dir) + '\n')
            
            self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
            if time.time() - lastTime > 0.016:
                lastTime = time.time()
                self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
                root.update()
        
        '''Print a last message'''
        self.addMessage(Lang['Backup complete.'] + '\n', clear=True)
        self.addMessage(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        self.start_button.config(state='normal')
        self.start_button.flash()



app = App(root)
root.mainloop()
