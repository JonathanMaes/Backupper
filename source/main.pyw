import os
import shutil
import win32api
import time
import json
from translate import Language

import traceback

try:
    # Python 3.x
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import showerror
    import tkinter.filedialog
except:
    # Python 2.x
    import Tkinter as tk
    from Tkinter import ttk
    from tkMessageBox import showerror
    import Tkinter.filedialog

root = tk.Tk()
root.geometry('800x340')
root.title('Jonathan\'s backupper')
root.iconbitmap('icon.ico')
root.tk_setPalette(background='gray92', foreground='black')
# root.resizable(False, False)


##############################################################################
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

class App(tk.Frame):
    def __init__(self, master, LangString='EN', fromDir = '', toDir = ''):
        super().__init__()
        
        master.report_callback_exception = self.report_callback_exception
        
        self.master = master
        self.Lang = {**Language['EN'], **Language[LangString]}
        self.resetStats()
        self.lastTime = 0
        self.byteHistory = [(time.time(), 0)]
        self.doBackup = False
        
        ## menubar testing
        '''self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        
        self.fileMenu = tk.Menu(self.menubar)
        self.fileMenu.add_command(label="Exit", command=lambda:self.quit())
        self.toggleVar = 0
        self.fileMenu.add_checkbutton(label="Toggle",variable=self.toggleVar)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)'''
        ## end of menubar testing
        
        # create all of the main containers
        self.top_frame = tk.Frame(master, pady=3)
        self.center_frame = tk.Frame(master, pady=3)
        self.btm_frame = tk.Frame(master, pady=3, padx=3)

        # layout all of the main containers
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.top_frame.grid(row=0, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1) # for entry widgets to stretch horizontally
        self.center_frame.grid(row=1, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.btm_frame.grid(row=2, sticky="ew")

        # create the widgets for the top frame
        self.fromPath_label = tk.Label(self.top_frame, text=self.Lang['Folder to backup'] + ': ')
        self.toPath_label = tk.Label(self.top_frame, text=self.Lang['Backup to'] + ': ')
        
        self.fromPathName = tk.StringVar()
        self.fromPathName.set(fromDir)
        self.fromPath_entry = tk.Entry(self.top_frame, textvariable=self.fromPathName, bg="white")
        self.fromPathBrowse = HoverButton(self.top_frame, text = self.Lang['Choose folder'], command = self.fromPathGet, bg="grey82", activebackground="grey72", fg="black", activeforeground="black")
        
        self.toPathName = tk.StringVar()
        self.toPathName.set(toDir)
        self.toPath_entry = tk.Entry(self.top_frame, textvariable=self.toPathName, bg="white")
        self.toPathBrowse = HoverButton(self.top_frame, text = self.Lang['Choose folder'], command = self.toPathGet, bg="grey82", activebackground="grey72", fg="black", activeforeground="black")
        
        # layout the widgets in the top frame
        self.fromPath_label.grid(row=0, column=0, sticky='E')
        self.fromPath_entry.grid(row=0, column=1, sticky='EW')
        self.fromPathBrowse.grid(row=0, column=2, padx=3, pady=3)
        self.toPath_label.grid(row=1, column=0, sticky='E')
        self.toPath_entry.grid(row=1, column=1, sticky='EW')
        self.toPathBrowse.grid(row=1, column=2, padx=3, pady=3)
        
        # create and layout the widgets for the center frame
        self.console_log = tk.Text(self.center_frame, state='disabled', bg="white", relief="solid", wrap=tk.WORD)
        self.console_log.tag_config("indent", lmargin2=20)
        self.console_log.bind('<<Modified>>', self.scrollConsole)
        self.console_log.height = self.console_log.cget('height')
        self.console_log.grid(row=0, column=0, sticky='nsew')
        self.addMessage(self.Lang['info'])
        
        self.progressbar = ttk.Progressbar(self.center_frame, orient=tk.HORIZONTAL, mode="determinate")
        
        # create the widgets for the bottom frame
        self.start_button = HoverButton(self.btm_frame, text = self.Lang['Start backup'], command = self.backup, bg="green2", activebackground="green4", fg="black", activeforeground="white")
        self.stop_button = HoverButton(self.btm_frame, text = self.Lang['Stop backup'], command = lambda: self.endBackup(stopped=True), bg="red2", activebackground="red4", fg="black", activeforeground="white")
        
        self.MB_text = tk.StringVar()
        self.MB_label = tk.Label(self.btm_frame, textvariable = self.MB_text)
        self.MB_text.set(self.Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        
        self.language_text = tk.StringVar()
        self.language_text.set(LangString)
        self.language_menu = tk.OptionMenu(self.btm_frame, self.language_text, *[lang for lang in Language])
        self.language_menu.config(indicatoron=0)
        self.language_text.trace('w', self.languageChanged)
        
        
        # layout the widgets for the bottom frame
        self.start_button.pack(side='left')
        self.language_menu.pack(side='right', padx=3)
        self.MB_label.pack(side='right')
    
    def report_callback_exception(self, *args):
        err = traceback.format_exception(*args)
        # since traceback.format_exception returns a list with each element being one line of the exception format, concatenate them
        formatted = ''
        for line in err:
            formatted += line
        showerror('An ERROR has occured.', formatted)
    
    def reset(self):
        self.__init__(root, getOption('language'), getOption('fromPath'), getOption('toPath'))
    
    def languageChanged(self, *args):
        if self.doBackup:
            self.language_text.set(getOption('language'))
            self.addMessage(self.Lang['Language cant be changed whilst backupping'])
            self.language_menu.pack()
            root.update()
            return None
        options['language'] = self.language_text.get()
        updateOptionsTxt(options)
        self.reset()
    
    def resetStats(self):
        self.stats = {'filesCopied':0, 'bytesCopied':0, 'filesChecked':0}
        self.lastTime = time.time()
    
    def initializeBackup(self, fromDirectory):
        self.doBackup = True
        self.resetStats()
        # Text in console
        self.addMessage(self.Lang['Preparing backup...'], clear=True)
        root.update()
        # Buttons
        self.start_button.config(state='disabled')
        self.stop_button.pack(side='left', padx=3)
        # Progress bar
        numFiles = sum([len(files) for r, d, files in os.walk(fromDirectory)])
        self.progressbar.grid(row=1, column=0, sticky="we")
        self.progressbar["maximum"] = numFiles
        
        self.addMessage(self.Lang['Backup started.'])
    
    def endBackup(self, error=False, stopped=False):
        self.doBackup = False
        # Text in console
        if not error:
            if stopped:
                self.addMessage(self.Lang['Backup stopped.'], clear=True)
            else:
                self.addMessage(self.Lang['Backup complete.'], clear=True)
            self.addMessage(self.Lang['Copied %d files, equal to %s.'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        # Buttons
        self.stop_button.pack_forget()
        self.start_button.config(state='normal')
        # Progress bar
        self.progressbar.grid_forget()
        self.progressbar["value"] = 0
        # Byte history
        self.byteHistory = [(time.time(), 0)]
    
    def scrollConsole(self, x):
        self.console_log.see(tk.END)
        self.console_log.edit_modified(0)
        
    def addMessage(self, message, clear=False, newline=True):
        self.console_log.config(state='normal')
        if clear:
            self.console_log.delete('1.0', tk.END)
        message +='\n' if newline else ''
        self.console_log.insert(tk.END, message, "indent")
        self.console_log.delete('1.0', '%d.0' % (int(self.console_log.index('end-1c').split('.')[0])-self.console_log.height))
        self.console_log.config(state='disabled')
    
    def fromPathGet(self, dirName=None):
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose the folder that you want to backup'])
        self.fromPathName.set(fileName)
        setOption('fromPath', fileName)
        
        
    def toPathGet(self, dirName=None):
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose folder to place backup in'])
        self.toPathName.set(fileName)
        setOption('toPath', fileName)
    
    def readableBytes(self, size):
        power, n = 2**10, 0
        Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return '%.2f %sB' % (size, Dic_powerN[n])
        
    def copyfile(self, fromPath, toPath, renewedFile=True):
        try:
            shutil.copyfile(fromPath, toPath)
            shutil.copystat(fromPath, toPath)
        except:
            self.addMessage(self.Lang['ERROR: Failed to copy %s'] % fromPath)
            return
        
        if renewedFile:
            self.addMessage(self.Lang['File updated: %s'] % fromPath)
        else:
            self.addMessage(self.Lang['File copied: %s'] % fromPath)
            
    def updateGUI(self):
        if time.time() - self.lastTime > 0.016:
            self.lastTime = time.time()
            # Bytes per second calculation
            self.byteHistory.append((time.time(), self.stats['bytesCopied']))
            self.byteHistory = self.byteHistory[-60:]
            self.MB_text.set((self.Lang['Copied %d files, equal to %s.'] + ' (%s/s)') % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied']), self.readableBytes((self.byteHistory[-1][1] - self.byteHistory[0][1])/(self.byteHistory[-1][0] - self.byteHistory[0][0]))))
            self.progressbar["value"] = self.stats['filesChecked']
            root.update()
    
    def backup(self):
        fromDirectory = self.fromPathName.get()
        toDirectory = self.toPathName.get()
        
        # Make sure the directory to backup actually exists
        if not os.path.exists(fromDirectory):
            self.addMessage(self.Lang['Folder to backup'] + ' (%s)' % fromDirectory + self.Lang[' does not exist, so can not be backupped.'], clear=True)
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
                    # If button 'stop backup' is pressed, stop the backup by exiting this function.
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
                    self.addMessage(self.Lang['Copying folder %s'] % os.path.join(path, dir))
            
            self.updateGUI()
        
        self.endBackup()

def updateOptionsTxt(options):
    with open('options.txt', 'w') as optionsFile:
        json.dump(options, optionsFile)

def setOption(optionName, value):
    options[optionName] = value
    updateOptionsTxt(options)

def getOption(optionName):
    return options[optionName]

def resetOptionsTxt():
    options = {'language' : 'EN', 'fromPath' : '', 'toPath' : ''}
    updateOptionsTxt(options)

if not os.path.exists('options.txt'):
    resetOptionsTxt()

with open('options.txt', 'r') as optionsFile:
    options = json.load(optionsFile)

app = App(root, options['language'], options['fromPath'], options['toPath'])
root.mainloop()