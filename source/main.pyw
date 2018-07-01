import os
import shutil
import win32api
import time
from translate import Language

try:
    import Tkinter as tk
    from Tkinter import ttk
    import Tkinter.filedialog
except:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.filedialog
root = tk.Tk()
root.geometry('800x340')
root.title('Jonathan\'s backupper')
root.iconbitmap('icon.ico')
root.tk_setPalette(background='gray92', foreground='black')
root.resizable(False, False)


##############################################################################
Lang = Language.NL

class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self,master=master,**kw)
        self.defaultBackground = self["background"]
        self.defaultForeground = self["foreground"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if not self["state"] == "disabled":
            self['background'] = self['activebackground']
            self['foreground'] = self['activeforeground']

    def on_leave(self, e):
        self['background'] = self.defaultBackground
        self['foreground'] = self.defaultForeground

class App:
    def __init__(self, master):
        self.resetStats()
        self.lastTime = 0
        self.byteHistory = [(time.time(), 0)]
        self.doBackup = True
        
        # create all of the main containers
        self.top_frame = tk.Frame(root, pady=3)
        self.center_frame = tk.Frame(root, pady=3)
        self.btm_frame = tk.Frame(root, pady=3, padx=3)

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
        self.fromPath_entry = tk.Entry(self.top_frame, textvariable=self.fromPathName, bg="white")
        self.fromPathBrowse = HoverButton(self.top_frame, text = Lang['Browse'], command = self.fromPathGet, bg="grey82", activebackground="grey72", fg="black", activeforeground="black")
        
        self.toPathName = tk.StringVar()
        self.toPath_entry = tk.Entry(self.top_frame, textvariable=self.toPathName, bg="white")
        self.toPathBrowse = HoverButton(self.top_frame, text = Lang['Browse'], command = self.toPathGet, bg="grey82", activebackground="grey72", fg="black", activeforeground="black")
        
        # layout the widgets in the top frame
        self.fromPath_label.grid(row=0, column=0, sticky='E')
        self.fromPath_entry.grid(row=0, column=1, sticky='EW')
        self.fromPathBrowse.grid(row=0, column=2, padx=3, pady=3)
        self.toPath_label.grid(row=1, column=0, sticky='E')
        self.toPath_entry.grid(row=1, column=1, sticky='EW')
        self.toPathBrowse.grid(row=1, column=2, padx=3, pady=3)
        
        # create the widgets for the center frame
        self.console_log = tk.Text(self.center_frame, height=10, state='disabled', bg="white")
        self.console_log.bind('<<Modified>>', self.scrollConsole)
        self.console_log.height = self.console_log.cget('height')
        self.console_log.grid(row=0, column=0, sticky='we')
        self.addMessage(Lang['Choose the folder that you want to backup, and the folder where you want the backup to be placed in.'] + '\n')
        
        self.progressbar = ttk.Progressbar(self.center_frame, orient=tk.HORIZONTAL, mode="determinate")
        
        # create the widgets for the bottom frame
        self.start_button = HoverButton(self.btm_frame, text = Lang['Start backup'], command = self.backup, bg="green2", activebackground="green4", fg="black", activeforeground="white")
        self.stop_button = HoverButton(self.btm_frame, text = Lang['Stop backup'], command = lambda: self.endBackup(stopped=True), bg="red2", activebackground="red4", fg="black", activeforeground="white")
        self.MB_text = tk.StringVar()
        self.MB_label = tk.Label(self.btm_frame, textvariable = self.MB_text)
        self.MB_text.set(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        
        # layout the widgets for the bottom frame
        self.start_button.pack(side='left')
        self.MB_label.pack(side='right')
    
    def resetStats(self):
        self.stats = {'filesCopied':0, 'bytesCopied':0, 'filesChecked':0}
        self.lastTime = time.time()
    
    def initializeBackup(self, fromDirectory):
        self.doBackup = True
        self.resetStats()
        # Text in console
        self.addMessage(Lang['Preparing backup...'] + '\n', clear=True)
        root.update()
        # Buttons
        self.start_button.config(state='disabled')
        self.stop_button.pack(side='left', padx=3)
        # Progress bar
        numFiles = sum([len(files) for r, d, files in os.walk(fromDirectory)])
        root.geometry('800x360')
        self.progressbar.grid(row=1, column=0, sticky="we")
        self.progressbar["maximum"] = numFiles
    
    def endBackup(self, error=False, stopped=False):
        self.doBackup = False
        # Text in console
        if not error:
            if stopped:
                self.addMessage(Lang['Backup stopped.'] + '\n', clear=True)
            else:
                self.addMessage(Lang['Backup complete.'] + '\n', clear=True)
            self.addMessage(Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        # Buttons
        self.stop_button.pack_forget()
        self.start_button.config(state='normal')
        # Progress bar
        root.geometry('800x340')
        self.progressbar.grid_forget()
        self.progressbar["value"] = 0
        # Byte history
        self.byteHistory = [(time.time(), 0)]
    
    def scrollConsole(self, x):
        self.console_log.see(tk.END)
        self.console_log.edit_modified(0)
        
    def addMessage(self, message, clear=False):
        self.console_log.config(state='normal')
        if clear:
            self.console_log.delete('1.0', tk.END)
        self.console_log.insert(tk.END, message)
        self.console_log.delete('1.0', '%d.0' % (int(self.console_log.index('end-1c').split('.')[0])-self.console_log.height))
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
        shutil.copystat(fromPath, toPath)
        if renewedFile:
            self.addMessage(Lang['File updated: '] + fromPath + '\n')
        else:
            self.addMessage(Lang['File copied: '] + fromPath + '\n')
            
    def updateGUI(self):
        if time.time() - self.lastTime > 0.016:
            self.lastTime = time.time()
            # Bytes per second calculation
            self.byteHistory.append((time.time(), self.stats['bytesCopied']))
            self.byteHistory = self.byteHistory[-60:]
            self.MB_text.set((Lang['Copied %d files, equal to %s.'] + ' (%s/s)') % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied']), self.readableBytes((self.byteHistory[-1][1] - self.byteHistory[0][1])/(self.byteHistory[-1][0] - self.byteHistory[0][0]))))
            self.progressbar["value"] = self.stats['filesChecked']
            root.update()
    
    def backup(self):
        fromDirectory = self.fromPathName.get()
        toDirectory = self.toPathName.get()
        
        # Make sure the directory to backup actually exists
        if not os.path.exists(fromDirectory):
            self.addMessage(Lang['Folder to backup'] + ' (%s)' % fromDirectory + Lang[' does not exist, so can not be backupped.'], clear=True)
            self.endBackup(error=True)
            return None
        # If the directory to backup to does not exist, make it.
        if not os.path.exists(toDirectory):
            os.makedirs(toDirectory)
        
        self.initializeBackup(fromDirectory)
        
        #############################################
        ## Here is the actual backupping happening ##
        #############################################
        
        for path,dirs,files in os.walk(fromDirectory):
            # Copy the files in this directory
            for filename in files:
                if not self.doBackup:
                    return None
                self.stats['filesChecked'] += 1
                pathName = os.path.join(path,filename)
                backupPathName = toDirectory + pathName.split(fromDirectory)[-1]
                
                # If the file does not yet exist in the backup directory
                if not os.path.exists(backupPathName):
                    self.copyfile(pathName, backupPathName, False)
                    self.stats['filesCopied'] += 1
                    self.stats['bytesCopied'] += os.path.getsize(pathName)
                # If the file in the backup directory is older than the original
                elif os.path.getmtime(pathName) > os.path.getmtime(backupPathName):
                    self.copyfile(pathName, backupPathName)
                    self.stats['filesCopied'] += 1
                    self.stats['bytesCopied'] += os.path.getsize(pathName)
                
                self.updateGUI()
            
            # If the directories in this directory's backup do not exist already, make them
            directoryToWriteTo = toDirectory + path.split(fromDirectory)[-1]  # The toDirectory location of this particular directory
            for dir in dirs:
                toDir = os.path.join(directoryToWriteTo, dir)
                if not os.path.exists(toDir):
                    os.makedirs(toDir)
                    self.addMessage(Lang['Copying folder '] + os.path.join(path, dir) + '\n')
            
            self.updateGUI()
        
        self.endBackup()

app = App(root)
root.mainloop()
