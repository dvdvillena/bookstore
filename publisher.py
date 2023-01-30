#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     publisher.py - Publisher record form
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import curses
import sqlite3
import time

import npyscreen

import bsWidgets as bs
import config

DATEFORMAT = config.dateFormat
DBTABLENAME = "'bookstore.Publisher'"

global form

helpText = "Another record form screen for the publishers.\n\n" \
    "* There is not much more to add to what has already been said about the other record forms. " \
    "Please see the Books and Authors help screens.\n\n"


class PublisherForm(npyscreen.FormBaseNew):
    "Publisher record on screen for maintenance."
    def __init__(self, name="Publisher", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
        widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        # Creates the father, npyscreen.FormBaseNew.
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

        global form
        form = self

        self.selectorForm = self.parentApp._Forms['PUBLISHERSELECTOR']

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_publisher   # Escape exit
        
        # Form title
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Publisher record "
        self.formTitleFld=self.add(bs.MyFixedText, name="PublisherTitle", value=self.formTitle, relx=2, rely=0, editable=False)  # Screen title line

        # Form fields
        self.numeralFld=self.add(bs.MyTitleText, name="Numeral:", value="", relx=9, rely=5, begin_entry_at=11, editable=False)
        self.nameFld=self.add(bs.MyTitleText, name="Name:", value="", relx=9, rely=7, begin_entry_at=11, editable=False)
        self.addressFld=self.add(bs.MyTitleText, name="Address:", value="", relx=9, rely=9, begin_entry_at=11, fixed_length=False, editable=False)
        self.phoneFld=self.add(bs.MyTitleText, name="Phone:", value="", relx=9, rely=11, begin_entry_at=11, editable=False)
        self.urlFld=self.add(bs.MyTitleText, name="URL:", value="", relx=9, rely=13, begin_entry_at=11, fixed_length=False, editable=False)

        # Form buttons
        self.ok_button=self.add(bs.MyMiniButtonPress, name="  OK  ", relx=26, rely=19, editable=True)
        self.cancel_button=self.add(bs.MyMiniButtonPress, name="Cancel", relx=42, rely=19, editable=True)

        # Status line
        self.statusLine=self.add(bs.MyFixedText, name="PublisherStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)

    def backup_fields(self):
        self.bu_numeral = self.numeralFld.value
        self.bu_name = self.nameFld.value
        self.bu_address = self.addressFld.value
        self.bu_phone = self.phoneFld.value
        self.bu_url = self.urlFld.value

    def update_fileRow(self):
        "Updates config.fileRow."
        if self.current_option != "Delete":
            id = config.fileRow[0]
            for row in config.fileRows:
                if row[0] == id:
                    config.fileRow = []
                    config.fileRow.append(row[0])
                    config.fileRow.append(int(self.numeralFld.value))
                    config.fileRow.append(self.nameFld.value)
                    config.fileRow.append(self.addressFld.value)
                    config.fileRow.append(self.phoneFld.value)
                    config.fileRow.append(self.urlFld.value)
                    break

    def exit_publisher(self):
        "Only for escape-exit, handler version."
        self.exitPublisher(modified=False)

    def exitPublisher(self, modified):
        "Exit record form."
        if modified:    # modify grid if needed
            self.update_fileRow()
            self.selectorForm.update_grid()
            self.backup_fields()
        self.selectorForm.grid.update()

        # To unlock the database (for Create) we must disconnect and re-connect:
        config.conn.close()
        self.parentApp.connect_database()

        config.parentApp.setNextForm("PUBLISHERSELECTOR")
        config.parentApp.switchFormNow()

    def get_last_numeral(self):
        "Get the last numeral from the database."
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
        "Setting the publisher form to create a new record."
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
        form.nameFld.editable = True
        form.nameFld.value = ""
        form.addressFld.editable = True
        form.addressFld.value = ""
        form.phoneFld.editable = True
        form.phoneFld.value = ""
        form.urlFld.editable = True
        form.urlFld.value = ""
        form.ok_button.when_pressed_function = form.createOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.createCancelbtn_function
        form.statusLine.value = "Creating a new record"
        form.backup_fields()
        form.editw = form.get_editw_number("Name:")
        config.last_operation = "Create"

    def set_readOnlyMode():
        "Setting the publisher form for read only display."
        global form
        form.current_option = "Read"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.nameFld.editable = False
        form.addressFld.editable = False
        form.phoneFld.editable = False
        form.urlFld.editable = False
        form.ok_button.when_pressed_function = form.readOnlyOKbtn_function
        form.ok_button.name = "OK"  # name changes between calls
        form.cancel_button.when_pressed_function = form.readOnlyCancelbtn_function
        form.statusLine.value = "Read-Only mode"
        form.editw = form.get_editw_number("OK")
        config.last_operation = "Read"

    def set_updateMode():
        "Setting the publisher form for update editing."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.current_option = "Update"
        form.convertDBtoFields()
        form.numeralFld.editable = True
        form.numeralFld.maximum_string_length = 3
        form.nameFld.editable = True
        form.addressFld.editable = True
        form.phoneFld.editable = True
        form.urlFld.editable = True
        form.ok_button.when_pressed_function = form.updateOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.updateCancelbtn_function
        form.statusLine.value = "Update mode: editing record"
        form.backup_fields()
        form.editw = form.get_editw_number("Name:")
        config.last_operation = "Update"

    def set_deleteMode():
        "Setting the publisher form for deleting."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.current_option = "Delete"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.nameFld.editable = False
        form.addressFld.editable = False
        form.phoneFld.editable = False
        form.urlFld.editable = False
        form.ok_button.when_pressed_function = form.deleteOKbtn_function
        form.ok_button.name = "Delete"
        form.cancel_button.when_pressed_function = form.deleteCancelbtn_function
        form.statusLine.value = "Delete mode"
        form.editw = form.get_editw_number("Delete")
        config.last_operation = "Delete"

    def convertDBtoFields(self):
        "Convert DB fields into screen fields (strings)."
        self.numeralFld.value = str(config.fileRow[1])
        self.nameFld.value = config.fileRow[2]
        self.addressFld.value = config.fileRow[3]
        self.phoneFld.value = config.fileRow[4]
        self.urlFld.value = config.fileRow[5]

    def strip_fields(self):
        "Required trimming of leading and trailing spaces."
        self.numeralFld.value = self.numeralFld.value.strip()
        self.nameFld.value = self.nameFld.value.strip()
        self.addressFld.value = self.addressFld.value.strip()
        self.phoneFld.value = self.phoneFld.value.strip()
        self.urlFld.value = self.urlFld.value.strip()
    
    def save_mem_record(self):
        "Save new record (from Create) in global variable."
        config.fileRow = []
        config.fileRow.append(None)    # ID field is incremental, fulfilled later
        config.fileRow.append(int(self.numeralFld.value))
        config.fileRow.append(self.nameFld.value)
        config.fileRow.append(self.addressFld.value)
        config.fileRow.append(self.phoneFld.value)
        config.fileRow.append(self.urlFld.value)
    
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
                self.save_created_publisher()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.exitPublisher(modified=False)

    def createCancelbtn_function(self):
        "Cancel button function under Create mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard creation?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitPublisher(modified=False)
        else:
            self.exitPublisher(modified=False)
   
    def readOnlyOKbtn_function(self):
        "OK button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitPublisher(modified=False)

    def readOnlyCancelbtn_function(self):
        "Cancel button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitPublisher(modified=False)

    def delete_publisher(self):
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
        self.exitPublisher(modified=True)

    def deleteOKbtn_function(self):
        "OK button function under Delete mode."
        # You cannot delete a publisher if it's in a book record
        conn = config.conn
        cur = conn.cursor()
        num = config.fileRow[1]
        sqlQuery = "SELECT id FROM 'bookstore.book' WHERE publisher_num = ?"
        cur.execute(sqlQuery, (str(num),) )
        try:
            id = cur.fetchone()[0]
        except TypeError:   # there are no rows
            id = None
        config.conn.commit()
        if id :
            pronoun = config.gender_neutral_pronoun.lower()
            bs.notify_OK("\n   You cannot delete this publisher because \n"+ "    " +\
                pronoun + " is listed in a book.\n", "Error")
            self.exitPublisher(modified=False)
        else:    # no books
            # Ask for confirmation to delete
            message = "\n   Select OK to confirm deletion"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.delete_publisher()
                try:
                    numeral = config.fileRow[1]
                except IndexError:  # there are no rows in the table
                    numeral = None
                self.selectorForm.grid.set_highlight_row(numeral)
            else:
                self.exitPublisher(modified=False)

    def deleteCancelbtn_function(self):
        "Cancel button function under Delete mode."
        bs.notify("\n   Record was NOT deleted", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        time.sleep(0.4)     # let it be seen
        self.exitPublisher(modified=False)

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
        elif self.nameFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("Name:") - 1
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
            errorMsg = "Error: Numeral must be integer"
            return errorMsg
        if len(self.numeralFld.value) > self.numeralFld.maximum_string_length:
            self.editw = self.get_editw_number("Numeral:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: Numeral maximum length exceeded"
            return errorMsg

        # repeated value check: numeral and name fields
        if self.numeralFld.value != self.bu_numeral or self.nameFld.value != self.bu_name:
            for row in config.fileRows:
                self.ok_button.editing = False
                # Already exists and it's not itself
                if row[1] == int(self.numeralFld.value) and self.numeralFld.value != self.bu_numeral:
                    self.editw = self.get_editw_number("Numeral:") - 1
                    errorMsg = "Error:  Numeral already exists"
                    return errorMsg
                # Already exists and it's not itself
                if row[2] == self.nameFld.value and self.nameFld.value != self.bu_name:
                    self.editw = self.get_editw_number("Name:") - 1
                    errorMsg = "Error:  Name already exists"
                    return errorMsg

    def exist_changes(self):
        "Checking for changes to the fields."
        exist_changes = False
        if self.numeralFld.value != self.bu_numeral or self.nameFld.value != self.bu_name or \
            self.addressFld.value != self.bu_address or self.phoneFld.value != self.bu_phone or \
            self.urlFld.value != self.bu_url:
            exist_changes = True
        return exist_changes    

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def save_created_publisher(self):
        "Button based Save function for C=Create."
        conn = config.conn
        cur = conn.cursor()
        sqlQuery = "INSERT INTO " + DBTABLENAME + " (numeral,name,address,phone,url) VALUES (?,?,?,?,?)"
        values = (self.numeralFld.value, self.nameFld.value, self.addressFld.value, self.phoneFld.value, self.urlFld.value)
        cur.execute(sqlQuery, values)
        conn.commit()
        conn.isolation_level = None     # free the multiuser lock
        config.fileRow[0] = cur.lastrowid
        bs.notify("\n       Record created", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        # update config.fileRows:
        new_record = []
        new_record.append(config.fileRow[0])    # id
        new_record.append(int(self.numeralFld.value))
        new_record.append(self.nameFld.value)
        new_record.append(self.addressFld.value)
        new_record.append(self.phoneFld.value)
        new_record.append(self.urlFld.value)
        config.fileRows.append(new_record)
        self.exitPublisher(modified=True)

    def save_updated_publisher(self):
        "Button based Save function for U=Update."

        cur = config.conn.cursor()

        # Change all the book.publisher_num's
        if self.numeralFld.value != self.bu_numeral:
            sqlQuery = "UPDATE 'bookstore.book' SET publisher_num=? WHERE publisher_num=?"
            values = (self.numeralFld.value, self.bu_numeral)
            cur.execute(sqlQuery, values)
            config.conn.commit()

        # Update publisher record
        sqlQuery = "UPDATE " + DBTABLENAME + " SET numeral=?, name=?, address=?, phone=?, url=? WHERE id=?"
        values = (self.numeralFld.value, self.nameFld.value, self.addressFld.value, self.phoneFld.value, self.urlFld.value, config.fileRow[0])
        try:
            cur.execute(sqlQuery, values)
            config.conn.commit()
        except sqlite3.IntegrityError:
            bs.notify_OK("\n     Numeral or name of publisher already exists. ", "Message")
            return

        bs.notify("\n       Record saved", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        self.exitPublisher(modified=True)
        
    def updateOKbtn_function(self):
        "OK button function under Update mode."
        self.strip_fields()     # Get rid of spaces
        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        else:
            if self.exist_changes():
                self.save_updated_publisher()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
                self.exitPublisher(modified=False)

    def updateCancelbtn_function(self):
        "Cancel button function under Update mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard changes?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitPublisher(modified=False)
        else:
            self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            self.exitPublisher(modified=False)

    def textfield_exit(self):
        "Exit from a text field with Escape"
        pass    # do nothing = don't exit
