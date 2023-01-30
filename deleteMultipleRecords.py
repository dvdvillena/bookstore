#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     deleteMultipleRecords.py - Delete multiple records (books and intermediate tables)
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import curses
import npyscreen
from npyscreen import wgwidget as widget
import config
import bsWidgets as bs
import sqlite3

TAB = "\t"
CR = "\n"

helpText =  "\nThis is a module to delete all or a range of table rows (records) from the \ndatabase.\n\n" +\
    "The database and table structure will remain the same.\n\n" +\
    "The user table will be left untouched as well.\n"


class DeleteMultipleRecordsForm(npyscreen.FormBaseNew):
    "Form for Deleting multiple records (books)."
    def __init__(self, name="DeleteMultipleRecords", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
    widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        """ Crea el padre, npyscreen.FormBaseNew. """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # Framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exitDeleteMultipleRecords   # Escape exit
        
        # Form title
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Delete Multiple Records "
        self.title = self.add(bs.MyFixedText, name="DeleteMultipleRecords", value=self.formTitle,\
            relx=2, rely=0, editable=False)  # Screen title line
        #-------------------------------------------------------------------------------------------------------------------------
        self.infoTxt = self.add(bs.MyMultiLineEdit, name="", value="", relx=13, rely=6, max_height=3, editable=False)
        info = "Warning: Multiple records will be deleted from the database.\n"
        self.infoTxt.value = info
        #-------------------------------------------------------------------------------------------------------------------------
        switchOptions = ["Empty the database", "Delete a book range","Delete an author range","Delete a publisher range","Delete a warehouse range"]
        self.deleteSwitches = self.add(bs.MyTitleSelectOne, max_height=5, value = [0,], name=" ", 
            relx=3, rely=9, width=55, max_width=55, values=switchOptions, scroll_exit=True)
        #-------------------------------------------------------------------------------------------------------------------------
        self.rangeFromFld=self.add(bs.MyTitleText, name="Delete from numeral:", value="", relx=13, rely=16, begin_entry_at=22,\
            width=31, use_two_lines=False, use_max_space=False, editable=True)
        self.rangeToFld=self.add(bs.MyTitleText, name="to numeral:", value="", relx=45, rely=16, begin_entry_at=13,\
            width=22, use_two_lines=False, use_max_space=False, editable=True)
        
        #-------------------------------------------------------------------------------------------------------------------------
        self.ok_button=self.add(Mi_MiniButtonPress, name="Delete records", relx=21, rely=19, editable=True)
        self.ok_button.when_pressed_function = self.DeleteRecordsbtn_function
        self.cancel_button=self.add(Mi_MiniButtonPress, name="Cancel", relx=45, rely=19, editable=True)
        self.cancel_button.when_pressed_function = self.Cancelbtn_function
        
        self.statusLine=self.add(npyscreen.FixedText, name="DeleteMultipleRecordsStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)
        self.statusLine.value = "Select options"

    def DeleteRecordsbtn_function(self):
        "Check Database button function."
        self.deleteMultipleRecords()

    def Cancelbtn_function(self):
        "Cancel button function."
        self.exitDeleteMultipleRecords()

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def check_fields_values(self):
        "Checking for wrong values in the fields."
        errorMsg = None

        if self.deleteSwitches.value[0] != 0:
            # Mandatory values check:
            emptyField = False
            if self.rangeFromFld.value == "":
                emptyField = True
                self.editw = 2
            elif self.rangeToFld.value == "":  
                emptyField = True
                self.editw = 3
            if emptyField:
                self.ok_button.editing = False
                errorMsg = "Error:  Mandatory field is empty"
                return errorMsg

            # wrong value check: rangeFrom field
            try:
                a = int(self.rangeFromFld.value)
            except ValueError:
                self.editw = 2
                self.ok_button.editing = False
                errorMsg = "Error: Numeral must be integer"
                return errorMsg

            # wrong value check: rangeTo field
            try:
                a = int(self.rangeToFld.value)
            except ValueError:
                self.editw = 3
                self.ok_button.editing = False
                errorMsg = "Error: Numeral must be integer"
                return errorMsg

            # wrong value check: range fields
            if self.rangeFromFld.value > self.rangeToFld.value:
                self.editw = 2
                self.ok_button.editing = False
                errorMsg = "Error in numerals range"
                return errorMsg

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def emptyTheDB(self):
        "Empty the whole recordset of the database."
        message = "   Do you want to empty the whole database?\n\n"
        if not bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            return False     # to the form
            
        conn = config.conn
        cur = conn.cursor()
        while True:
            try:
                conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite only allows a single writer per database
                conn.execute('PRAGMA locking_mode = EXCLUSIVE')
                conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
                break
            except sqlite3.OperationalError:
                bs.notify_OK("\n    Database is locked, please wait.", "Message")
        try:
            sqlQuery = "DELETE FROM 'bookstore.book'"
            cur.execute(sqlQuery)
            sqlQuery = "DELETE FROM 'bookstore.author'"
            cur.execute(sqlQuery)
            sqlQuery = "DELETE FROM 'bookstore.publisher'"
            cur.execute(sqlQuery)
            sqlQuery = "DELETE FROM 'bookstore.warehouse'"
            cur.execute(sqlQuery)
            sqlQuery = "DELETE FROM 'bookstore.book_author'"
            cur.execute(sqlQuery)
            sqlQuery = "DELETE FROM 'bookstore.book_warehouse'"
            cur.execute(sqlQuery)
        except sqlite3.Error as e:
            bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
        
        conn.commit()
        return True

    def deleteRecordRange(self, table, first, last):
        "Delete a record range in a specified table."
        conn = config.conn
        cur = conn.cursor()
        self.table = table
        while True:
            try:
                conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite only allows a single writer per database
                conn.execute('PRAGMA locking_mode = EXCLUSIVE')
                conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
                break
            except sqlite3.OperationalError:
                bs.notify_OK("\n    Database is locked, please wait.", "Message")

        if self.table == "book":
            tableTxt = "'bookstore.book'"
        elif self.table == "author":
            tableTxt = "'bookstore.author'"
        elif self.table == "publisher":
            tableTxt = "'bookstore.publisher'"
        elif self.table == "warehouse":
            tableTxt = "'bookstore.warehouse'"

        try:
            sqlQuery = "DELETE FROM " + tableTxt + " WHERE numeral >= " + str(first) + " AND numeral <= " + str(last)
            cur.execute(sqlQuery)
        except sqlite3.Error as e:
            bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
            return False

        if self.table == "book":
            try:
                sqlQuery = "DELETE FROM 'bookstore.book_author' WHERE book_num >= " + str(first) + " AND book_num <= " + str(last)
                cur.execute(sqlQuery)
                sqlQuery = "DELETE FROM 'bookstore.book_warehouse' WHERE book_num >= " + str(first) + " AND book_num <= " + str(last)
                cur.execute(sqlQuery)
            except sqlite3.Error as e:
                bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
        
        conn.commit()
        return True

    def deleteMultipleRecords(self):
        "Delete multiple records from the database."

        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        
        message = "   Do you really want to delete the records now?\n\n"
        if not bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            self.exitDeleteMultipleRecords()

        if self.deleteSwitches.value[0] == 0:   # Empty the database
            if self.emptyTheDB():
                bs.notify_OK("\n     Database records were deleted.\n", "Message")
            else:
                bs.notify_OK("\n     Nothing was deleted.\n", "Message")
            self.exitDeleteMultipleRecords()
        else:
            if self.deleteSwitches.value[0] == 1:
                self.table = "book"
            elif self.deleteSwitches.value[0] == 2:
                self.table = "author"
            elif self.deleteSwitches.value[0] == 3:
                self.table = "publisher"
            elif self.deleteSwitches.value[0] == 4:
                self.table = "warehouse"
            first = self.rangeFromFld.value
            last = self.rangeToFld.value

            if self.deleteRecordRange(self.table, first, last):
                bs.notify_OK("\n     Database records were deleted.\n", "Message")
            self.exitDeleteMultipleRecords()

    def exitDeleteMultipleRecords(self):

        config.last_operation = "DeleteMultipleRecords"
        if self.deleteSwitches.value[0] == 0:   # Empty the database
            self.parentApp._Forms['BOOKSELECTOR'].update_grid()
            self.parentApp._Forms['AUTHORSELECTOR'].update_grid()
            self.parentApp._Forms['PUBLISHERSELECTOR'].update_grid()
            self.parentApp._Forms['WAREHOUSESELECTOR'].update_grid()
        else:
            if self.table == "book":
                self.parentApp._Forms['BOOKSELECTOR'].update_grid()
            elif self.table == "author":
                self.parentApp._Forms['AUTHORSELECTOR'].update_grid()
            elif self.table == "publisher":
                self.parentApp._Forms['PUBLISHERSELECTOR'].update_grid()
            elif self.table == "warehouse":
                self.parentApp._Forms['WAREHOUSESELECTOR'].update_grid()

        config.parentApp.setNextForm("UTILITIES")
        config.parentApp.switchFormNow()
    

class Mi_MiniButtonPress(npyscreen.MiniButtonPress):
    # NB.  The when_pressed_function functionality is potentially dangerous. It can set up
    # a circular reference that the garbage collector will never free. 
    # If this is a risk for your program, it is best to subclass this object and
    # override when_pressed_function instead.  Otherwise your program will leak memory.
    def __init__(self, screen, when_pressed_function=None, *args, **keywords):
        super(npyscreen.MiniButtonPress, self).__init__(screen, *args, **keywords)
        self.when_pressed_function = when_pressed_function

        self.how_exited = widget.EXITED_DOWN   
    
    def set_up_handlers(self):
        super(npyscreen.MiniButtonPress, self).set_up_handlers()
        
        self.handlers.update({
                curses.ascii.NL: self.h_toggle,
                curses.ascii.CR: self.h_toggle,
            })
        
    def destroy(self):
        self.when_pressed_function = None
        del self.when_pressed_function
    
    def h_toggle(self, ch):
        self.value = True
        self.display()
        if self.when_pressed_function:
            self.when_pressed_function()
        else:
            self.whenPressed()
        self.value = False
        self.display()

    def whenPressed(self):
        pass
