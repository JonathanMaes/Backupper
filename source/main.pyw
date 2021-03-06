﻿# TO DO:
# * Move the total copied size to the progress bar: <files_copied>/<total_files>
#   And make the progress bar dependent on the number of bytes processed instead of the number of files
#   Problem is: this will further increase the time needed to 'initialize backup' by a factor of 7
#   But this can be used to calculate an approximate remaining time
# * [DONE, confirmation pending] Change console text to display the current file instead of the last copied one
# * Add a list of directories/files to ignore?
#   (in an Appdata file which can be opened through a button or something or in a top menubar)
# * Log the entire console to some file in appdata (can be disabled through menu button, save in options.txt)
# * Auto-check for updates via the github site
# * [DONE, confirmation pending] Display errors at the end

# Local imports
import programenv as pe
from translate import Language

# General imports
import os
import shutil
import win32api
import time
import json
import ctypes
import traceback
import sys

try:
    # Python 3.x
    import tkinter as tk
    from tkinter import ttk
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
        self.erroredFiles = []
        
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
        self.progressbar_text = tk.StringVar()
        self.progressbar_label = tk.Label(self.center_frame, textvariable = self.progressbar_text)
        
        # create the widgets for the bottom frame
        self.start_button = HoverButton(self.btm_frame, text = self.Lang['Start backup'], command = self.backup, bg="green2", activebackground="green4", fg="black", activeforeground="white")
        self.stop_button = HoverButton(self.btm_frame, text = self.Lang['Stop backup'], command = lambda: self.endBackup(stopped=True), bg="red2", activebackground="red4", fg="black", activeforeground="white")
        
        self.MB_text = tk.StringVar()
        self.MB_label = tk.Label(self.btm_frame, textvariable = self.MB_text)
        self.MB_text.set('')
        
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
            for example changing the number of lines displayed in the console.
            @param event [?]: Necessary for binding to <Configure> tkinter event.
        '''
        # Since we always read from the .height property, we need to update it accordingly
        self.console_log.height = (self.console_log.winfo_height()/2)//self.console_log.fontSize
    
    def report_callback_exception(self, *args):
        '''
            Function gets called when an exception occurs in tkinter itself.
            Since the console is invisible, the error is displayed in a custom window.
        '''
        pe.reportError(fatal=True, message='The tkinter GUI manager has encountered an error.')
        self.doBackup = False # Since an error occured, the backup should be 'properly' (sort of) stopped as well
    
    def reset(self):
        '''
            Resets the App by re-__init__ializing
        '''
        self.__init__(root, self.options)
    
    def languageChanged(self, *args):
        '''
            Resets the App, using the new language
        '''
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
        '''
            Resets the backup stats variable: self.stats
        '''
        self.stats = {'filesCopied':0, 'bytesCopied':0, 'filesChecked':0, 'errors':0}
        self.lastTime = time.time()
    
    def initializeBackup(self, fromDirectory):
        ''' 
            Does everything that needs to be done before the backup starts
            - sets self.doBackup to True
            - resets the backup stats (files copied, bytes copied...)
            - changes appearance of start and stop buttons
            - shows progress bar and sets its maximum
            @param fromDirectory [str]: The path of the directory that needs
                to be backupped.
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
        self.progressbar_label.grid(row=2, column=0, sticky="we")
        
        self.addMessage(self.Lang['Backup started.'])
    
    def endBackup(self, error=False, stopped=False):
        ''' 
            Does everything that needs to be done to properly stop the backup 
            - sets self.doBackup to False
            - if there was no error, say that everything was good
            - regardless of errors, reset the buttons and progressbar etc.
            @param error [bool]: Whether an error occured when initializing
                the backup.
            @param stopped [bool]: Whether the backup was stopped manually by
                the user by pressing the 'Stop backup' button.
        '''
        self.doBackup = False
        # Text in console
        if not error: # No error when initializing the backup
            if stopped: # Stopped by the user manually
                self.addMessage(self.Lang['Backup stopped.'], clear=True)
            else:
                self.addMessage(self.Lang['Backup complete.'], clear=True)
            self.addMessage(self.Lang['_filesCopiedInfo'] % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied'])))
            if len(self.erroredFiles) != 0: # If there were files that yielded an error while copying
                self.addMessage(self.Lang['Some files could not be copied:'])
                for file in self.erroredFiles:
                    self.addMessage(self.Lang['_reportFailedFile'] % file, crop=False)
        # Buttons
        self.stop_button.pack_forget()
        self.start_button.config(state='normal')
        # Progress bar
        self.progressbar.grid_forget()
        self.progressbar.config(value=0)
        self.progressbar_label.grid_forget()
        # Clear byte history for bytes/second measurement, and corresponding text
        self.byteHistory = [(time.time(), 0)]
        self.MB_text.set('')
        # Error history
        self.erroredFiles = []
    
    def scrollConsole(self, x):
        ''' 
            Scrolls the console to the end.
            @param x [?]: Necessary for binding to <<Modified>> tkinter event.
        '''
        self.console_log.see(tk.END)
        self.console_log.edit_modified(0)
        
    def addMessage(self, message, clear=False, newline=True, crop=True):
        ''' 
            Adds a new line to the self.console_log widget.
            This is not as easy as just adding a line: the Text widget must be
            enabled, then disabled, and out-of-sight lines deleted.
            @param message [str]: The message to be inserted into the console.
            @param clear [bool]: Whether to clear the entire console and keep
                only the new message.
            @param newline [bool]: Whether to begin a newline for this message.
            @param crop [bool]: Whether to crop the console to keep only the
                latest entries that are visible.
        '''
        self.console_log.config(state='normal')
        if clear:
            self.console_log.delete('1.0', tk.END)
        message += '\n' if newline else ''
        try:
            self.console_log.insert(tk.END, message, "indent")
        except:
            self.console_log.insert(tk.END, self.Lang["Copying file: File name could not be displayed."], "indent")
        if crop:
            self.console_log.delete('1.0', '%d.0' % (int(self.console_log.index('end-1c').split('.')[0])-self.console_log.height))
        self.console_log.config(state='disabled')
    
    def updatePaths(self, *args, **kwargs):
        '''
            Updates the options with the current text in the entry fields for
            the fromPath and toPath.
        '''
        self.options.set('fromPath', self.fromPathName.get())
        self.options.set('toPath', self.toPathName.get())

    def fromPathGet(self):
        '''
            Shows a dialog to choose the directory to backup.
        '''
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose the folder that you want to backup'], initialdir=self.fromPathName.get())
        if fileName:
            self.fromPathName.set(fileName)
            self.options.set('fromPath', fileName)
        
        
    def toPathGet(self):
        '''
            Shows a dialog to choose the directory to place the backup in.
        '''
        fileName = tk.filedialog.askdirectory(title = self.Lang['Choose folder to place backup in'], initialdir=self.toPathName.get())
        if fileName:
            self.toPathName.set(fileName)
            self.options.set('toPath', fileName)
    
    def readableBytes(self, size):
        '''
            Converts an int to a string displaying kB, MB, GB, TB...
            @param size [int]: The file size to convert to a readable format.
        '''
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
            @param fromPath [str]: The location of the original file.
            @param toPath [str]: The location of the copy of the file.
            @param renewedFile [bool]: Whether the file was already backupped
                previously, and this was just an update since the previously
                backupped file was outdated.
        '''
        if renewedFile:
            self.addMessage(self.Lang['Updating file: %s'] % fromPath)
        else:
            self.addMessage(self.Lang['Copying file: %s'] % fromPath)
        
        try:
            shutil.copyfile(fromPath, toPath)
            shutil.copystat(fromPath, toPath)
            self.stats['filesCopied'] += 1
            self.stats['bytesCopied'] += os.path.getsize(fromPath)
        except:
            self.addMessage(self.Lang['ERROR: Failed to copy %s'] % fromPath)
            self.stats['errors'] += 1
            self.erroredFiles.append(fromPath)
            return
        
    
    def updateGUI(self):
        '''
            Redraws the GUI.
            Also updates the bytesHistory list, which holds the total amount
            of bytes copied at each updateGUI call, and calculates the bytes/s
            using the self.lastTime variable to calculate the elapsed time.
        '''
        if time.time() - self.lastTime > 0.016:
            self.lastTime = time.time()
            # Bytes per second calculation
            self.byteHistory.append((time.time(), self.stats['bytesCopied']))
            self.byteHistory = self.byteHistory[-60:]
            byteRate = (self.byteHistory[-1][1] - self.byteHistory[0][1])/(self.byteHistory[-1][0] - self.byteHistory[0][0])
            bottom_text = (self.Lang['_filesCopiedInfo'] + ' (%s/s)') % (self.stats['filesCopied'], self.readableBytes(self.stats['bytesCopied']), self.readableBytes(byteRate))
            if len(self.erroredFiles) != 0:
                bottom_text = '%s (%d errors)' % (bottom_text, len(self.erroredFiles))
            self.MB_text.set(bottom_text)
            self.progressbar["value"] = self.stats['filesChecked']
            self.progressbar_text.set(self.Lang['_fileRatio'] % (self.stats['filesChecked'], self.progressbar.cget('maximum')))
            root.update()
    
    def backup(self):
        '''
            The main function that is called when 'Start backup' is pressed
        '''
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
                # Prevent issues with / or \ (error occurs when backupping whole D:/ or C:/ disk)
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
        self.appdataDirectory = os.path.expandvars(u"%%APPDATA%%\\%s" % pe.PROGRAMNAME)
        self.file = os.path.join(self.appdataDirectory, file)
        if not os.path.exists(self.appdataDirectory):
            os.makedirs(self.appdataDirectory)
        if not os.path.exists(self.file):
            self.reset()
        else:
            with open(self.file, 'r') as optionsFile:
                self.options = json.load(optionsFile)
    
    def updateFile(self):
        '''
            Writes the options dictionary to a json file to remember the settings
        '''
        with open(self.file, 'w') as optionsFile:
            json.dump(self.options, optionsFile)

    def set(self, optionName, value, saveFile=False):
        '''
            Changes one of the settings, including:
            - language : EN or NL
            - fromPath : the path to backup
            - toPath : the path to place the backup in
            @param optionName [str]: The name of the option to be updated.
            @param value [?]: The value to assign to that option.
            @param saveFile [bool]: Whether to save the options.json file
                after this update of the options object.
        '''
        self.options[optionName] = value
        self.updateFile()

    def get(self, optionName):
        '''
            Gets the specified option's value.
            @param optionName [str]: Name of the option that is requested.
        '''
        return self.options[optionName]

    def reset(self):
        '''
            Resets all options to the default settings.
        '''
        self.options = {'language' : 'EN', 'fromPath' : '', 'toPath' : ''}
        self.updateFile()


if __name__ == '__main__':
    willUpdate = pe.checkForUpdates()
    if willUpdate:
        sys.exit()

    # Tkinter
    root = tk.Tk()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    # Set width, height of window, and position of upper left corner on screen
    root.geometry('%dx%d+%d+%d' % (screen_width//2, screen_height//3, screen_width//4, screen_height//3))
    root.title(pe.PROGRAMNAME)
    root.iconbitmap('data/icon.ico')
    root.tk_setPalette(background='gray92', foreground='black')
    root.resizable(True, True)

    # Main app
    app = App(root, Options())