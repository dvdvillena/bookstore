#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     user.py - User form
#
##############################################################################
# Copyright (c) 2022 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import base64
import curses
import sqlite3
import time

import npyscreen

import bsWidgets as bs
import config

EXITED_DOWN  =  1   # copied from npyscreen
DATEFORMAT = config.dateFormat
DBTABLENAME = "'bookstore.User'"

global form

helpText =  "The form for the final user record.\n\n" \
    "* The user level is intended to serve as a security level of some kind for every user, " \
    "but that security mechanism is not yet implemented.\n\n" +\
    "* There's a 'Change password' button to enter the new password, that is immediately encrypted."


class UserForm(npyscreen.FormBaseNew):
    "User record on screen for maintenance."
    def __init__(self, name="User", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
        widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        """ Creates the father, npyscreen.FormBaseNew. """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

        global form
        form = self

        self.selectorForm = self.parentApp._Forms['USERSELECTOR']

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_user   # Escape exit
        
        # Form title
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - User record "
        self.formTitleFld=self.add(bs.MyFixedText, name="UserTitle", value=self.formTitle, relx=2, rely=0, editable=False)  # Línea de título de pantalla
        # Form fields
        self.numeralFld=self.add(bs.MyTitleText, name="Numeral:", value="", relx=16, rely=6, begin_entry_at=15, editable=False)
        self.numeralFld.how_exited = EXITED_DOWN    # for Create mode
        self.userFld=self.add(bs.MyTitleText, name="User:", value="", relx=16, rely=8, begin_entry_at=15, editable=False)
        self.usernameFld=self.add(bs.MyTitleText, name="Full name:", value="", relx=16, rely=10, begin_entry_at=15, editable=False)
        self.userlevelFld=self.add(bs.MyTitleText, name="User level:", value="", relx=16, rely=12, begin_entry_at=15, editable=False)
        self.creationDateFld=self.add(bs.TitleDateField, name="Creation date:", value="", format=DATEFORMAT, 
            relx=16, rely=14, begin_entry_at=15, editable=False)
        self.passwordFld=self.add(npyscreen.TitlePassword, name="Encrypted password:", value="", relx=16, rely=16, begin_entry_at=22, use_max_space=False, editable=False)
        self.change_password_button=self.add(bs.MyMiniButtonPress, name="Change Password", relx=50, rely=16, editable=False)
        self.ok_button=self.add(bs.MyMiniButtonPress, name="  OK  ", relx=28, rely=20, editable=True)
        self.cancel_button=self.add(bs.MyMiniButtonPress, name="Cancel", relx=44, rely=20, editable=True)
        self.statusLine=self.add(npyscreen.FixedText, name="UserStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)

    def backup_fields(self):
        self.bu_numeral = self.numeralFld.value
        self.bu_user = self.userFld.value
        self.bu_username = self.usernameFld.value
        self.bu_userlevel = self.userlevelFld.value
        self.bu_creationDate = self.creationDateFld.value
        self.bu_password = self.passwordFld.value  

    def update_fileRow(self):
        "Updates config.fileRow."
        if self.current_option != "Delete":
            id = config.fileRow[0]
            for row in config.fileRows:
                if row[0] == id:
                    config.fileRow = []
                    config.fileRow.append(row[0])
                    config.fileRow.append(int(self.numeralFld.value))
                    config.fileRow.append(self.userFld.value)
                    config.fileRow.append(self.usernameFld.value)
                    config.fileRow.append(self.userlevelFld.value)
                    config.fileRow.append(self.creationDateFld.value)
                    config.fileRow.append(self.passwordFld.value)
                    break

    def exit_user(self):
        "Only for escape-exit, handler version."
        self.exitUser(modified=False)

    def exitUser(self, modified):
        "Exit record form."
        self.passwordFld.label_widget.value = "Encrypted password:"
        if modified:    # modify grid if needed
            self.update_fileRow()
            #selectorForm = self.parentApp._Forms['USERSELECTOR']
            self.selectorForm.update_grid()
            self.backup_fields()
        self.selectorForm.grid.update()

        # To unlock the database (for Create) we must disconnect and re-connect:
        config.conn.close()
        self.parentApp.connect_database()

        config.parentApp.setNextForm("USERSELECTOR")
        config.parentApp.switchFormNow()

    def get_last_numeral(self):
        cur = config.conn.cursor()
        sqlQuery = "SELECT Numeral FROM " + DBTABLENAME + " ORDER BY Numeral DESC LIMIT 1"
        cur.execute(sqlQuery)
        try:
            numeral = cur.fetchone()[0]
        except TypeError:   # there are no rows
            numeral = 0
        config.conn.commit()
        return numeral

    def set_createMode():
        "Setting the user form to create a new record."
        global form
        conn = config.conn
        while True:     # for Creation, we must set the locking here
            try:
                conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite only allows a single writer per database
                conn.execute('PRAGMA locking_mode = EXCLUSIVE')
                conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
                break
            except sqlite3.OperationalError:
                bs.notify_OK("\n    Database is locked, please wait.", "Message")
        form.current_option = "Create"
        form.numeralFld.editable = True
        form.numeralFld.maximum_string_length = 3
        form.numeralFld.value = str(form.get_last_numeral() + 1)
        form.userFld.editable = True
        form.userFld.value = ""
        form.usernameFld.editable = True
        form.usernameFld.value = ""
        form.userlevelFld.editable = True
        form.userlevelFld.value = ""
        form.creationDateFld.editable = True
        form.creationDateFld.value = form.selectorForm.today
        form.passwordFld.editable = True
        form.passwordFld.value = ""
        form.change_password_button.editable = False
        form.ok_button.when_pressed_function = form.createOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.createCancelbtn_function
        form.statusLine.value = "Creating a new record"
        form.backup_fields()
        form.editw = form.get_editw_number("User:")
        config.last_operation = "Create"

    def set_readOnlyMode():
        "Setting the user form for read only display."
        global form
        form.current_option = "Read"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.userFld.editable = False
        form.usernameFld.editable = False
        form.userlevelFld.editable = False
        form.creationDateFld.editable = False
        form.passwordFld.editable = False
        form.change_password_button.editable = False
        form.ok_button.when_pressed_function = form.readOnlyOKbtn_function
        form.ok_button.name = "OK"  # name changes between calls
        form.cancel_button.when_pressed_function = form.readOnlyCancelbtn_function
        form.statusLine.value = "Read-Only mode"
        form.editw = form.get_editw_number("  OK  ")
        config.last_operation = "Read"

    def set_updateMode():
        "Setting the user form for update editing."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.current_option = "Update"
        form.convertDBtoFields()
        form.numeralFld.editable = True
        form.numeralFld.maximum_string_length = 3
        form.userFld.editable = True
        form.usernameFld.editable = True
        form.userlevelFld.editable = True
        form.creationDateFld.editable = True
        form.passwordFld.editable = False
        form.change_password_button.when_pressed_function = form.changePasswordbtn_function
        form.change_password_button.editable = True
        form.password_changed = False
        form.ok_button.when_pressed_function = form.updateOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.updateCancelbtn_function
        form.statusLine.value = "Update mode: editing record"
        form.backup_fields()
        form.editw = form.get_editw_number("User:")
        config.last_operation = "Update"

    def set_deleteMode():
        "Setting the user form for deleting."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.current_option = "Delete"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.userFld.editable = False
        form.usernameFld.editable = False
        form.userlevelFld.editable = False
        form.creationDateFld.editable = False
        form.passwordFld.editable = False
        form.change_password_button.editable = False
        form.ok_button.when_pressed_function = form.deleteOKbtn_function
        form.ok_button.name = "Delete"
        form.cancel_button.when_pressed_function = form.deleteCancelbtn_function
        form.statusLine.value = "Delete mode"
        form.editw = form.get_editw_number("Delete")
        config.last_operation = "Delete"

    def convertDBtoFields(self):
        "Convert DB fields into screen fields (strings)."
        self.numeralFld.value = str(config.fileRow[1])
        self.userFld.value = config.fileRow[2]
        self.usernameFld.value = config.fileRow[3]
        self.userlevelFld.value = str(config.fileRow[4])
        self.creationDateFld.value = self.DBtoScreenDate(config.fileRow[5], DATEFORMAT)
        self.passwordFld.value = config.fileRow[6]

    def strip_fields(self):
        "Required trimming of leading and trailing spaces."
        self.numeralFld.value = self.numeralFld.value.strip()
        self.userFld.value = self.userFld.value.strip()
        self.usernameFld.value = self.usernameFld.value.strip()
        self.userlevelFld.value = self.userlevelFld.value.strip()
        self.creationDateFld.value = self.creationDateFld.value.strip()
        self.passwordFld.value = self.passwordFld.value.strip()
    
    def save_mem_record(self):
        "Save new record (from Create) in global variable."
        config.fileRow = []
        config.fileRow.append(None)    # ID field is incremental, fulfilled later
        config.fileRow.append(int(self.numeralFld.value))
        config.fileRow.append(self.userFld.value)
        config.fileRow.append(self.usernameFld.value)
        config.fileRow.append(int(self.userlevelFld.value))
        config.fileRow.append(self.creationDateFld.value)
        config.fileRow.append(self.passwordFld.value)
    
    def createOKbtn_function(self):
        "OK button function under Create mode."
        self.strip_fields()     # Get rid of spaces
        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        else:
            if self.exist_changes():
                self.save_mem_record()  # backup record in config variable
                self.encrypt_password()
                self.save_created_user()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.exitUser(modified=False)

    def createCancelbtn_function(self):
        "Cancel button function under Create mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard creation?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitUser(modified=False)
        else:
            self.exitUser(modified=False)
   
    def readOnlyOKbtn_function(self):
        "OK button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitUser(modified=False)

    def readOnlyCancelbtn_function(self):
        "Cancel button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitUser(modified=False)

    def delete_user(self):
        "Button based Delete function for D=Delete."
        conn = config.conn
        cur = conn.cursor()
        id = config.fileRow[0]
        sqlQuery = "DELETE FROM " + DBTABLENAME + " WHERE id = " + str(id)
        cur.execute(sqlQuery)
        conn.commit()
        bs.notify("\n       Record deleted", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        # update config.fileRows:
        index = 0           # for positioning
        for row in config.fileRows:
            if row[0] == id:
                config.fileRows.remove(row)
                break
            index += 1
        # update config.fileRow to the previous record in list:
        if index > 0:
            index -= 1
        try:
            config.fileRow = config.fileRows[index]
        except IndexError:  # there are no rows in the table
            config.fileRow = []
        self.exitUser(modified=True)

    def deleteOKbtn_function(self):
        "OK button function under Delete mode."
        # Ask for confirmation to delete
        message = "\n   Select OK to confirm deletion"
        if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            self.delete_user()
            try:
                numeral = config.fileRow[1]
            except IndexError:
                numeral = None            
            self.selectorForm.grid.set_highlight_row(numeral)
        else:
            self.exitUser(modified=False)

    def deleteCancelbtn_function(self):
        "Cancel button function under Delete mode."
        bs.notify("\n   Record was NOT deleted", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        time.sleep(0.4)     # let it be seen
        self.exitUser(modified=False)

    def while_editing(self, *args, **keywords):
        "Executes in between fields."
        pass

    def get_editw_number(self, fieldName):
        "Returns the .editw number of fieldName"
        for w in self._widgets_by_id:
            if self._widgets_by_id[w].name == fieldName:
                return w

    def check_fields_values(self):
        "Checking for wrong values in the fields."
        errorMsg = None

        # Mandatory values check:
        emptyField = False
        if self.numeralFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Numeral:") - 1
        elif self.userFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("User:") - 1
        elif self.creationDateFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Creation date:") - 1
        elif self.passwordFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Encrypted password:") - 1
        if emptyField:
            self.ok_button.editing = False
            errorMsg = "Error:  Mandatory field is empty"
            return errorMsg

        # wrong value check: numeral field
        try:
            a = int(self.numeralFld.value)
        except ValueError:
            self.editw = self.get_editw_number("Numeral:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: Numeral must be an integer"
            return errorMsg
        if len(self.numeralFld.value) > self.numeralFld.maximum_string_length:
            self.editw = self.get_editw_number("Numeral:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: Numeral maximum length exceeded"
            return errorMsg

        # wrong value check: user field
        if " " in self.userFld.value:
            self.editw = self.get_editw_number("User:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: User must be a single word"
            return errorMsg

        # wrong value check: userlevel field
        try:
            a = int(self.userlevelFld.value)
        except ValueError:
            self.editw = self.get_editw_number("User level:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: User level must be integer"
            return errorMsg

        # wrong value check: password field
        if " " in self.passwordFld.value:
            self.editw = self.get_editw_number("Encrypted password:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: Password must be a single word"
            return errorMsg            

        # repeated value check: numeral and user fields
        if self.numeralFld.value != self.bu_numeral or self.userFld.value != self.bu_user:
            for row in config.fileRows:
                self.ok_button.editing = False
                # Ya existe y no es él mismo
                if row[1] == int(self.numeralFld.value) and self.numeralFld.value != self.bu_numeral:
                    self.editw = self.get_editw_number("Numeral:") - 1
                    errorMsg = "Error:  Numeral already exists"
                    return errorMsg
                # Ya existe y no es él mismo
                if row[2] == self.userFld.value and self.userFld.value != self.bu_user:
                    self.editw = self.get_editw_number("User:") - 1
                    errorMsg = "Error:  User already exists"
                    return errorMsg

        # wrong value check: user field
        if not self.userFld.value[0].isalpha():
            self.ok_button.editing = False
            self.editw = self.get_editw_number("User:") - 1
            errorMsg = "Error: User field must start with a letter"
            return errorMsg
        else:
            if not self.userFld.value.isalnum():
                self.ok_button.editing = False
                self.editw = self.get_editw_number("User:") - 1
                errorMsg = "Error: User field must be alphanumeric"
                return errorMsg

        # check de fecha errónea:
        if not self.creationDateFld.check_value_is_ok():
            self.ok_button.editing = False
            self.editw = self.get_editw_number("Creation date:") - 1
            errorMsg = "Error: Incorrect date; format is "+self.creationDateFld.format
            return errorMsg

    def exist_changes(self):
        "Checking for changes to the fields."
        exist_changes = False
        if self.numeralFld.value != self.bu_numeral or self.userFld.value != self.bu_user or \
            self.usernameFld.value != self.bu_username or self.userlevelFld.value != self.bu_userlevel or \
            self.creationDateFld.value != self.bu_creationDate or self.passwordFld.value != self.bu_password:
            exist_changes = True
        return exist_changes    

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def encrypt_password(self):
        "Quick'n'dirty encryption of the password when saving record."
        dataBytes = base64.b64encode(self.passwordFld.value.encode('utf-8'))
        self.passwordFld.value = repr(dataBytes)[2:-1]
        form.editw = form.get_editw_number("Encrypted password:") - 1
    
    def save_created_user(self):
        "Button based Save function for C=Create."
        conn = config.conn
        cur = conn.cursor()
        DBcreationDate = self.screenToDBDate(self.creationDateFld.value, self.creationDateFld.format)
        sqlQuery = "INSERT INTO " + DBTABLENAME + " (numeral,user,user_name,user_level,creation_date,password) VALUES (?,?,?,?,?,?)"
        values = (self.numeralFld.value, self.userFld.value, self.usernameFld.value, self.userlevelFld.value, DBcreationDate, self.passwordFld.value)
        cur.execute(sqlQuery, values)
        conn.commit()
        conn.isolation_level = None     # free the multiuser lock
        config.fileRow[0] = cur.lastrowid
        bs.notify("\n       Record created", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        # actualizo config.fileRows:
        new_record = []
        new_record.append(config.fileRow[0])
        new_record.append(int(self.numeralFld.value))
        new_record.append(self.userFld.value)
        new_record.append(self.usernameFld.value)
        new_record.append(int(self.userlevelFld.value))
        new_record.append(self.creationDateFld.value)
        new_record.append(self.passwordFld.value)
        config.fileRows.append(new_record)
        self.exitUser(modified=True)

    def save_updated_user(self):
        "Button based Save function for U=Update."
        if self.password_changed:   # we've changed the password
            self.encrypt_password()
            bs.notify("\n    Encrypting password", title="Message", form_color='STANDOUT', wrap=True, wide=False)
            self.password_changed = False
        cur = config.conn.cursor()
        DBcreationDate   = self.screenToDBDate(self.creationDateFld.value, self.creationDateFld.format)
        sqlQuery = "UPDATE " + DBTABLENAME + " SET numeral=?, user=?, user_name=?, user_level=?, creation_date=?, \
            password=? WHERE id=?"
        values = (str(self.numeralFld.value), self.userFld.value, self.usernameFld.value, self.userlevelFld.value, \
            DBcreationDate, self.passwordFld.value, config.fileRow[0])
        try:
            cur.execute(sqlQuery, values)
            config.conn.commit()
        except sqlite3.IntegrityError:
            bs.notify_OK("\n     Numeral or user already exists. ", "Message")
            return

        bs.notify("\n       Record saved", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        self.exitUser(modified=True)
        
    def updateOKbtn_function(self):
        "OK button function under Update mode."
        self.strip_fields()     # Get rid of spaces
        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        else:
            if self.exist_changes():
                self.save_updated_user()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
                self.exitUser(modified=False)

    def changePasswordbtn_function(self):
        self.change_password_button.editing = False
        self.change_password_button.editable = False
        self.passwordFld.editable = True
        self.passwordFld.value = ""
        self.passwordFld.label_widget.value = "New password:"
        self.editw = 5
        self.password_changed = True
    
    def updateCancelbtn_function(self):
        "Cancel button function under Update mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard changes?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitUser(modified=False)
        else:
            self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            self.exitUser(modified=False)

    def screenToDBDate(self, screenDate, screenFormat):
        "Converts a simple screen date to a SQLite DB timestamp"
        if screenDate == "":
            return ""   # non-mandatory dates
        if screenFormat[0] == "d":
            day   = screenDate[0:2]
            month = screenDate[3:5]
        else:
            day   = screenDate[3:5]
            month = screenDate[0:2]
        year = screenDate[6:]
        if len(year) == 2:
            if int(year) > 69:           # Hmm...
                century = "19"
            else:
                century = "20"
            year = century + year
        DBdate = year + "-" + month + "-" + day + " 00:00:00.000"
        return DBdate

    def DBtoScreenDate(self, DBdate, format):
        "Converts DB timestamp to screen simple date."
        self.possible_formats = config.dateAcceptedFormats
        if DBdate in ["", None] or format in ["", None]:
            return ""
        if format not in self.possible_formats:
            return "FormatError"
        day   = DBdate[8:10]
        month = DBdate[5:7]
        year  = DBdate[0:4]
        sep   = format[2]
        if format[0] == "d":
            screenDate = day + sep + month + sep
        else:
            screenDate = month + sep + day + sep
        if len(format) == 8:
            year = year[2:]
        screenDate = screenDate + year
        return screenDate

    def textfield_exit(self):
        "Exit from a text field with Escape"
        pass    # do nothing = don't exit
