#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     mainMenu.py - Main menu screen
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import datetime
import os.path
import sqlite3
import sys
import time
import tracemalloc
import linecache

import npyscreen
from npyscreen import util_viewhelp

import author
import authorSelector
import book
import bookListing
import bookSelector
import bsWidgets as bs

import config
import identification
import publisher
import publisherSelector
import user
import userSelector
import utilities
import warehouse
import warehouseSelector
import dbIntegrityCheck
import deleteMultipleRecords
from config import SCREENWIDTH as WIDTH

AUTHENTICATE = config.AUTHENTICATE
DATEFORMAT = config.dateFormat

helpText =  "\nA simple menu form.\n\n\n" +\
    "* There's a 'Main menu' title that is a plain npyscreen.FixedText widget.\n\n" +\
    "* Under the title, there's the main selector widget, an adapted npyscreen.MultiLineAction.\n\n" +\
    "* Options can be accessed through the arrow keys + Enter, or through the direct pressing of a number key.\n\n" +\
    "* Menu '6.Utilities' leads to another submenu.\n\n" +\
    "* The main purpose of this program is to share my experience with the npyscreen terminal user interface and of course to learn some Python." 


class bookstoreApp(npyscreen.NPSAppManaged):
    def onStart(self):
        "Override this method to perform any initialization."
        
        self.connect_database()

        # check tables' existence:
        cur = config.conn.cursor()
        DBprefix = "bookstore."
        table_list = [  "author",
                        "book",
                        "book_author",
                        "publisher",
                        "user",
                        "warehouse",
                        "book_warehouse"
                        ]

        while True: # locking the SQLite single user DB
            for tname in table_list:
                tname = DBprefix + tname
                sqlQuery = "SELECT EXISTS ( SELECT name FROM sqlite_schema WHERE type='table' AND name=? )"
                try:
                    cur.execute(sqlQuery, (tname,) )
                    if cur.fetchone()[0] != 1 : 
                        bs.notify_OK("\n Database: Table does not exist: '" + tname + "'","Error")
                        sys.exit()                
                except sqlite3.OperationalError:    # default timeout is 5 sec
                    bs.notify_OK("\n    Database is locked, please wait.", "Bookstore")
                    continue    # to the loop
            break   # go on

        npyscreen.setTheme(npyscreen.Themes.DefaultTheme)

        # Forms __inits__() are executed now:
        self.registerForm("MAIN", MainMenuForm(name="MainMenu", parentApp=self, help=helpText, \
            lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH, maximum_columns=WIDTH))
        self.registerForm("IDENTIFICATION", identification.ID_Form(name="Identification", parentApp=self, \
            help=identification.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("BOOKSELECTOR", bookSelector.BookSelectForm(name="BookSelector", parentApp=self, \
            help=bookSelector.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("BOOK", book.BookForm(name="BookForm", parentApp=self, \
            help=book.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("AUTHORSELECTOR", authorSelector.AuthorSelectForm(name="AuthorSelector", parentApp=self, \
            help=authorSelector.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("AUTHOR", author.AuthorForm(name="AuthorForm", parentApp=self, \
            help=author.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("PUBLISHERSELECTOR", publisherSelector.PublisherSelectForm(name="PublisherSelector", parentApp=self, \
            help=publisherSelector.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("PUBLISHER", publisher.PublisherForm(name="PublisherForm", parentApp=self, \
            help=publisher.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("WAREHOUSESELECTOR", warehouseSelector.WarehouseSelectForm(name="WarehouseSelector", parentApp=self, \
            help=warehouseSelector.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("WAREHOUSE", warehouse.WarehouseForm(name="WarehouseForm", parentApp=self, \
            help=warehouse.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("BOOKLISTING", bookListing.BookListingForm(name="BookListingForm", parentApp=self, \
            help=bookListing.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("UTILITIES", utilities.UtilitiesMenuForm(name="UtilitiesForm", parentApp=self, \
            help=utilities.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("USERSELECTOR", userSelector.UserSelectForm(name="UserSelector", parentApp=self, \
            help=userSelector.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("USER", user.UserForm(name="UserForm", parentApp=self, \
            help=user.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("DB_INTEGRITY_CHECK", dbIntegrityCheck.DBintegrityCheckForm(name="DBintegrityCheckForm", parentApp=self, \
            help=dbIntegrityCheck.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))
        self.registerForm("DELETE_MULTIPLE_RECORDS", deleteMultipleRecords.DeleteMultipleRecordsForm(name="DeleteMultipleRecordsForm", parentApp=self, \
            help=deleteMultipleRecords.helpText, lines=0, columns=0, minimum_lines=25, minimum_columns=WIDTH))

    def onInMainLoop(self):
        """Called between each screen while the application is running. Not called before the first screen. Override at will"""
        if self.NEXT_ACTIVE_FORM == 'IDENTIFICATION':
            form = self._Forms["IDENTIFICATION"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'BOOKSELECTOR':
            form = self._Forms["BOOKSELECTOR"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'AUTHORSELECTOR':
            form = self._Forms["AUTHORSELECTOR"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'PUBLISHERSELECTOR':
            form = self._Forms["PUBLISHERSELECTOR"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'WAREHOUSESELECTOR':
            form = self._Forms["WAREHOUSESELECTOR"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'BOOKLISTING':
            form = self._Forms["BOOKLISTING"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.
        elif self.NEXT_ACTIVE_FORM == 'USERSELECTOR':
            form = self._Forms["USERSELECTOR"]
            form.editw = 1  # focus to widget 1 (grid) so InputOpt field lose it.

    def connect_database(self):
        "Check and connect database."
        # SQLite DB file exists:
        DBpath = config.dataPath
        DBname = config.dbname
        self.DBfilename = DBpath + DBname
        if not os.path.exists(self.DBfilename):
            bs.notify_OK("\n  Database file "+self.DBfilename+" does not exist.", "Error")
            sys.exit()
        # DB Connection creation
        conn = None
        try:
            conn = sqlite3.connect(self.DBfilename)
        except sqlite3.Error as e:
            print(e)
        config.conn = conn      # connection for this instance of bookstore

    def onCleanExit(self):
        """Override this method to perform any cleanup when application is exiting without error."""
        

class MainMenuForm(npyscreen.FormBaseNew):
    "Main menu form."

    def __init__(self, name=None, parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None, \
        cycle_widgets=False, *args, **keywords):
        """ Crea el padre, npyscreen._FormBase """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets, *args, **keywords)   # goes to _FormBase.__init__()
        
        self.password_entered = False
        self.app = parentApp

    def create(self):
        "The standard constructor will call the method .create(), which you should override to create the Form widgets."
        self.framed = True   # form with frame
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exitApplication   # Escape exit
        self.setup_key_handlers()   # shortcuts
        self.nextrely += 1  # vertical distance between menu title and menu
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Main"
        self.name = self.formTitle
        # Screen title line
        wg = self.add(npyscreen.FixedText, name="MainTitle", value=self.name, relx=2, rely=0, editable=False)
        # Menu title line
        wg = self.add(npyscreen.FixedText, name="MenuTitle", value="Main menu", relx=32, rely=6, editable=False)
        # Main menu selector
        wg = self.mainSelector()
        # Bottom status line
        self.statusLine = " Select option "
        wg = self.add(npyscreen.FixedText, name="MainStatus", value=self.statusLine, relx=2, rely=24, use_max_space=True, editable=False)
        
    def setup_key_handlers(self):
        self.add_handlers({"1": self.keyHandler})  # menu 1
        self.add_handlers({"2": self.keyHandler})  # menu 2
        self.add_handlers({"3": self.keyHandler})  # menu 3
        self.add_handlers({"4": self.keyHandler})  # menu 4
        self.add_handlers({"5": self.keyHandler})  # menu 5
        self.add_handlers({"6": self.keyHandler})  # menu 6
        self.add_handlers({"q": self.keyHandler})  # exit with "q"
        self.add_handlers({"Q": self.keyHandler})  # exit with "Q"
   
    def pre_edit_loop(self):
        if AUTHENTICATE and not self.password_entered:
            self.password_entered = True
            identification.ID_Form.set_ID()

    def post_edit_loop(self):
        pass
    
    def _during_edit_loop(self):
        pass

    def mainSelector(self):
        value_list = [
           "1. Book edition",
           "2. Author edition",
           "3. Publisher edition",
           "4. Warehouse edition",
           "5. Book listing",
           "6. Utilities",
           "Q. Quit program" ]

        self.selector = self.add(VerticalMenu,
                        w_id=None,
                        max_height=11,
                        rely=9,
                        relx=29,
                        name="MainMenu",
                        footer="", 
                        values=value_list,
                        editable=True,
                        hidden=False,
                        slow_scroll=False
                        )
        return self.selector
        
    def keyHandler(self, keyAscii):
        match keyAscii:
            case 49:    # menu 1
                self.selector.cursor_line=0
                self.display()
                time.sleep(0.2)
                self.menuBookSelector()
            case 50:    # menu 2
                self.selector.cursor_line=1
                self.display()
                time.sleep(0.2)
                self.menuAuthorSelector()
            case 51:    # menu 3
                self.selector.cursor_line=2
                self.display()
                time.sleep(0.2)
                self.menuPublisherSelector()
            case 52:    # menu 4
                self.selector.cursor_line=3
                self.display()
                time.sleep(0.2)
                self.menuWarehouseSelector()
            case 53:    # menu 5
                self.selector.cursor_line=4
                self.display()
                time.sleep(0.2)
                self.menuBookListing()
            case 54:    # menu 6
                self.selector.cursor_line=5
                self.display()
                time.sleep(0.2)
                self.menuUtilities()
            case ( 81 | 113 ):    # menu Q/q
                self.selector.cursor_line=9
                self.display()
                time.sleep(0.2)
                self.exitApplication()

    def menuBookSelector(self):
        # Calls books selector
        selectorForm = self.parentApp._Forms['BOOKSELECTOR']
        selectorForm.update_grid()  # must be read here to get config.fileRows right
        selectorForm.ask_option()
        self.app.switchForm("BOOKSELECTOR")
        
    def menuAuthorSelector(self):
        # Calls authors selector
        selectorForm = self.parentApp._Forms['AUTHORSELECTOR']
        selectorForm.update_grid()  # must be read here to get config.fileRows right
        selectorForm.ask_option()
        self.app.switchForm("AUTHORSELECTOR")
        
    def menuPublisherSelector(self):
        # Calls publishers selector
        selectorForm = self.parentApp._Forms['PUBLISHERSELECTOR']
        selectorForm.update_grid()  # must be read here to get config.fileRows right
        selectorForm.ask_option()
        self.app.switchForm("PUBLISHERSELECTOR")
        
    def menuWarehouseSelector(self):
        # Calls warehouse selector
        selectorForm = self.parentApp._Forms['WAREHOUSESELECTOR']
        selectorForm.update_grid()  # must be read here to get config.fileRows right
        selectorForm.ask_option()
        self.app.switchForm("WAREHOUSESELECTOR")

    def menuBookListing(self):
        # Calls book listing 
        form = self.parentApp._Forms['BOOKLISTING']
        form.initialize()
        self.app.switchForm("BOOKLISTING")
        
    def menuUtilities(self):
        # Call utilities menu.
        self.app.switchForm("UTILITIES")

    def updateMenu(self):
        self.display(clear=True)    # repaints, coming from F1_Help
        self.edit()
        
    def exitApplication(self):

        if config.TRACEMALLOC:
            snapshot = tracemalloc.take_snapshot()
            self.display_top(snapshot)

        if config.CONFIRMEXIT:
            message = "  Press OK to exit the application"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                print(config.normal_exit_message)
                sys.exit()
        else:
            print(config.normal_exit_message)
            sys.exit()

    def h_display_help(self, input):
        "Adaptation from FormBase to redraw the menu screen"
        if self.help == None: return
        if self.name:
            help_name="%s - Help" %(self.name)
        else: 
            help_name=None
        util_viewhelp.view_help(self.help, title=help_name, autowrap=self.WRAP_HELP)
        self.display()
        self.updateMenu()
        return True

    def get_today(self):
        sep = DATEFORMAT[2]
        if DATEFORMAT[0] == "d":
            format = "%d"+sep+"%m"+sep+"%Y"
        else:
            format = "%m"+sep+"%d"+sep+"%Y"
        return datetime.datetime.today().strftime(format)

    def display_top(self, snapshot, key_type='lineno', limit=10):
        "tracemalloc results."
        snapshot = snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))
        top_stats = snapshot.statistics(key_type)

        print("Top %s lines" % limit)
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            print("#%s: %s:%s: %.1f KiB"
                  % (index, frame.filename, frame.lineno, stat.size / 1024))
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line:
                print('    %s' % line)

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            print("%s other: %.1f KiB" % (len(other), size / 1024))
        total = sum(stat.size for stat in top_stats)
        print("Total allocated size: %.1f KiB" % (total / 1024))


class VerticalMenu(bs.MyMultiLineAction):
    " Main Menu "
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.how_exited = True

    def actionHighlighted(self, act_on_this, keypress):
        "Select by arrows + Enter key."
        form = self.parent
        if act_on_this[0] == "1":   # Book selector
            form.menuBookSelector()
        elif act_on_this[0] == "2": # Author selector
            form.menuAuthorSelector()
        elif act_on_this[0] == "3": # Publisher selector
            form.menuPublisherSelector()
        elif act_on_this[0] == "4": # Warehouse selector
            form.menuWarehouseSelector()
        elif act_on_this[0] == "5": # Book listing
            form.menuBookListing()
        elif act_on_this[0] == "6": # Utilities
            form.menuUtilities()
        elif act_on_this[0] == "Q": # Quit program
            form.exitApplication()
