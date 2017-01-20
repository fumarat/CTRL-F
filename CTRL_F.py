#! /usr/bin/env python

"""
=======
CTRL-F
=======

DESCRIPTION:
GUI for searching a sequence/regular expression in PyMol objects and/or selections.
Input is assumed to be one letter amino acid code.

FEATURES:
> Search with a string of one letter code amino acids
> Seach in either a single, selected PyMol object 
  or selection or all available objects/selection
> Seach either by entering a search string an pressing "Find" or hitting enter
  or by using the interactive search mode in which every key press triggers a search;
  much like you are used to from Strg-F find appliations like in web browsers
> combine interactive and global searches
> use regular expressions instead of one letter amino acid codes

USAGE:
Install the CTRL-F.py plugin with PyMol's plugin installer.
See Help window in the GUI for a quick usage reference.
Otherwise see the readme file in https://github.com/fumarat/CTRL-F

AUTHOR:
Max Plach, 2017

ACKNOWLEDGEMENTS:
e-leon (look in github if you are interested)

LICENSE:
BSD-2-Clause, see https://opensource.org/licenses/BSD-2-Clause

USED SOFTWARE:
CTRL-F uses findseq by Jason Vertrees, 2009. See https://pymolwiki.org/index.php/Findseq
findseq copyright 2009, Jason Vertrees, BSD-2-Clause

Disclaimer:
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""


from Tkinter import *
from pymol import cmd
import re
import types
import random
import time
from pymol import cmd, plugins
import webbrowser

#==========================
# Create CTRL-F Application
#==========================

class CTRLF(Frame):

    #=====================
    # Initialize the class
    #=====================
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.parent = parent

        # Initialize a variable for storing the search all option
        self.searchall = IntVar()

        # Initialize a variable for storing the interactive option
        self.interactive = IntVar()

        # Initialize a variable for storing the searchs string
        self.search_var = StringVar()

        # Initialize a variable for storing the pymol object or selection
        self.pymol_selection = StringVar()

        # Generate the widgets
        self.pack()
        self.create_widgets()

        # Trace the search string input for interactive searching
        self.search_var.trace("w", self.search_var_trace)

        # Fill the listbox with available pymol objects and selections
        self.pymollist = []
        self.fill_pymol_list()

        # Initialize the lists for storing the
        # list of searchable objects and selctions = searchlist
        # the list of strings to search = searchstrings
        self.searchlist = []
        self.searchstrings = []

        # Check if only a single PyMol object/selection is available
        # if yes, print a status message that this
        if len(cmd.get_names("objects",1)) == 1:
            self.labelStatusDisplay.configure(text="Selected %s" % cmd.get_names("objects",1)[0])
        else:
            pass

        # Initialize a list for keeping track of the old searches
        # and for deleting them
        self.oldsearches = []

    #============================
    # Create the main GUI widgets
    #============================
    def create_widgets(self):

        #=======================
		# Widdget Initialization
        #=======================

        self.labelObjSel = Label(self,
            font = "{MS Sans Serif} 8 bold",
            text = "Objects and Selections",
        )
        self.labelSearch = Label(self,
            font = "{MS Sans Serif} 8 bold",
            text = "Search",
        )
        self.labelStatusDisplay = Label(self,
            justify = "center",
            text = "Status Display",
            wraplength = 150,
        )
        self.lboxObjSel = Listbox(self,
            height = 0,
            width = 0,
        )
        self.entry = Entry(self,
            textvariable=self.search_var,
            width = 0,
        )
        self.buttonSearch = Button(self,
            text = "Find",
            width = 15,
        )
        self.buttonClear = Button(self,
            text = "Clear all hits",
            width = 15,
        )
        self.checkboxSearchAll = Checkbutton(self,
            takefocus = 1,
            text = "search in all",
        )
        self.checkboxInteractive = Checkbutton(self,
            text = "interactive",
        )
        self.labelStatus = Label(self,
            font = "{MS Sans Serif} 8 bold",
            text = "Status",
        )
        self.buttonHelp = Button(self,
            text = "Help",
            width = 15,
        )
        self.buttonAbout = Button(self,
            text = "About",
            width = 15,
        )

        
        #=====================
        # Widget configuration
        #=====================

        # Bind a click on the listbox of PyMol objects/selections to get the selection
        self.lboxObjSel.bind("<Button-1>", self.get_searchstring)

        # Configure the entry widget
        self.entry.configure(
            width=20
        )
        
        # Bind the enter key when in the searchbox to start the search
        self.entry.bind("<Return>", self.action_searchbutton)

        # Set focus to the entry widget
        self.entry.focus()

        # Bind the action to the search button
        self.buttonSearch.configure(
            command = self.action_searchbutton
        )

        # Bind the action to the Clear button
        self.buttonClear.configure(
            command = self.action_deletebutton
        )

        # Configure the listbox that displays previous searches
        #self.lboxPreviousSearches.bind("<<ListboxSelect>>", self.get_searchstring)

        # Configure a checkbutton for searching in all available pymol objects and selections
        self.checkboxSearchAll.configure(
            variable = self.searchall,
            command = self.action_searchall
        )

        # Configure a checkbutton for interactive searches (real-time highlighting)
        self.checkboxInteractive.configure(
            variable = self.interactive,
            command = self.action_interactive
        )

        # Turn the interactive checkbutton on by default
        self.checkboxInteractive.select()

        # Configure the Help button
        self.buttonHelp.configure(
            command = self.create_help_window
        )

        # Configure the About button
        self.buttonAbout.configure(
            command = self.create_about_window
        )


        #====================
		# Geometry Management
        #====================
        self.labelObjSel.grid(
            in_    = self,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "n"
        )
        self.labelSearch.grid(
            in_    = self,
            column = 2,
            row    = 1,
            columnspan = 2,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "n"
        )
        self.lboxObjSel.grid(
            in_    = self,
            column = 1,
            row    = 2,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 5,
            sticky = "news"
        )
        self.entry.grid(
            in_    = self,
            column = 2,
            row    = 2,
            columnspan = 2,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "new"
        )
        self.buttonSearch.grid(
            in_    = self,
            column = 4,
            row    = 2,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        self.labelStatus.grid(
            in_    = self,
            column = 2,
            row    = 4,
            columnspan = 2,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "n"
        )
        self.buttonClear.grid(
            in_    = self,
            column = 4,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        self.labelStatusDisplay.grid(
            in_    = self,
            column = 2,
            row    = 5,
            columnspan = 2,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 2,
            sticky = "news"
        )
        self.checkboxSearchAll.grid(
            in_    = self,
            column = 2,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        self.checkboxInteractive.grid(
            in_    = self,
            column = 3,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        self.buttonHelp.grid(
            in_    = self,
            column = 4,
            row    = 5,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        self.buttonAbout.grid(
            in_    = self,
            column = 4,
            row    = 6,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )

        #================
        # Resize Behavior
        #================
        self.grid_rowconfigure(1, minsize = 5, pad = 3)
        self.grid_rowconfigure(2, minsize = 11, pad = 3)
        self.grid_rowconfigure(3, minsize = 17, pad = 3)
        self.grid_rowconfigure(4, minsize = 6, pad = 3)
        self.grid_rowconfigure(5, minsize = 11, pad = 3)
        self.grid_rowconfigure(6, weight = 1, minsize = 40, pad = 3)
        self.grid_columnconfigure(1, minsize = 110, pad = 3)
        self.grid_columnconfigure(2, minsize = 30, pad = 3)
        self.grid_columnconfigure(3, minsize = 54, pad = 3)
        self.grid_columnconfigure(4, minsize = 100, pad = 3)



    
    #===========================================================================
    # Function for triggering interactive search from entries into the searchbox
    #===========================================================================
    def search_var_trace(self, *args):
        # Get the search string
        search_var = self.search_var.get()
        # Get the state of the interactive check box
        interactive = self.interactive.get()

        if interactive == 1:
            self.action_searchbutton()
        else:
            pass

    #============================================
    # Function for refreshing the main GUI window
    #============================================
    def refresh(self, *args):

        curr_list = self.pymollist
        curr_selection = self.pymol_selection

        if len(curr_list) != len(cmd.get_names("all")):
            # first, fill the list ob PyMol objects/selections
            self.fill_pymol_list()

        # Find the current selection and select it again
        for i, item in enumerate(self.pymollist):
            if item == curr_selection:
                self.lboxObjSel.selection_set(i)
                break

        # Repeat the again after 1000 msec
        self.after(1000, self.refresh)


    #==========================================================
    # Function for filling the list of PyMol objects/selections
    #==========================================================
    def fill_pymol_list(self, *args):
        # Fill the list with all objets and selections from pymol
        self.pymollist = cmd.get_names("all")

        # delete all entries in the corresponding listbox
        self.lboxObjSel.delete(0, END)

        # and put the items from pymollist into the listbox again
        for item in self.pymollist:
            self.lboxObjSel.insert(END, item)

        # focus on the end of the list
        self.lboxObjSel.see(END)


    #==============================================
    # Function for creating the about window widget
    #==============================================
    def create_about_window(self, *args):
        # Create the widget as an instance of the toplevel GUI window
        about_window = Toplevel(self)
        about_window.wm_title("About")
        # Prevent resizing
        about_window.resizable(0, 0)
        about_window.minsize(width=180, height=180)
        about_window.wm_geometry("")

        # Generate the widgets
        _labelframe_1 = LabelFrame(about_window,
            font = "{MS Sans Serif} 11 bold",
            text = "About",
        )
        _frame_2 = Frame(_labelframe_1,
        )
        _text_version = Label(_frame_2,
            font = "{MS Sans Serif} 10",
            text = "CTRL-F v1.0",
            wraplength = 200,
        )
        _text_license = Label(_labelframe_1,
            text = "Copyright 2017 Max Plach",
            wraplength = 200,
        )
        _text_contact = Label(_labelframe_1,
            cursor = "hand2",
            font = "{MS Sans Serif} 8 underline",
            foreground = "#0000ff",
            text = "Contact",
            wraplength = 200,
        )
        _button_quit = Button(_labelframe_1,
            text = "Back",
            width = 15,
        )
        _label_1 = Label(_labelframe_1,
            cursor = "hand2",
            font = "{MS Sans Serif} 8 underline",
            foreground = "#0000ff",
            text = "2-Clause BSD License",
        )

        # widget commands

        _button_quit.configure(
            command = about_window.destroy
        )

        _label_1.bind("<Button-1>", lambda e, url="https://opensource.org/licenses/BSD-2-Clause":self.open_url_lambda(url))

        _text_contact.bind("<Button-1>", lambda e, url="http://www.uni-regensburg.de/biologie-vorklinische-medizin/biochemie-2/merkl/index.html":self.open_url_lambda(url))


        # Geometry Management
        _labelframe_1.grid(
            in_    = about_window,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = "news"
        )
        _frame_2.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _text_version.grid(
            in_    = _frame_2,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = ""
        )
        _text_license.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 2,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = ""
        )
        _text_contact.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 4,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = ""
        )
        _button_quit.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 5,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = ""
        )
        _label_1.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 3,
            pady = 3,
            rowspan = 1,
            sticky = ""
        )


        # Resize Behavior
        about_window.grid_rowconfigure(1, minsize = 85, pad = 0)
        about_window.grid_columnconfigure(1, minsize = 210, pad = 0)
        _frame_2.grid_rowconfigure(1, minsize = 2, pad = 0)
        _frame_2.grid_columnconfigure(1, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(1, minsize = 9, pad = 0)
        _labelframe_1.grid_rowconfigure(2, minsize = 2, pad = 0)
        _labelframe_1.grid_rowconfigure(3, minsize = 29, pad = 0)
        _labelframe_1.grid_rowconfigure(4, minsize = 2, pad = 0)
        _labelframe_1.grid_rowconfigure(5, minsize = 37, pad = 0)
        _labelframe_1.grid_columnconfigure(1, minsize = 80, pad = 0)



    #===================================
    # Function to create the help window
    #===================================
    def create_help_window(self, *args):
        # Create the window
        help_window = Toplevel(self)
        help_window.wm_title("Quick Help")
        # Prevent resizing
        help_window.resizable(0, 0)
        help_window.minsize(width=300, height=200)
        help_window.wm_geometry("")

        # Generate the widgets
        _labelframe_1 = LabelFrame(help_window,
            font = "{MS Sans Serif} 11 bold",
            text = "Quick Help",
        )
        _frame_1 = Frame(_labelframe_1,
        )
        _frame_2 = Frame(_labelframe_1,
        )
        _frame_3 = Frame(_labelframe_1,
        )
        _frame_4 = Frame(_labelframe_1,
        )
        _frame_5 = Frame(_labelframe_1,
        )
        _frame_6 = Frame(_labelframe_1,
        )
        _frame_7 = Frame(_labelframe_1,
        )
        _frame_8 = Frame(_labelframe_1,
        )
        _frame_9 = Frame(_labelframe_1,
        )
        point2 = Label(_frame_7,
            anchor = "nw",
            justify = "left",
            text = "Second, enter the search string and hit \"Find\". The input is assumed as one letter amino acid code. It is possible to use regular expression as search strings. Returned hits will be saved as PyMol selections named after the object/selection that was searched and the search string.",
            wraplength = 400,
        )
        point3 = Label(_frame_6,
            justify = "left",
            text = "You can also check the box \"search in all\" to search in all available PyMol objects and selections. In this case, the returned hits will be saved as PyMol selections with the prefix \"all\".",
            wraplength = 400,
        )
        point4 = Label(_frame_5,
            justify = "left",
            text = "To search interactively, just check the corresponding box! Note that in this case returned hits are always assigned to the PyMol selection \"interactive\", regardless if the search was limited to a certain PyMol object/selection or if all available objects/selections were searched. The interactive search is turned on by deault.",
            wraplength = 400,
        )
        point5 = Label(_frame_4,
            justify = "left",
            text = "To delete all previously returned hits (and the corresponding PyMol selections and objects) just press \"Clear all hits\". Sometimes the selections in PyMol will only disappear if you return to the main PyMol window.",
            wraplength = 400,
        )
        point6 = Label(_frame_3,
            anchor = "nw",
            compound = "left",
            justify = "left",
            text = "For further help please see the github documentation:",
            wraplength = 400,
        )
        point7 = Label(_frame_2,
            justify = "left",
            font="{MS Sans Serif} 8 underline",
            text = "https://github.com/fumarat/CTRL-F",
            wraplength = 400,
            foreground = "#0000EE",
            cursor="hand2",
        )
        point1 = Label(_frame_8,
            anchor = "nw",
            justify = "left",
            text = "First, select a PyMol object or selection from the list on the left. The active selection will be highlighted in blue and shown in the status display. If there is only one PyMol object available, it will be automatically selected.",
            wraplength = 400,
        )
        buttonQuit = Button(_frame_1,
            text = "Back",
            width = 15,
        )
        _label_14 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )
        _label_15 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )
        _label_16 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )
        _label_17 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )
        _label_18 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )
        _label_7 = Label(_labelframe_1,
            font = "{MS Sans Serif} 10 bold",
            foreground = "#990000",
            text = ">",
        )

        # widget commands
        buttonQuit.configure(
            command = help_window.destroy
        )

        # Open a browser to github when clicking the link
        point7.bind("<Button-1>", self.open_url_text)

        # Geometry Management
        _labelframe_1.grid(
            in_    = help_window,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_1.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 8,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_2.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 7,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_3.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 6,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_4.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 5,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_5.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 4,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_6.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_7.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 2,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_8.grid(
            in_    = _labelframe_1,
            column = 2,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        _frame_9.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "news"
        )
        point2.grid(
            in_    = _frame_7,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point3.grid(
            in_    = _frame_6,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point4.grid(
            in_    = _frame_5,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point5.grid(
            in_    = _frame_4,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point6.grid(
            in_    = _frame_3,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point7.grid(
            in_    = _frame_2,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        point1.grid(
            in_    = _frame_8,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 2,
            pady = 2,
            rowspan = 1,
            sticky = "nw"
        )
        buttonQuit.grid(
            in_    = _frame_1,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = ""
        )
        _label_14.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 2,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )
        _label_15.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 3,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )
        _label_16.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 4,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )
        _label_17.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 5,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )
        _label_18.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 6,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )
        _label_7.grid(
            in_    = _labelframe_1,
            column = 1,
            row    = 1,
            columnspan = 1,
            ipadx = 0,
            ipady = 0,
            padx = 0,
            pady = 0,
            rowspan = 1,
            sticky = "ne"
        )

        # Resize Behavior
        help_window.grid_rowconfigure(1, minsize = 4, pad = 0)
        help_window.grid_columnconfigure(1, minsize = 15, pad = 0)
        _frame_1.grid_rowconfigure(1, minsize = 39, pad = 0)
        _frame_1.grid_columnconfigure(1, minsize = 384, pad = 0)
        _frame_2.grid_rowconfigure(1, minsize = 2, pad = 0)
        _frame_2.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_3.grid_rowconfigure(1, minsize = 23, pad = 0)
        _frame_3.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_4.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_4.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_5.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_5.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_6.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_6.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_7.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_7.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_8.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_8.grid_columnconfigure(1, minsize = 40, pad = 0)
        _frame_9.grid_rowconfigure(1, minsize = 40, pad = 0)
        _frame_9.grid_columnconfigure(1, minsize = 5, pad = 0)
        _labelframe_1.grid_rowconfigure(1, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(2, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(3, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(4, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(5, minsize = 40, pad = 0)
        _labelframe_1.grid_rowconfigure(6, minsize = 11, pad = 0)
        _labelframe_1.grid_rowconfigure(7, minsize = 5, pad = 0)
        _labelframe_1.grid_rowconfigure(8, minsize = 6, pad = 0)
        _labelframe_1.grid_columnconfigure(1, minsize = 34, pad = 0)
        _labelframe_1.grid_columnconfigure(2, minsize = 1, pad = 0)


    #=========================================================
    # Function to open an url from the text of a tkinter label
    #=========================================================
    def open_url_text(self, event):
        webbrowser.open_new(event.widget.cget("text"))

    #===============================================================
    # Function to open an url with a lambda function in the callback
    #===============================================================
    def open_url_lambda(self, url):
        webbrowser.open_new(url)


    #==========================================================
    # Function to add a search to the list of existing searches
    #==========================================================
    def add_list(self, *args):
        search_term = self.search_var.get()

        if not search_term in searchhistory:
            searchhistory.append(search_term)


    #===========================================================================
    # Function for getting a selection of a PyMol object/selection from clicking
    # on an available object/selection in the lboxObjSel listbox
    #===========================================================================
    def get_searchstring(self, *args):
        # THe wait is required for the listbox element to become active
        self.after(100, self.get_string)

    # Helper function for get_searchstring
    def get_string(self, *args):
        self.pymol_selection = self.lboxObjSel.get(ACTIVE)
        self.labelStatusDisplay.configure(text="Selected %s" % self.pymol_selection)





    #=======================================
    # Function for the searchall checkbutton
    #=======================================
    def action_searchall(self, *args):
        # store the value of the searchall checkbox into the variable searchall
        searchall = self.searchall.get()

    #=========================================
    # Function for the interactive checkbutton
    #=========================================
    def action_interactive(self, *args):
        # store the value of the interactive checkbox into the variable interactive
        interactive = self.interactive.get()

    #======================================
    # Function for the actual search action
    #======================================
    def action_searchbutton(self, *args):

        # Get the variables of the searchall and interactive checkboxes
        searchall = self.searchall.get()
        interactive = self.interactive.get()

        # Check if an interactive search should be performed

        # if no, do the normal searches
        if interactive == 0:
            # Check if only in a single object/selection should be searched or in all
            if searchall == 0:
                self.action_searchbutton_single()
            elif searchall == 1:
                self.action_searchbutton_all()

        # if yes, do the interative searches
        if interactive == 1:
            # Check if only in a single object/selection should be searched or in all
            if searchall == 0:
                self.action_searchbutton_single_interactive()
            elif searchall == 1:
                self.action_searchbutton_all_interactive()
 
    #==============================================================
    # Function for a search witha single selection, non-interactive
    #==============================================================
    def action_searchbutton_single(self, *args):
        # Add the current search to the list of previous searches
        self.add_list()

        # Get the search term
        search_term = self.search_var.get()
        
        self.searchstrings = []
        self.searchstrings.append(search_term)

        # Try the following
        # Go to except, e.g. when no selection or object from the pymol list has been selected
        try:
            # Get the single selected object/selection

            # If only one PyMol object is available, automatically select that
            if len(cmd.get_names("objects",1)) == 1:
                search_selection = cmd.get_names("objects",1)[0]
            # if not, let the user choose from the list of objects/selection
            else:
                search_selection = self.pymol_selection

            # Append the selection to a list that is needed for deleting old searches
            self.oldsearches.append("%s_%s" % (search_selection, self.searchstrings[0].upper()))

            # Do the search
            findseq(self.searchstrings[0], search_selection, selName="%s_%s" % (search_selection, self.searchstrings[0].upper()), het=0, firstOnly=0)

            # Display a status message
            self.labelStatusDisplay.configure(text="Search saved as %s_%s" % (search_selection, self.searchstrings[0].upper()))

            # Enable the returned selection
            cmd.enable("%s_%s" % (search_selection, self.searchstrings[0].upper()))

        except:
            # Tell the user something went wrong
            self.labelStatusDisplay.configure(text="Warning, select Object/Selection first!")
        
        # Now try if the selection that has been found is empty, i.e. nothing has been found
        # In this case delete the returned selection immediately
        try:
            # Check if the selection contains amino acids, thus something has been found
            if cmd.count_atoms(self.oldsearches[-1]) == 0:
                self.labelStatusDisplay.configure(text="Nothing found!")
                cmd.delete(self.oldsearches[-1])

        # If the returned selection has something in it (i.e. something has been found), do nothing
        except:
            pass


    #================================================================
    # Function for a search with a single selection, interactive mode
    #================================================================
    def action_searchbutton_single_interactive(self, *args):
        # Get the search term from the entry field (variable self.search_var)
        search_term = self.search_var.get()
        
        # Initialize a list of search terms and append the search term
        self.searchstrings = []
        self.searchstrings.append(search_term)

        # Try the following
        # Go to except, e.g. when no selection or object from the pymol list has been selected
        try:
            # Get the single selected object/selection

            # If only one PyMol object is available, automatically select that
            if len(cmd.get_names("objects",1)) == 1:
                search_selection = cmd.get_names("objects",1)[0]
            # if not, let the user choose from the list of objects/selection
            else:
                search_selection = self.pymol_selection

#                search_selection = self.searchlist[0]

            # Generate an empty pymol selection, called "interactive"
            cmd.select("interactive", "None")

            # Now do the actual find work
            # call the findseq function with the following arguments
            # needle = self.searchstrings[0]
            # haystack = search_selection
            # selName = "interactive" --> gets overwritten after each search
            findseq(self.searchstrings[0], search_selection, selName="interactive", het=0, firstOnly=0)

            # Tell a status
            self.labelStatusDisplay.configure(text="Search saved as \"interactive\"" )

            # Enable the returned selection
            cmd.enable("interactive")


        except:
            # Tell the user to select a pymol object/selection first
            self.labelStatusDisplay.configure(text="Warning, select Object/Selection first!")

        
        # Now try if the selection that has been found is empty, i.e. nothing has been found
        # In this case delete the returned selection immediately
        try:
            # Check if the selection contains amino acids, thus something has been found
            if cmd.count_atoms("interactive") == 0:
                self.labelStatusDisplay.configure(text="Nothing found!")
                cmd.delete("interactive")

        # If the returned selection has something in it (i.e. something has been found), do nothing
        except:
            pass

    #================================================================
    # Function for a search in all objects/selection, non-interactive
    #================================================================
    def action_searchbutton_all(self, *args):
        # Add the current search to the list of previous searches
        self.add_list()

        # Get the search term
        search_term = self.search_var.get()
        
        self.searchstrings = []
        self.searchstrings.append(search_term)

        # Try the following
        # Go to except, e.g. when no selection or object from the pymol list has been selected
        try: 
            
            # Generate a string for combining the intermediary search results into a single selection
            selection_string = ""

            # Itereate through all available pymol objects/selections
            for i, ObjSel in enumerate(self.pymollist):
                search_selection = ObjSel            
                findseq(self.searchstrings[0], search_selection, selName="sele_%i" % i, het=0, firstOnly=0)

                # Append the current returned selection to the selection_string
                selection_string += "sele_%i," % i

            # Remove last comma from selection string
            selection_string = selection_string[:-1]

            # Generate a return selection that is named "all_SEARCHSTRING"
            return_selection = "all_%s" % self.searchstrings[0].upper()
            cmd.select(return_selection, selection_string)

            # Delete the intermediary selections
            for i, ObjSel in enumerate(self.pymollist):
                cmd.delete("sele_%i" % i)

            # Append the returned search to the list of oldsearches
            # Required for cecking if the search is empty or not, see below
            self.oldsearches.append("all_%s" % self.searchstrings[0].upper())

            # Tell a status
            self.labelStatusDisplay.configure(text="Search saved as all_%s" % self.searchstrings[0].upper())

            # Enable the returned selection
            cmd.enable("all_%s" % self.searchstrings[0].upper())


        except:
            self.labelStatusDisplay.configure(text="Warning, select Object/Selection first!")

        
        # Now try if the selection that has been found is empty, i.e. nothing has been found
        # In this case delete the returned selection immediately
        try:
            # Check if the selection contains amino acids, thus something has been found
            if cmd.count_atoms(self.oldsearches[-1]) == 0:
                self.labelStatusDisplay.configure(text="Nothing found!")
                cmd.delete(self.oldsearches[-1])

        # If the returned selection has something in it (i.e. something has been found), do nothing
        except:
            pass


    #=================================================================
    # Function for a search in all objects/selection, interactive mode
    #=================================================================
    def action_searchbutton_all_interactive(self, *args):
        # Get the search term
        search_term = self.search_var.get()
        
        # Initialize a list for search terms and append the search term to it
        self.searchstrings = []
        self.searchstrings.append(search_term)

        # Try the following
        # Go to except, e.g. when no selection or object from the pymol list has been selected
        try: 
            
            # Generate a string for combining the intermediary search results into a single selection
            selection_string = ""

            # Generate an empty pymol selection, called "interactive"
            cmd.select("interactive_all", "None")

            # Iterate through all available pymol objects/selections
            for i, ObjSel in enumerate(self.pymollist):
                # Select the pymol selection/object
                search_selection = ObjSel

                # Now do the actual find work
                # call the findseq function with the following arguments
                # needle = self.searchstrings[0]
                # haystack = search_selection
                # selName = "interactive" --> gets overwritten after each search
                findseq(self.searchstrings[0], search_selection, selName="sele_%i" % i, het=0, firstOnly=0)

                # Append the current returned selection to the selection_string
                selection_string += "sele_%i," % i

            # Remove last comma from selection string
            selection_string = selection_string[:-1]

            # Generate a return selection that is named "all_SEARCHSTRING"
            return_selection = "interactive_all"
            cmd.select(return_selection, selection_string)

            # Delete the intermediary selections
            for i, ObjSel in enumerate(self.pymollist):
                cmd.delete("sele_%i" % i)

            # Append the returned search to the list of oldsearches
            # Required for cecking if the search is empty or not, see below
            # self.oldsearches.append("all_%s" % self.searchstrings[0])

            # Tell a status
            self.labelStatusDisplay.configure(text="Search saved as interactive_all")

            # Enable the returned selection
            cmd.enable("interactive_all")


        except:
            self.labelStatusDisplay.configure(text="Warning, select Object/Selection first!")

        
        # Now try if the selection that has been found is empty, i.e. nothing has been found
        # In this case delete the returned selection immediately
        try:
            # Check if the selection contains amino acids, thus something has been found
            if cmd.count_atoms("interactive") == 0:
                self.labelStatusDisplay.configure(text="Nothing found!")
                cmd.delete("interactive")

        # If the returned selection has something in it (i.e. something has been found), do nothing
        except:
            pass


    #====================================
    # Function for deleting previous hits
    #====================================
    def action_deletebutton(self, *args):
        # delete all old hits from non-interactive searches
        # these hits are stored in the list self.oldsearches
        for item in self.oldsearches:
            cmd.delete(item)

        # delete the hits from interactive searches
        # these are always named "interactive"
        cmd.delete("interactive")
        cmd.delete("interactive_all")

        # Show a status message
        self.labelStatusDisplay.configure(text="Cleared all hits")

        


"""
Functions from findseq by Jason Vertrees, 2009
"""

def findseq(needle, haystack, selName=None, het=0, firstOnly=0):
    # set the name of the selection to return.
    if selName == None:
        rSelName = "foundSeq" + str(random.randint(0, 32000))
        selName = rSelName
    elif selName == "sele":
        rSelName = "sele"
    else:
        rSelName = selName

    # input checking
    if not checkParams(needle, haystack, selName, het, firstOnly):
        #print("There was an error with a parameter.  Please see")
        #print("the above error message for how to fix it.")
        return None

    one_letter = {
        '00C': 'C', '01W': 'X', '0A0': 'D', '0A1': 'Y', '0A2': 'K',
        '0A8': 'C', '0AA': 'V', '0AB': 'V', '0AC': 'G', '0AD': 'G',
        '0AF': 'W', '0AG': 'L', '0AH': 'S', '0AK': 'D', '0AM': 'A',
        '0AP': 'C', '0AU': 'U', '0AV': 'A', '0AZ': 'P', '0BN': 'F',
        '0C ': 'C', '0CS': 'A', '0DC': 'C', '0DG': 'G', '0DT': 'T',
        '0G ': 'G', '0NC': 'A', '0SP': 'A', '0U ': 'U', '0YG': 'YG',
        '10C': 'C', '125': 'U', '126': 'U', '127': 'U', '128': 'N',
        '12A': 'A', '143': 'C', '175': 'ASG', '193': 'X', '1AP': 'A',
        '1MA': 'A', '1MG': 'G', '1PA': 'F', '1PI': 'A', '1PR': 'N',
        '1SC': 'C', '1TQ': 'W', '1TY': 'Y', '200': 'F', '23F': 'F',
        '23S': 'X', '26B': 'T', '2AD': 'X', '2AG': 'G', '2AO': 'X',
        '2AR': 'A', '2AS': 'X', '2AT': 'T', '2AU': 'U', '2BD': 'I',
        '2BT': 'T', '2BU': 'A', '2CO': 'C', '2DA': 'A', '2DF': 'N',
        '2DM': 'N', '2DO': 'X', '2DT': 'T', '2EG': 'G', '2FE': 'N',
        '2FI': 'N', '2FM': 'M', '2GT': 'T', '2HF': 'H', '2LU': 'L',
        '2MA': 'A', '2MG': 'G', '2ML': 'L', '2MR': 'R', '2MT': 'P',
        '2MU': 'U', '2NT': 'T', '2OM': 'U', '2OT': 'T', '2PI': 'X',
        '2PR': 'G', '2SA': 'N', '2SI': 'X', '2ST': 'T', '2TL': 'T',
        '2TY': 'Y', '2VA': 'V', '32S': 'X', '32T': 'X', '3AH': 'H',
        '3AR': 'X', '3CF': 'F', '3DA': 'A', '3DR': 'N', '3GA': 'A',
        '3MD': 'D', '3ME': 'U', '3NF': 'Y', '3TY': 'X', '3XH': 'G',
        '4AC': 'N', '4BF': 'Y', '4CF': 'F', '4CY': 'M', '4DP': 'W',
        '4F3': 'GYG', '4FB': 'P', '4FW': 'W', '4HT': 'W', '4IN': 'X',
        '4MF': 'N', '4MM': 'X', '4OC': 'C', '4PC': 'C', '4PD': 'C',
        '4PE': 'C', '4PH': 'F', '4SC': 'C', '4SU': 'U', '4TA': 'N',
        '5AA': 'A', '5AT': 'T', '5BU': 'U', '5CG': 'G', '5CM': 'C',
        '5CS': 'C', '5FA': 'A', '5FC': 'C', '5FU': 'U', '5HP': 'E',
        '5HT': 'T', '5HU': 'U', '5IC': 'C', '5IT': 'T', '5IU': 'U',
        '5MC': 'C', '5MD': 'N', '5MU': 'U', '5NC': 'C', '5PC': 'C',
        '5PY': 'T', '5SE': 'U', '5ZA': 'TWG', '64T': 'T', '6CL': 'K',
        '6CT': 'T', '6CW': 'W', '6HA': 'A', '6HC': 'C', '6HG': 'G',
        '6HN': 'K', '6HT': 'T', '6IA': 'A', '6MA': 'A', '6MC': 'A',
        '6MI': 'N', '6MT': 'A', '6MZ': 'N', '6OG': 'G', '70U': 'U',
        '7DA': 'A', '7GU': 'G', '7JA': 'I', '7MG': 'G', '8AN': 'A',
        '8FG': 'G', '8MG': 'G', '8OG': 'G', '9NE': 'E', '9NF': 'F',
        '9NR': 'R', '9NV': 'V', 'A  ': 'A', 'A1P': 'N', 'A23': 'A',
        'A2L': 'A', 'A2M': 'A', 'A34': 'A', 'A35': 'A', 'A38': 'A',
        'A39': 'A', 'A3A': 'A', 'A3P': 'A', 'A40': 'A', 'A43': 'A',
        'A44': 'A', 'A47': 'A', 'A5L': 'A', 'A5M': 'C', 'A5O': 'A',
        'A66': 'X', 'AA3': 'A', 'AA4': 'A', 'AAR': 'R', 'AB7': 'X',
        'ABA': 'A', 'ABR': 'A', 'ABS': 'A', 'ABT': 'N', 'ACB': 'D',
        'ACL': 'R', 'AD2': 'A', 'ADD': 'X', 'ADX': 'N', 'AEA': 'X',
        'AEI': 'D', 'AET': 'A', 'AFA': 'N', 'AFF': 'N', 'AFG': 'G',
        'AGM': 'R', 'AGT': 'X', 'AHB': 'N', 'AHH': 'X', 'AHO': 'A',
        'AHP': 'A', 'AHS': 'X', 'AHT': 'X', 'AIB': 'A', 'AKL': 'D',
        'ALA': 'A', 'ALC': 'A', 'ALG': 'R', 'ALM': 'A', 'ALN': 'A',
        'ALO': 'T', 'ALQ': 'X', 'ALS': 'A', 'ALT': 'A', 'ALY': 'K',
        'AP7': 'A', 'APE': 'X', 'APH': 'A', 'API': 'K', 'APK': 'K',
        'APM': 'X', 'APP': 'X', 'AR2': 'R', 'AR4': 'E', 'ARG': 'R',
        'ARM': 'R', 'ARO': 'R', 'ARV': 'X', 'AS ': 'A', 'AS2': 'D',
        'AS9': 'X', 'ASA': 'D', 'ASB': 'D', 'ASI': 'D', 'ASK': 'D',
        'ASL': 'D', 'ASM': 'X', 'ASN': 'N', 'ASP': 'D', 'ASQ': 'D',
        'ASU': 'N', 'ASX': 'B', 'ATD': 'T', 'ATL': 'T', 'ATM': 'T',
        'AVC': 'A', 'AVN': 'X', 'AYA': 'A', 'AYG': 'AYG', 'AZK': 'K',
        'AZS': 'S', 'AZY': 'Y', 'B1F': 'F', 'B1P': 'N', 'B2A': 'A',
        'B2F': 'F', 'B2I': 'I', 'B2V': 'V', 'B3A': 'A', 'B3D': 'D',
        'B3E': 'E', 'B3K': 'K', 'B3L': 'X', 'B3M': 'X', 'B3Q': 'X',
        'B3S': 'S', 'B3T': 'X', 'B3U': 'H', 'B3X': 'N', 'B3Y': 'Y',
        'BB6': 'C', 'BB7': 'C', 'BB9': 'C', 'BBC': 'C', 'BCS': 'C',
        'BCX': 'C', 'BE2': 'X', 'BFD': 'D', 'BG1': 'S', 'BGM': 'G',
        'BHD': 'D', 'BIF': 'F', 'BIL': 'X', 'BIU': 'I', 'BJH': 'X',
        'BLE': 'L', 'BLY': 'K', 'BMP': 'N', 'BMT': 'T', 'BNN': 'A',
        'BNO': 'X', 'BOE': 'T', 'BOR': 'R', 'BPE': 'C', 'BRU': 'U',
        'BSE': 'S', 'BT5': 'N', 'BTA': 'L', 'BTC': 'C', 'BTR': 'W',
        'BUC': 'C', 'BUG': 'V', 'BVP': 'U', 'BZG': 'N', 'C  ': 'C',
        'C12': 'TYG', 'C1X': 'K', 'C25': 'C', 'C2L': 'C', 'C2S': 'C',
        'C31': 'C', 'C32': 'C', 'C34': 'C', 'C36': 'C', 'C37': 'C',
        'C38': 'C', 'C3Y': 'C', 'C42': 'C', 'C43': 'C', 'C45': 'C',
        'C46': 'C', 'C49': 'C', 'C4R': 'C', 'C4S': 'C', 'C5C': 'C',
        'C66': 'X', 'C6C': 'C', 'C99': 'TFG', 'CAF': 'C', 'CAL': 'X',
        'CAR': 'C', 'CAS': 'C', 'CAV': 'X', 'CAY': 'C', 'CB2': 'C',
        'CBR': 'C', 'CBV': 'C', 'CCC': 'C', 'CCL': 'K', 'CCS': 'C',
        'CCY': 'CYG', 'CDE': 'X', 'CDV': 'X', 'CDW': 'C', 'CEA': 'C',
        'CFL': 'C', 'CFY': 'FCYG', 'CG1': 'G', 'CGA': 'E', 'CGU': 'E',
        'CH ': 'C', 'CH6': 'MYG', 'CH7': 'KYG', 'CHF': 'X', 'CHG': 'X',
        'CHP': 'G', 'CHS': 'X', 'CIR': 'R', 'CJO': 'GYG', 'CLE': 'L',
        'CLG': 'K', 'CLH': 'K', 'CLV': 'AFG', 'CM0': 'N', 'CME': 'C',
        'CMH': 'C', 'CML': 'C', 'CMR': 'C', 'CMT': 'C', 'CNU': 'U',
        'CP1': 'C', 'CPC': 'X', 'CPI': 'X', 'CQR': 'GYG', 'CR0': 'TLG',
        'CR2': 'GYG', 'CR5': 'G', 'CR7': 'KYG', 'CR8': 'HYG', 'CRF': 'TWG',
        'CRG': 'THG', 'CRK': 'MYG', 'CRO': 'GYG', 'CRQ': 'QYG', 'CRU': 'E',
        'CRW': 'ASG', 'CRX': 'ASG', 'CS0': 'C', 'CS1': 'C', 'CS3': 'C',
        'CS4': 'C', 'CS8': 'N', 'CSA': 'C', 'CSB': 'C', 'CSD': 'C',
        'CSE': 'C', 'CSF': 'C', 'CSH': 'SHG', 'CSI': 'G', 'CSJ': 'C',
        'CSL': 'C', 'CSO': 'C', 'CSP': 'C', 'CSR': 'C', 'CSS': 'C',
        'CSU': 'C', 'CSW': 'C', 'CSX': 'C', 'CSY': 'SYG', 'CSZ': 'C',
        'CTE': 'W', 'CTG': 'T', 'CTH': 'T', 'CUC': 'X', 'CWR': 'S',
        'CXM': 'M', 'CY0': 'C', 'CY1': 'C', 'CY3': 'C', 'CY4': 'C',
        'CYA': 'C', 'CYD': 'C', 'CYF': 'C', 'CYG': 'C', 'CYJ': 'X',
        'CYM': 'C', 'CYQ': 'C', 'CYR': 'C', 'CYS': 'C', 'CZ2': 'C',
        'CZO': 'GYG', 'CZZ': 'C', 'D11': 'T', 'D1P': 'N', 'D3 ': 'N',
        'D33': 'N', 'D3P': 'G', 'D3T': 'T', 'D4M': 'T', 'D4P': 'X',
        'DA ': 'A', 'DA2': 'X', 'DAB': 'A', 'DAH': 'F', 'DAL': 'A',
        'DAR': 'R', 'DAS': 'D', 'DBB': 'T', 'DBM': 'N', 'DBS': 'S',
        'DBU': 'T', 'DBY': 'Y', 'DBZ': 'A', 'DC ': 'C', 'DC2': 'C',
        'DCG': 'G', 'DCI': 'X', 'DCL': 'X', 'DCT': 'C', 'DCY': 'C',
        'DDE': 'H', 'DDG': 'G', 'DDN': 'U', 'DDX': 'N', 'DFC': 'C',
        'DFG': 'G', 'DFI': 'X', 'DFO': 'X', 'DFT': 'N', 'DG ': 'G',
        'DGH': 'G', 'DGI': 'G', 'DGL': 'E', 'DGN': 'Q', 'DHA': 'A',
        'DHI': 'H', 'DHL': 'X', 'DHN': 'V', 'DHP': 'X', 'DHU': 'U',
        'DHV': 'V', 'DI ': 'I', 'DIL': 'I', 'DIR': 'R', 'DIV': 'V',
        'DLE': 'L', 'DLS': 'K', 'DLY': 'K', 'DM0': 'K', 'DMH': 'N',
        'DMK': 'D', 'DMT': 'X', 'DN ': 'N', 'DNE': 'L', 'DNG': 'L',
        'DNL': 'K', 'DNM': 'L', 'DNP': 'A', 'DNR': 'C', 'DNS': 'K',
        'DOA': 'X', 'DOC': 'C', 'DOH': 'D', 'DON': 'L', 'DPB': 'T',
        'DPH': 'F', 'DPL': 'P', 'DPP': 'A', 'DPQ': 'Y', 'DPR': 'P',
        'DPY': 'N', 'DRM': 'U', 'DRP': 'N', 'DRT': 'T', 'DRZ': 'N',
        'DSE': 'S', 'DSG': 'N', 'DSN': 'S', 'DSP': 'D', 'DT ': 'T',
        'DTH': 'T', 'DTR': 'W', 'DTY': 'Y', 'DU ': 'U', 'DVA': 'V',
        'DXD': 'N', 'DXN': 'N', 'DYG': 'DYG', 'DYS': 'C', 'DZM': 'A',
        'E  ': 'A', 'E1X': 'A', 'EDA': 'A', 'EDC': 'G', 'EFC': 'C',
        'EHP': 'F', 'EIT': 'T', 'ENP': 'N', 'ESB': 'Y', 'ESC': 'M',
        'EXY': 'L', 'EY5': 'N', 'EYS': 'X', 'F2F': 'F', 'FA2': 'A',
        'FA5': 'N', 'FAG': 'N', 'FAI': 'N', 'FCL': 'F', 'FFD': 'N',
        'FGL': 'G', 'FGP': 'S', 'FHL': 'X', 'FHO': 'K', 'FHU': 'U',
        'FLA': 'A', 'FLE': 'L', 'FLT': 'Y', 'FME': 'M', 'FMG': 'G',
        'FMU': 'N', 'FOE': 'C', 'FOX': 'G', 'FP9': 'P', 'FPA': 'F',
        'FRD': 'X', 'FT6': 'W', 'FTR': 'W', 'FTY': 'Y', 'FZN': 'K',
        'G  ': 'G', 'G25': 'G', 'G2L': 'G', 'G2S': 'G', 'G31': 'G',
        'G32': 'G', 'G33': 'G', 'G36': 'G', 'G38': 'G', 'G42': 'G',
        'G46': 'G', 'G47': 'G', 'G48': 'G', 'G49': 'G', 'G4P': 'N',
        'G7M': 'G', 'GAO': 'G', 'GAU': 'E', 'GCK': 'C', 'GCM': 'X',
        'GDP': 'G', 'GDR': 'G', 'GFL': 'G', 'GGL': 'E', 'GH3': 'G',
        'GHG': 'Q', 'GHP': 'G', 'GL3': 'G', 'GLH': 'Q', 'GLM': 'X',
        'GLN': 'Q', 'GLQ': 'E', 'GLU': 'E', 'GLX': 'Z', 'GLY': 'G',
        'GLZ': 'G', 'GMA': 'E', 'GMS': 'G', 'GMU': 'U', 'GN7': 'G',
        'GND': 'X', 'GNE': 'N', 'GOM': 'G', 'GPL': 'K', 'GS ': 'G',
        'GSC': 'G', 'GSR': 'G', 'GSS': 'G', 'GSU': 'E', 'GT9': 'C',
        'GTP': 'G', 'GVL': 'X', 'GYC': 'CYG', 'GYS': 'SYG', 'H2U': 'U',
        'H5M': 'P', 'HAC': 'A', 'HAR': 'R', 'HBN': 'H', 'HCS': 'X',
        'HDP': 'U', 'HEU': 'U', 'HFA': 'X', 'HGL': 'X', 'HHI': 'H',
        'HHK': 'AK', 'HIA': 'H', 'HIC': 'H', 'HIP': 'H', 'HIQ': 'H',
        'HIS': 'H', 'HL2': 'L', 'HLU': 'L', 'HMF': 'A', 'HMR': 'R',
        'HOL': 'N', 'HPC': 'F', 'HPE': 'F', 'HPQ': 'F', 'HQA': 'A',
        'HRG': 'R', 'HRP': 'W', 'HS8': 'H', 'HS9': 'H', 'HSE': 'S',
        'HSL': 'S', 'HSO': 'H', 'HTI': 'C', 'HTN': 'N', 'HTR': 'W',
        'HV5': 'A', 'HVA': 'V', 'HY3': 'P', 'HYP': 'P', 'HZP': 'P',
        'I  ': 'I', 'I2M': 'I', 'I58': 'K', 'I5C': 'C', 'IAM': 'A',
        'IAR': 'R', 'IAS': 'D', 'IC ': 'C', 'IEL': 'K', 'IEY': 'HYG',
        'IG ': 'G', 'IGL': 'G', 'IGU': 'G', 'IIC': 'SHG', 'IIL': 'I',
        'ILE': 'I', 'ILG': 'E', 'ILX': 'I', 'IMC': 'C', 'IML': 'I',
        'IOY': 'F', 'IPG': 'G', 'IPN': 'N', 'IRN': 'N', 'IT1': 'K',
        'IU ': 'U', 'IYR': 'Y', 'IYT': 'T', 'JJJ': 'C', 'JJK': 'C',
        'JJL': 'C', 'JW5': 'N', 'K1R': 'C', 'KAG': 'G', 'KCX': 'K',
        'KGC': 'K', 'KOR': 'M', 'KPI': 'K', 'KST': 'K', 'KYQ': 'K',
        'L2A': 'X', 'LA2': 'K', 'LAA': 'D', 'LAL': 'A', 'LBY': 'K',
        'LC ': 'C', 'LCA': 'A', 'LCC': 'N', 'LCG': 'G', 'LCH': 'N',
        'LCK': 'K', 'LCX': 'K', 'LDH': 'K', 'LED': 'L', 'LEF': 'L',
        'LEH': 'L', 'LEI': 'V', 'LEM': 'L', 'LEN': 'L', 'LET': 'X',
        'LEU': 'L', 'LG ': 'G', 'LGP': 'G', 'LHC': 'X', 'LHU': 'U',
        'LKC': 'N', 'LLP': 'K', 'LLY': 'K', 'LME': 'E', 'LMQ': 'Q',
        'LMS': 'N', 'LP6': 'K', 'LPD': 'P', 'LPG': 'G', 'LPL': 'X',
        'LPS': 'S', 'LSO': 'X', 'LTA': 'X', 'LTR': 'W', 'LVG': 'G',
        'LVN': 'V', 'LYM': 'K', 'LYN': 'K', 'LYR': 'K', 'LYS': 'K',
        'LYX': 'K', 'LYZ': 'K', 'M0H': 'C', 'M1G': 'G', 'M2G': 'G',
        'M2L': 'K', 'M2S': 'M', 'M3L': 'K', 'M5M': 'C', 'MA ': 'A',
        'MA6': 'A', 'MA7': 'A', 'MAA': 'A', 'MAD': 'A', 'MAI': 'R',
        'MBQ': 'Y', 'MBZ': 'N', 'MC1': 'S', 'MCG': 'X', 'MCL': 'K',
        'MCS': 'C', 'MCY': 'C', 'MDH': 'X', 'MDO': 'ASG', 'MDR': 'N',
        'MEA': 'F', 'MED': 'M', 'MEG': 'E', 'MEN': 'N', 'MEP': 'U',
        'MEQ': 'Q', 'MET': 'M', 'MEU': 'G', 'MF3': 'X', 'MFC': 'GYG',
        'MG1': 'G', 'MGG': 'R', 'MGN': 'Q', 'MGQ': 'A', 'MGV': 'G',
        'MGY': 'G', 'MHL': 'L', 'MHO': 'M', 'MHS': 'H', 'MIA': 'A',
        'MIS': 'S', 'MK8': 'L', 'ML3': 'K', 'MLE': 'L', 'MLL': 'L',
        'MLY': 'K', 'MLZ': 'K', 'MME': 'M', 'MMT': 'T', 'MND': 'N',
        'MNL': 'L', 'MNU': 'U', 'MNV': 'V', 'MOD': 'X', 'MP8': 'P',
        'MPH': 'X', 'MPJ': 'X', 'MPQ': 'G', 'MRG': 'G', 'MSA': 'G',
        'MSE': 'M', 'MSL': 'M', 'MSO': 'M', 'MSP': 'X', 'MT2': 'M',
        'MTR': 'T', 'MTU': 'A', 'MTY': 'Y', 'MVA': 'V', 'N  ': 'N',
        'N10': 'S', 'N2C': 'X', 'N5I': 'N', 'N5M': 'C', 'N6G': 'G',
        'N7P': 'P', 'NA8': 'A', 'NAL': 'A', 'NAM': 'A', 'NB8': 'N',
        'NBQ': 'Y', 'NC1': 'S', 'NCB': 'A', 'NCX': 'N', 'NCY': 'X',
        'NDF': 'F', 'NDN': 'U', 'NEM': 'H', 'NEP': 'H', 'NF2': 'N',
        'NFA': 'F', 'NHL': 'E', 'NIT': 'X', 'NIY': 'Y', 'NLE': 'L',
        'NLN': 'L', 'NLO': 'L', 'NLP': 'L', 'NLQ': 'Q', 'NMC': 'G',
        'NMM': 'R', 'NMS': 'T', 'NMT': 'T', 'NNH': 'R', 'NP3': 'N',
        'NPH': 'C', 'NRP': 'LYG', 'NRQ': 'MYG', 'NSK': 'X', 'NTY': 'Y',
        'NVA': 'V', 'NYC': 'TWG', 'NYG': 'NYG', 'NYM': 'N', 'NYS': 'C',
        'NZH': 'H', 'O12': 'X', 'O2C': 'N', 'O2G': 'G', 'OAD': 'N',
        'OAS': 'S', 'OBF': 'X', 'OBS': 'X', 'OCS': 'C', 'OCY': 'C',
        'ODP': 'N', 'OHI': 'H', 'OHS': 'D', 'OIC': 'X', 'OIP': 'I',
        'OLE': 'X', 'OLT': 'T', 'OLZ': 'S', 'OMC': 'C', 'OMG': 'G',
        'OMT': 'M', 'OMU': 'U', 'ONE': 'U', 'ONL': 'X', 'OPR': 'R',
        'ORN': 'A', 'ORQ': 'R', 'OSE': 'S', 'OTB': 'X', 'OTH': 'T',
        'OTY': 'Y', 'OXX': 'D', 'P  ': 'G', 'P1L': 'C', 'P1P': 'N',
        'P2T': 'T', 'P2U': 'U', 'P2Y': 'P', 'P5P': 'A', 'PAQ': 'Y',
        'PAS': 'D', 'PAT': 'W', 'PAU': 'A', 'PBB': 'C', 'PBF': 'F',
        'PBT': 'N', 'PCA': 'E', 'PCC': 'P', 'PCE': 'X', 'PCS': 'F',
        'PDL': 'X', 'PDU': 'U', 'PEC': 'C', 'PF5': 'F', 'PFF': 'F',
        'PFX': 'X', 'PG1': 'S', 'PG7': 'G', 'PG9': 'G', 'PGL': 'X',
        'PGN': 'G', 'PGP': 'G', 'PGY': 'G', 'PHA': 'F', 'PHD': 'D',
        'PHE': 'F', 'PHI': 'F', 'PHL': 'F', 'PHM': 'F', 'PIV': 'X',
        'PLE': 'L', 'PM3': 'F', 'PMT': 'C', 'POM': 'P', 'PPN': 'F',
        'PPU': 'A', 'PPW': 'G', 'PQ1': 'N', 'PR3': 'C', 'PR5': 'A',
        'PR9': 'P', 'PRN': 'A', 'PRO': 'P', 'PRS': 'P', 'PSA': 'F',
        'PSH': 'H', 'PST': 'T', 'PSU': 'U', 'PSW': 'C', 'PTA': 'X',
        'PTH': 'Y', 'PTM': 'Y', 'PTR': 'Y', 'PU ': 'A', 'PUY': 'N',
        'PVH': 'H', 'PVL': 'X', 'PYA': 'A', 'PYO': 'U', 'PYX': 'C',
        'PYY': 'N', 'QLG': 'QLG', 'QUO': 'G', 'R  ': 'A', 'R1A': 'C',
        'R1B': 'C', 'R1F': 'C', 'R7A': 'C', 'RC7': 'HYG', 'RCY': 'C',
        'RIA': 'A', 'RMP': 'A', 'RON': 'X', 'RT ': 'T', 'RTP': 'N',
        'S1H': 'S', 'S2C': 'C', 'S2D': 'A', 'S2M': 'T', 'S2P': 'A',
        'S4A': 'A', 'S4C': 'C', 'S4G': 'G', 'S4U': 'U', 'S6G': 'G',
        'SAC': 'S', 'SAH': 'C', 'SAR': 'G', 'SBL': 'S', 'SC ': 'C',
        'SCH': 'C', 'SCS': 'C', 'SCY': 'C', 'SD2': 'X', 'SDG': 'G',
        'SDP': 'S', 'SEB': 'S', 'SEC': 'A', 'SEG': 'A', 'SEL': 'S',
        'SEM': 'X', 'SEN': 'S', 'SEP': 'S', 'SER': 'S', 'SET': 'S',
        'SGB': 'S', 'SHC': 'C', 'SHP': 'G', 'SHR': 'K', 'SIB': 'C',
        'SIC': 'DC', 'SLA': 'P', 'SLR': 'P', 'SLZ': 'K', 'SMC': 'C',
        'SME': 'M', 'SMF': 'F', 'SMP': 'A', 'SMT': 'T', 'SNC': 'C',
        'SNN': 'N', 'SOC': 'C', 'SOS': 'N', 'SOY': 'S', 'SPT': 'T',
        'SRA': 'A', 'SSU': 'U', 'STY': 'Y', 'SUB': 'X', 'SUI': 'DG',
        'SUN': 'S', 'SUR': 'U', 'SVA': 'S', 'SVX': 'S', 'SVZ': 'X',
        'SYS': 'C', 'T  ': 'T', 'T11': 'F', 'T23': 'T', 'T2S': 'T',
        'T2T': 'N', 'T31': 'U', 'T32': 'T', 'T36': 'T', 'T37': 'T',
        'T38': 'T', 'T39': 'T', 'T3P': 'T', 'T41': 'T', 'T48': 'T',
        'T49': 'T', 'T4S': 'T', 'T5O': 'U', 'T5S': 'T', 'T66': 'X',
        'T6A': 'A', 'TA3': 'T', 'TA4': 'X', 'TAF': 'T', 'TAL': 'N',
        'TAV': 'D', 'TBG': 'V', 'TBM': 'T', 'TC1': 'C', 'TCP': 'T',
        'TCQ': 'X', 'TCR': 'W', 'TCY': 'A', 'TDD': 'L', 'TDY': 'T',
        'TFE': 'T', 'TFO': 'A', 'TFQ': 'F', 'TFT': 'T', 'TGP': 'G',
        'TH6': 'T', 'THC': 'T', 'THO': 'X', 'THR': 'T', 'THX': 'N',
        'THZ': 'R', 'TIH': 'A', 'TLB': 'N', 'TLC': 'T', 'TLN': 'U',
        'TMB': 'T', 'TMD': 'T', 'TNB': 'C', 'TNR': 'S', 'TOX': 'W',
        'TP1': 'T', 'TPC': 'C', 'TPG': 'G', 'TPH': 'X', 'TPL': 'W',
        'TPO': 'T', 'TPQ': 'Y', 'TQQ': 'W', 'TRF': 'W', 'TRG': 'K',
        'TRN': 'W', 'TRO': 'W', 'TRP': 'W', 'TRQ': 'W', 'TRW': 'W',
        'TRX': 'W', 'TS ': 'N', 'TST': 'X', 'TT ': 'N', 'TTD': 'T',
        'TTI': 'U', 'TTM': 'T', 'TTQ': 'W', 'TTS': 'Y', 'TY2': 'Y',
        'TY3': 'Y', 'TYB': 'Y', 'TYI': 'Y', 'TYN': 'Y', 'TYO': 'Y',
        'TYQ': 'Y', 'TYR': 'Y', 'TYS': 'Y', 'TYT': 'Y', 'TYU': 'N',
        'TYX': 'X', 'TYY': 'Y', 'TZB': 'X', 'TZO': 'X', 'U  ': 'U',
        'U25': 'U', 'U2L': 'U', 'U2N': 'U', 'U2P': 'U', 'U31': 'U',
        'U33': 'U', 'U34': 'U', 'U36': 'U', 'U37': 'U', 'U8U': 'U',
        'UAR': 'U', 'UCL': 'U', 'UD5': 'U', 'UDP': 'N', 'UFP': 'N',
        'UFR': 'U', 'UFT': 'U', 'UMA': 'A', 'UMP': 'U', 'UMS': 'U',
        'UN1': 'X', 'UN2': 'X', 'UNK': 'X', 'UR3': 'U', 'URD': 'U',
        'US1': 'U', 'US2': 'U', 'US3': 'T', 'US5': 'U', 'USM': 'U',
        'V1A': 'C', 'VAD': 'V', 'VAF': 'V', 'VAL': 'V', 'VB1': 'K',
        'VDL': 'X', 'VLL': 'X', 'VLM': 'X', 'VMS': 'X', 'VOL': 'X',
        'X  ': 'G', 'X2W': 'E', 'X4A': 'N', 'X9Q': 'AFG', 'XAD': 'A',
        'XAE': 'N', 'XAL': 'A', 'XAR': 'N', 'XCL': 'C', 'XCP': 'X',
        'XCR': 'C', 'XCS': 'N', 'XCT': 'C', 'XCY': 'C', 'XGA': 'N',
        'XGL': 'G', 'XGR': 'G', 'XGU': 'G', 'XTH': 'T', 'XTL': 'T',
        'XTR': 'T', 'XTS': 'G', 'XTY': 'N', 'XUA': 'A', 'XUG': 'G',
        'XX1': 'K', 'XXY': 'THG', 'XYG': 'DYG', 'Y  ': 'A', 'YCM': 'C',
        'YG ': 'G', 'YOF': 'Y', 'YRR': 'N', 'YYG': 'G', 'Z  ': 'C',
        'ZAD': 'A', 'ZAL': 'A', 'ZBC': 'C', 'ZCY': 'C', 'ZDU': 'U',
        'ZFB': 'X', 'ZGU': 'G', 'ZHP': 'N', 'ZTH': 'T', 'ZZJ': 'A'}

    # remove hetero atoms (waters/ligands/etc) from consideration?
    if het:
        cmd.select("__h", "br. " + haystack)
    else:
        cmd.select("__h", "br. " + haystack + " and not het")

    # get the AAs in the haystack
    aaDict = {'aaList': []}
    cmd.iterate("(name ca) and __h", "aaList.append((resi,resn,chain))", space=aaDict)

    IDs = [int(x[0]) for x in aaDict['aaList']]
    AAs = ''.join([one_letter[x[1]] for x in aaDict['aaList']])
    chains = [x[2] for x in aaDict['aaList']]

    reNeedle = re.compile(needle.upper())
    it = reNeedle.finditer(AAs)

    # make an empty selection to which we add residues
    cmd.select(rSelName, 'None')

    for i in it:
        (start, stop) = i.span()
        # we found some residues, which chains are they from?
        i_chains = chains[start:stop]
        # are all residues from one chain?
        if len(set(i_chains)) != 1:
        	# now they are not, this match is not really a match, skip it
        	continue
        chain = i_chains[0]
        cmd.select(rSelName, rSelName + " or (__h and i. " + str(IDs[start]) + "-" + str(IDs[stop - 1]) + " and c. " + chain + " )")
        if int(firstOnly):
            break
    cmd.delete("__h")
    return rSelName

#cmd.extend("findseq", findseq)


def checkParams(needle, haystack, selName, het, firstOnly):
    """
    This is just a helper function for checking the user input
    """
    # check Needle
    #if len(needle) == 0 or not cmd.is_string(needle):
    #    print("Error: Please provide a string 'needle' to search for.")
    #    print("Error: For help type 'help motifFinder'.")
    #    return False

    # check Haystack
    if len(haystack) == 0 or not cmd.is_string(haystack):
        print("Error: Please provide valid PyMOL object or selection name")
        print("Error: in which to search.")
        print("Error: For help type 'help motifFinder'.")
        return False

    # check het
    try:
        het = bool(int(het))
    except ValueError:
        print("Error: The 'het' parameter was not 0 or 1.")
        return False

    # check first Only
    try:
        firstOnly = bool(int(het))
    except ValueError:
        print("Error: The 'firstOnly' parameter was not 0 or 1.")
        return False

    # check selName
    if not cmd.is_string(selName):
        print("Error: selName was not a string.")
        return False
    return True

"""
End of functions from findseq
"""



#=================================
# Configure the PyMol plugin
#=================================

# Initialize an empty search history
searchhistory = []


#======================
# Initialize the plugin
#======================
def __init__(self):

    # Set a global variable for tracing if the user pressed the STRG-F key combo for starting the plugin
    # and initialize it with 0
    # The open_var is necessary to track if already a top window is open
    global trace_var
    global open_var
    trace_var = 0
    open_var = 0

    # Register the plugin under the plugin menu and make an entry "CTRL-F"
    self.menuBar.addmenuitem("Plugin", "command", "CTRL-F", label="CTRL-F", command = lambda s=self : showWindow(s))

    # Make a key binding that can be used from within the PyMol PMG app window
    root = plugins.get_tk_root()
    root.bind("<Control-f>", lambda s=self : toggler(s))

    # Make a key bining that can be used from withtin the PyMol viewer
    # this makes a callback to toggler, which toggles the trace_var
    cmd.set_key("CTRL-F", lambda s=self : toggler(s))
    # Do the same thing for the PyMol command
    cmd.extend("CTRL-F", lambda s=self : toggler(s))

    # Start the checker function
    checker()


# Toggler function that toggles the trace variable between 0 and 1
def toggler(self, *args):
    # Tell the function about the global variable trace_var
    global trace_var
    global open_var

    # Only toggle the variable if no window is open yet
    if open_var == 0:
        if trace_var == 0:
            trace_var = 1


# Function to check the value of the variable trace_var
def checker():
    # Get the PyMol pmg app root window
    root = plugins.get_tk_root()
    # Tell the function about the global trace_var variable
    global trace_var
    global open_var

    # Check if trace_var is 1
    # if yes, start the plugin and set it back to 0
    if trace_var == 1:
        showWindow()
        trace_var = 0
        open_var = 1

    # Continue checking every 10 ms
    root.after(10, checker)


# Function to reset the open_var
# This function is triggered when in the toplevel window the X close button is pressed
def resetter(self, *args):
    global open_var
    open_var = 0
    self.destroy()



#=========================================================================
# Start the plugin
# This function requires an event as an argument, so passt it a None event
#=========================================================================
def showWindow(event = None):

    # Get the PyMol pmg app root window
    root = plugins.get_tk_root()

    # make a new toplevel window
    top = Toplevel(root)

    # bring the new window into focus
    top.focus()

    # regulate its resize behaviour
    top.resizable(0, 1)
    # set window dimensions
    top.minsize(width=300, height=200)
    top.wm_geometry("")
    top.wm_title("Find in PyMol")

    # Put the focus on the new window
    top.focus_force()

    top.protocol("WM_DELETE_WINDOW", lambda t=top: resetter(t))

    # Generate the main plugin window
    frame = CTRLF(top)
    frame.focus_force()
    
    # And start the refresh routine
    frame.refresh()
