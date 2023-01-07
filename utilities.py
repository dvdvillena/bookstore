#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     utilities.py - Utilities menu screen 
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import time

import npyscreen
from npyscreen import util_viewhelp

import config

helpText =  "  Utilities submenu.\n\n" +\
            "  The user table and some convenience tools I parked here."


class UtilitiesMenuForm(npyscreen.FormBaseNew):
    def __init__(self, name=None, parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None, \
        cycle_widgets=False, *args, **keywords):
        """ Crea el padre, npyscreen._FormBase """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets, *args, **keywords)   # goes to _FormBase.__init__()
        
    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # form with frame
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exitUtilities   # Escape exit
        self.prepara_key_handlers()   # shortcuts
        self.nextrely += 1  # vertical distance between menu title and menu
        # Form title
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Utilities"
        self.name = self.formTitle
        # Screen title line
        wg = self.add(npyscreen.FixedText, name="MainTitle", value=self.name, relx=2, rely=0, editable=False)
        # Menu title line
        wg = self.add(npyscreen.FixedText, name="UtilitiesTitle", value="Utilities menu", relx=30, rely=6, editable=False)
        # Main menu selector
        wg = self.mainSelector()
        # Bottom status line 
        self.statusLine = " Select option "
        wg = self.add(npyscreen.FixedText, name="UtilitiesStatus", value=self.statusLine, relx=2, rely=24, use_max_space=True, editable=False)
        
    def prepara_key_handlers(self):
        self.add_handlers({"1": self.keyHandler})  # menu 1
        self.add_handlers({"2": self.keyHandler})  # menu 2
        self.add_handlers({"3": self.keyHandler})  # menu 3
        self.add_handlers({"q": self.keyHandler})  # exit with "q"
        self.add_handlers({"Q": self.keyHandler})  # exit with "Q"
   
    def keyHandler(self, keyAscii):
        match keyAscii:
            case 49:    # menu 1
                self.selector.cursor_line=0
                self.display()
                time.sleep(0.2)
                self.userSelector()
            case 50:    # menu 2
                self.selector.cursor_line=1
                self.display()
                time.sleep(0.2)
                self.dbIntegrityCheck()
            case 51:    # menu 3
                self.selector.cursor_line=2
                self.display()
                time.sleep(0.2)
                self.deleteMultipleRecords()
            case ( 81 | 113 ):    # menu Q/q
                self.selector.cursor_line=2
                self.display()
                time.sleep(0.2)
                self.exitUtilities()

    def pre_edit_loop(self):
        pass

    def post_edit_loop(self):
        pass

    def _during_edit_loop(self):
        pass

    def mainSelector(self):
        value_list = [
           "1. User edition",
           "2. Check database referential integrity",
           "3. Delete multiple records",
           "Q. Quit utilities" ]

        self.selector = self.add(VerticalMenu,
                        w_id=None,
                        max_height=7,
                        rely=9,
                        relx=28,
                        name="UtilitiesMenu",
                        footer="", 
                        values=value_list,
                        editable=True,
                        hidden=False,
                        slow_scroll=False
                        )
        return self.selector

    def updateMenu(self):
        self.display(clear=True)    # repaints, coming from F1_Help
        self.edit()

    def exitUtilities(self):
        "With Q or Escape keys"
        config.parentApp.setNextForm("MAIN")
        config.parentApp.switchFormNow()

    def userSelector(self):
        "User control info and selector."
        App = config.parentApp
        selectorForm = App._Forms['USERSELECTOR']
        selectorForm.update_grid()  # must be read here to get config.fileRows right
        selectorForm.ask_option()
        App.switchForm("USERSELECTOR")

    def dbIntegrityCheck(self):
        "Check database referential integrity." 
        App = config.parentApp
        App.switchForm("DB_INTEGRITY_CHECK")

    def deleteMultipleRecords(self):
        "Delete multiple records (books)." 
        App = config.parentApp
        App.switchForm("DELETE_MULTIPLE_RECORDS")

    def h_display_help(self, input):
        "Adaptation from FormBase to redraw the menu screen."
        if self.help == None: return
        if self.name:
            help_name="%s - Help" %(self.name)
        else: 
            help_name=None
        util_viewhelp.view_help(self.help, title=help_name, autowrap=self.WRAP_HELP)
        self.display()
        self.updateMenu()
        return True


class VerticalMenu(npyscreen.MultiLineAction):
    " Main Menu "
    def actionHighlighted(self, act_on_this, keypress):
        #print(act_on_this, keypress)
        if act_on_this[0] == "Q":  # Quit utilities menu
            UtilitiesMenuForm.exitUtilities(UtilitiesMenuForm)
        elif act_on_this[0] == "1": # User edition
            UtilitiesMenuForm.userSelector(UtilitiesMenuForm)
        elif act_on_this[0] == "2": # Check integrity
            UtilitiesMenuForm.dbIntegrityCheck(UtilitiesMenuForm)
        elif act_on_this[0] == "3": # Delete multiple records
            UtilitiesMenuForm.deleteMultipleRecords(UtilitiesMenuForm)
