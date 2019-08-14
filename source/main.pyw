# TO DO:
# * Move the total copied size to the progress bar: <files_copied>/<total_files>
#   And make the progress bar dependent on the number of bytes processed instead of the number of files
#   Problem is: this will further increase the time needed to 'initialize backup' by a factor of 7
# * Split the text at the bottom, that says how many files are copied, to:
#   <n> files copied, <errors> errors encountered \n (<bytes per second>), approximately <time> remaining.
# * Add two checkboxes next to the 'Stop backup' button:
#    one with 'Show Error messages', default 'true' (save edits in options)
#    another below with 'Show log of copied files', default 'false'
# * Add option 'Add to Start Menu' to installer
# * Change console text to display the current file instead of the last copied one
# * Add a list of directories/files to ignore
#   (in an Appdata file which can be opened through a button or something or in a top menubar)
# * Auto-check for updates via the github site
# * Display errors at the end


import os
import shutil
import win32api
import time
import json
import ctypes
from translate import Language

import traceback

try:
    # Python 3.x
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import showerror
    import tkinter.filedialog
except:
    raise ImportError('Python 3 (tkinter) is needed to run %s, but is not found.' % __name__)


##############################################################################
class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self,master=master,**kw)
        self.defaultBackground = self.cget("background")
        self.defaultForeground = self.cget("foreground")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if not self.cget("state") == "disabled":
            self.config(background=self.cget('activebackground'))
            self.config(foreground=self.cget('activeforeground'))

    def on_leave(self, e):
        self.config(background=self.defaultBackground)
        self.config(foreground=self.defaultForeground)

class App(tk.Frame):
    def __init__(self, master, options):
        self.options = options
        
        super().__init__()

        # Set DPI Awareness to fix blurry app on high DPI screens
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Windows 10/8
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware() # Windows 7/Vista
            except:
                pass
        
        # When an error occurs, open a custom window displaying the error
        master.report_callback_exception = self.report_callback_exception

        # When the root window is resized, call self.windowResized, this updates all widgets accordingly
        master.bind("<Configure>", self.windowResized)
        master.bind("<Key>", self.updatePaths)
        
        self.master = master
        self.Lang = {**Language['EN'], **Language[self.options.get('language')]} # Merge English and selected language dicts to fill in untranslated strings
        self.resetStats()
        self.lastTime = 0
        self.byteHistory = [(time.time(), 0)]
        self.doBackup = False
        
        ## menubar test
        '''self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        
        self.fileMenu = tk.Menu(self.menubar)
        self.fileMenu.add_command(label="Exit", command=lambda:self.quit())
        self.toggleVar = 0
        self.fileMenu.add_checkbutton(label="Toggle",variable=self.toggleVar)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)'''
        ## end menubar test
        
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
        self.fromPathName.set(self.options.get('fromPath'))
        self.toPathName = tk.StringVar()
        self.toPathName.set(self.options.get('toPath'))

        self.fromPath_entry = tk.Entry(self.top_frame, textvariable=self.fromPathName, bg="white", validate="all", validatecommand=self.updatePaths)
        self.fromPathBrowse = HoverButton(self.top_frame, text = self.Lang['Choose folder'], command = self.fromPathGet, bg="grey82", activebackground="grey72", fg="black", activeforeground="black")
        self.toPath_entry = tk.Entry(self.top_frame, textvariable=self.toPathName, bg="white", validate="all", validatecommand=self.updatePaths)
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
        self.console_log.fontSize = 10
        self.console_log.config(font=("Courier", self.console_log.fontSize))
        self.console_log.grid(row=0, column=0, sticky='nsew')
        
        self.progressbar = ttk.Progressbar(self.center_frame, orient=tk.HORIZONTAL, mode="determinate")
        
        # create the widgets for the bottom frame
        self.start_button = HoverButton(self.btm_frame, text = self.Lang['Start backup'], command = self.backup, bg="green2", activebackground="green4", fg="black", activeforeground="white")
        self.stop_button = HoverButton(self.btm_frame, text = self.Lang['Stop backup'], command = lambda: self.endBackup(stopped=True), bg="red2", activebackground="red4", fg="black", activeforeground="white")
        
        self.MB_text = tk.StringVar()
        self.MB_label = tk.Label(self.btm_frame, textvariable = self.MB_text)
        self.MB_text.set(self.Lang['_filesCopiedInfo'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        
        self.language_text = tk.StringVar()
        self.language_text.set(self.options.get('language'))
        self.language_menu = tk.OptionMenu(self.btm_frame, self.language_text, *[lang for lang in Language])
        self.language_menu.config(indicatoron=0)
        self.language_text.trace('w', self.languageChanged) # if the language is changed, this variable changes, so call self.languageChanged for further configurations
        
        
        # layout the widgets for the bottom frame
        self.start_button.pack(side='left')
        self.language_menu.pack(side='right', padx=3)
        self.MB_label.pack(side='right')
        
        root.update()
        
        # Display this message after root.update(), since otherwise
        # self.console_log.winfo_height() is still default 0 and the
        # message will thus be deleted by the addMessage function
        self.addMessage(self.Lang['info'])
        
        # Start interactivity
        master.mainloop()
    
    def windowResized(self, event):
        ''' 
            Handles everything that needs to be done when the window is resized,
            for example changing the number of lines displayed in the console 
        '''
        # Since we always read from the .height property, we need to update it accordingly
        self.console_log.height = (self.console_log.winfo_height()/2)//self.console_log.fontSize
    
    def report_callback_exception(self, *args):
        '''
            Function gets called when an exception occurs in Python itself.
            Since the console is invisible, the error is displayed in a custom window.
        '''
        # traceback.format_exception returns a list of strings, each being one line of the exception output,
        # so they are concatenated with ''.join
        etype, value, tb = args
        showerror('An ERROR has occured.', ''.join(traceback.format_exception(etype, value, tb)))
        # Since an error occured, the backup should be 'properly' stopped as well
        self.doBackup = False
    
    def reset(self):
        ''' Resets the App by re-__init__ializing '''
        self.__init__(root, self.options)
    
    def languageChanged(self, *args):
        ''' Resets the App, using the new language '''
        if self.doBackup:
            # Since the method to change the language is simply to reset the app,
            # it is not possible to change the language whilst backupping.
            self.language_text.set(self.options.get('language')) # Resets the language label to the one before the user tried to change it
            self.addMessage(self.Lang['Language cant be changed whilst backupping'])
            self.language_menu.pack()
            root.update()
            return None
        self.options.set('language', self.language_text.get(), saveFile=True)
        self.reset()
    
    def resetStats(self):
        ''' Resets the backup stats variable: self.stats '''
        self.stats = {'filesCopied':0, 'bytesCopied':0, 'filesChecked':0, 'errors':0}
        self.lastTime = time.time()
    
    def initializeBackup(self, fromDirectory):
        ''' 
            Does everything that needs to be done before the backup starts
            - sets self.doBackup to True
            - resets the backup stats (files copied, bytes copied...)
            - changes appearance of start and stop buttons
            - shows progress bar and sets its maximum
        '''
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
        self.progressbar.config(maximum=numFiles)
        
        self.addMessage(self.Lang['Backup started.'])
    
    def endBackup(self, error=False, stopped=False):
        ''' 
            Does everything that needs to be done to properly stop the backup 
            - sets self.doBackup to False
            - if there was no error, say that everything was good
            - regardless of errors, reset the buttons and progressbar etc.
        '''
        self.doBackup = False
        # Text in console
        if not error:
            if stopped:
                self.addMessage(self.Lang['Backup stopped.'], clear=True)
            else:
                self.addMessage(self.Lang['Backup complete.'], clear=True)
            self.addMessage(self.Lang['_filesCopiedInfo'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
        # Buttons
        self.stop_button.pack_forget()
        self.start_button.config(state='normal')
        # Progress bar
        self.progressbar.grid_forget()
        self.progressbar.config(value=0)
        # Byte history for bytes/second measurement
        self.byteHistory = [(time.time(), 0)]
    
    def scrollConsole(self, x):
        ''' Scrolls the console to the end '''
        self.console_log.see(tk.END)
        self.console_log.edit_modified(0)
        
    def addMessage(self, message, clear=False, newline=True):
        ''' 
            Adds a new line to the self.console_log widget.
            This is not as easy as just adding a line: the Text widget must be
            enabled, then disabled, and out-of-sight lines deleted.
        '''
        self.console_log.config(state='normal')
        if clear:
            self.console_log.delete('1.0', tk.END)
        message +='\n' if newline else ''
        self.console_log.insert(tk.END, message, "indent")
        self.console_log.delete('1.0', '%d.0' % (int(self.console_log.index('end-1c').split('.')[0])-self.console_log.height))
        self.console_log.config(state='disabled')
    
    def updatePaths(self, *args, **kwargs):
        self.options.set('fromPath', self.fromPathName.get())
        self.options.set('toPath', self.toPathName.get())

    def fromPathGet(self, dirName=None):
        ''' Shows a dialog to choose the directory to backup '''
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose the folder that you want to backup'], initialdir=self.fromPathName.get())
        if fileName:
            self.fromPathName.set(fileName)
            self.options.set('fromPath', fileName)
        
        
    def toPathGet(self, dirName=None):
        ''' Shows a dialog to choose the directory to place the backup in '''
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose folder to place backup in'], initialdir=self.toPathName.get())
        if fileName:
            self.toPathName.set(fileName)
            self.options.set('toPath', fileName)
    
    def readableBytes(self, size):
        ''' Converts an int to a string displaying kB, MB, GB, TB... '''
        power, n = 2**10, 0
        Dic_powerN = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return '%.2f %sB' % (size, Dic_powerN[n])
        
    def copyfile(self, fromPath, toPath, renewedFile=True):
        ''' 
            Copies a file. Updates backup stats accordingly and catches copy-
            errors. Displays a corresponding message in self.console_log. 
        '''
        try:
            shutil.copyfile(fromPath, toPath)
            shutil.copystat(fromPath, toPath)
            self.stats['filesCopied'] += 1
            self.stats['bytesCopied'] += os.path.getsize(fromPath)
        except:
            self.addMessage(self.Lang['ERROR: Failed to copy %s'] % fromPath)
            self.stats['errors'] += 1
            return
        
        if renewedFile:
            self.addMessage(self.Lang['File updated: %s'] % fromPath)
        else:
            self.addMessage(self.Lang['File copied: %s'] % fromPath)
    
    def updateGUI(self):
        ''' Redraws the GUI.
            Also updates the bytesHistory list, which holds the total amount
            of bytes copied at each updateGUI call, and calculates the bytes/s
            using the self.lastTime variable to calculate the elapsed time.
        '''
        if time.time() - self.lastTime > 0.016:
            self.lastTime = time.time()
            # Bytes per second calculation
            self.byteHistory.append((time.time(), self.stats['bytesCopied']))
            self.byteHistory = self.byteHistory[-60:]
            self.MB_text.set((self.Lang['_filesCopiedInfo'] + ' (%s/s)') % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied']), self.readableBytes((self.byteHistory[-1][1] - self.byteHistory[0][1])/(self.byteHistory[-1][0] - self.byteHistory[0][0]))))
            self.progressbar["value"] = self.stats['filesChecked']
            root.update()
    
    def backup(self):
        ''' The main function that is called when 'start backup' is pressed '''
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
                # Prevent issues whith / or \ (error occurs when backupping whole D:/ or C:/ disk)
                backupPathName = toDirectory + pathName.split(fromDirectory.strip('\\/ '))[-1]
                
                # If the file does not yet exist in the backup directory
                if not os.path.exists(backupPathName):
                    self.copyfile(pathName, backupPathName, False)
                # If the file in the backup directory is older than the original
                elif os.path.getmtime(pathName) > os.path.getmtime(backupPathName):
                    self.copyfile(pathName, backupPathName)
                
                self.updateGUI()
            
            # If the directories in this directory's backup do not exist already, make them
            directoryToWriteTo = toDirectory + path.split(fromDirectory.strip('\\/ '))[-1]  # The toDirectory location of this particular directory
            for dir in dirs:
                toDir = os.path.join(directoryToWriteTo, dir)
                if not os.path.exists(toDir):
                    os.makedirs(toDir)
                    self.addMessage(self.Lang['Copying folder %s'] % os.path.join(path, dir))
            
            self.updateGUI()
        
        self.endBackup()


class Options():
    def __init__(self, file='options.json'):
        self.appdataDirectory = os.path.expandvars("%APPDATA%\\Jonathan's Backupper")
        self.file = os.path.join(self.appdataDirectory, file)
        if not os.path.exists(self.appdataDirectory):
            os.makedirs(self.appdataDirectory)
        if not os.path.exists(self.file):
            self.reset()
        else:
            with open(self.file, 'r') as optionsFile:
                self.options = json.load(optionsFile)
    
    def updateFile(self):
        ''' Writes the options dictionary to a json file to remember the settings '''
        with open(self.file, 'w') as optionsFile:
            json.dump(self.options, optionsFile)

    def set(self, optionName, value, saveFile=False):
        ''' 
            Changes one of the settings, including:
            - language : EN or NL
            - fromPath : the path to backup
            - toPath : the path to place the backup in
        '''
        self.options[optionName] = value
        self.updateFile()

    def get(self, optionName):
        ''' Gets the specified options value '''
        return self.options[optionName]

    def reset(self):
        ''' Resets all options to the default settings '''
        self.options = {'language' : 'EN', 'fromPath' : '', 'toPath' : ''}
        self.updateFile()


if __name__ == '__main__':
    root = tk.Tk()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    # Set width, height of window, and position of upper left corner on screen
    root.geometry('%dx%d+%d+%d' % (screen_width//2, screen_height//3, screen_width//4, screen_height//3))
    root.title('Jonathan\'s backupper')
    root.iconbitmap('data/icon.ico')
    root.tk_setPalette(background='gray92', foreground='black')
    root.resizable(True, True)

    app = App(root, Options())