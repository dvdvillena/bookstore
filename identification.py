#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     identification.py - Ask for user, password and datetime
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import base64
import curses
import sys

import npyscreen

import bsWidgets as bs
import config

EXITED_DOWN  =  1   # copied from npyscreen
DBTABLENAME = "'bookstore.User'"
DATETIMEFORMAT = config.dateTimeFormat
global form

helpText = "Enter user 'david' and password '1234' to go on.\n\nA simple identification initial form. Can be deactivated by a variable.\n\n" +\
    "* As in all the next forms, you can move along the different input fields using the TAB or Enter keys. " +\
    "But keep in mind that the Enter key activates/runs a button like 'OK' when it is reached.\n\n" +\
    "* So the right way to jump between the fields is TAB to move forward, and shift-TAB to move backwards. " +\
    " Use the enter key to 'press' the buttons.\n\n" +\
    "* Here you can check that the forward motion of the TAB is not limited and keeps returning to the first field, " +\
    "but in other forms it is limited in the last item if it's a 'Cancel' button.\n\n" +\
    "* This ID form displays error messages at the bottom line when input fields are left empty, and shows an " +\
    "error dialog when 'OK' is pressed and the user or password are wrong.\n\n" +\
    "* This ID form can be exited using the Esc key, but other forms can only be exited through the use of OK/Cancel buttons. " +\
    "This is to enforce the end user to answer explicit options."


class ID_Form(npyscreen.FormBaseNew):
    "ID entry form"

    def __init__(self, name="User", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
        widget_list=None, cycle_widgets=True, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        """ Creates the father, npyscreen.FormBaseNew. """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

        global form
        form = self

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # boxed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exitID   # Escape exit
        
        # Form title
        version = config.program_version
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Authentication "
        self.title=self.add(npyscreen.FixedText, name="UserIDTitle", value=self.formTitle, relx=2, rely=0, editable=False)  # Línea de título de pantalla
        self.title.how_exited = EXITED_DOWN    # for cursor positioning
        # Form fields
        self.userFld=self.add(bs.MyTitleText, name="User:", value="", relx=27, rely=8, begin_entry_at=12, editable=True)
        self.passwordFld=self.add(npyscreen.TitlePassword, name="Password:", value="", relx=27, rely=10, begin_entry_at=12, editable=False)
        self.ok_button=self.add(ID_MiniButtonPress, name="  OK  ", relx=35, rely=15, editable=True)
        self.statusLine=self.add(npyscreen.FixedText, name="IDStatus", value="Press Esc to exit", relx=2, rely=23, use_max_space=True, editable=False)

    def exitID(self):
        "Only for escape-exit from identification form."
        print("Program exited normally.")
        sys.exit()

    def textfield_exit(self):
        "Exit from a text field with Escape"
        global form
        form.exitID()

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def check_fields_values(self):
        "Checking for wrong values in the fields."
        errorMsg = None
        self.userFld.value = self.userFld.value.strip()
        self.passwordFld.value = self.passwordFld.value.strip()

        # empty value check:  user field
        if self.userFld.value == "":
            self.editw = 0  # truco, porque aplica el ch(13)=EXITED_DOWN del botón!
            self.ok_button.editing = False
            errorMsg = "Error: User field is empty"
            return errorMsg

        # empty value check:  password field
        if self.passwordFld.value == "":
            self.editw = 1  # truco, porque aplica el ch(13)=EXITED_DOWN del botón!
            self.ok_button.editing = False
            errorMsg = "Error: Password field is empty"
            return errorMsg

    def OKbtn_function(self):
        "Search user and password."

        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return

        cur = config.conn.cursor()
        sqlQuery = "SELECT user, user_level, password FROM " + DBTABLENAME + " WHERE user = ?"
        cur.execute(sqlQuery, (self.userFld.value,) )
        user_row = cur.fetchone()
        if user_row is None:
            bs.notify_OK("\n  User does not exist ", "Error")
            self.editw = 0
            self.ok_button.editing = False
        else:   # User was found
            "Cheap encryption of the password"
            dataBytes = base64.b64encode(self.passwordFld.value.encode('utf-8'))
            dataBytes = repr(dataBytes)[2:-1]
            if dataBytes != user_row[2]:
                bs.notify_OK("\n  Wrong password ", "Error")
                self.passwordFld.value = ""
                self.editw = 1
                self.ok_button.editing = False
            else:   # Password is OK: exit from this form to the main menu
                self.editing = False

    def set_ID():
        "Called from main menu."
        global form
        form.userFld.editable = True
        form.userFld.value = ""
        form.passwordFld.editable = True
        form.passwordFld.value = ""
        form.ok_button.when_pressed_function = form.OKbtn_function
        form.edit()


class ID_MiniButtonPress(bs.MyMiniButtonPress):
    "DV: Added Esc-key exit capacity."
    # NB.  The when_pressed_function functionality is potentially dangerous. It can set up
    # a circular reference that the garbage collector will never free. 
    # If this is a risk for your program, it is best to subclass this object and
    # override when_pressed_function instead.  Otherwise your program will leak memory.
    def __init__(self, screen, when_pressed_function=None, *args, **keywords):
        super(bs.MyMiniButtonPress, self).__init__(screen, *args, **keywords)  # goes to class MyMiniButtonPress
        self.when_pressed_function = when_pressed_function
            
    def h_escape(self, ch):     # Escape key on the buttons
        print(config.normal_exit_message)
        sys.exit()
