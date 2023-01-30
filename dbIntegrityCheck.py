#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     dbIntegrityCheck.py - Database Integrity Check
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

TAB = "\t"
CR = "\n"

helpText =  "Check database referential integrity:\n\n" \
        "   1.For each book:\n" \
        "       author must exist\n" \
        "       publisher must exist\n" \
        "       warehouse must exist\n" \
        "   2.For each book_author:\n" \
        "       book must exist\n" \
        "       author must exist\n" \
        "   3.For each book_warehouse:\n" \
        "       book must exist\n" \
        "       warehouse must exist\n" \
        "   4.Check book_author duplicates\n" \
        "   5.Check book_warehouse duplicates\n\n" \
        " (Foreign keys' 'ON UPDATE' and 'ON DELETE' actions are disabled)"


class DBintegrityCheckForm(npyscreen.FormBaseNew):
    "Form for the DB integrity check."
    def __init__(self, name="DBIntegrityCheck", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
    widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        """ Crea el padre, npyscreen.FormBaseNew. """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # Framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exitDBintegrityCheck   # Escape exit
        
        # Form title
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Check DB Integrity "
        self.title = self.add(bs.MyFixedText, name="DBintegrityCheck", value=self.formTitle,\
            relx=2, rely=0, editable=False)  # Screen title line
        #-------------------------------------------------------------------------------------------------------------------------
        self.infoTxt = self.add(bs.MyMultiLineEdit, name="", value="", relx=13, rely=7, max_height=3, editable=False)
        info = "Database will be checked for referential integrity.\n"
        self.infoTxt.value = info
        #-------------------------------------------------------------------------------------------------------------------------
        self.ok_button=self.add(Mi_MiniButtonPress, name="Check Database", relx=21, rely=14, editable=True)
        self.ok_button.when_pressed_function = self.CheckDatabasebtn_function
        self.cancel_button=self.add(Mi_MiniButtonPress, name="Cancel", relx=45, rely=14, editable=True)
        self.cancel_button.when_pressed_function = self.Cancelbtn_function
        
        self.statusLine=self.add(npyscreen.FixedText, name="DBintegrityCheckStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)
        self.statusLine.value = "Select button"

    def CheckDatabasebtn_function(self):
        "Check Database button function."
        self.checkIntegrity()

    def Cancelbtn_function(self):
        "Cancel button function."
        self.exitDBintegrityCheck()

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def checkIntegrity(self):
        "Check database referential integrity."
        """ 1.For each book:
                author must exist
                publisher must exist
                warehouses must exist
            2.For each book_author:
                book must exist
                author must exist
            3.For each book_warehouse:
                book must exist
                warehouse must exist
            4.Check book_author duplicates
            5.Check book_warehouse duplicates
        """
        message = "   Do you want to check database now?\n   (it can take some time to complete)\n"
        if not bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            return      # to the utilities menu

        # 1.Check book -> book_author -> author
        #       book -> publisher
        #       book -> book_warehouse -> warehouse
        bs.notify("\n    Checking book -> book_author -> author\n" +
                    "    Checking book -> publisher...\n", title="Message", form_color='STANDOUT', wrap=True, wide=False,)
        conn = config.conn
        cur = conn.cursor()
        sqlQuery = "SELECT numeral, publisher_num FROM 'bookstore.book' ORDER BY id"
        cur.execute(sqlQuery)
        books = cur.fetchall()
        for book in books:
            sqlQuery = "SELECT author_num FROM 'bookstore.book_author' WHERE book_num=?"
            try:
                cur.execute(sqlQuery, (book[0],) )
                authnum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n     Book with numeral " + str(book[0]) + " has no assigned author. ", "Message")
                continue
            sqlQuery = "SELECT numeral, name FROM 'bookstore.author' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (authnum,) )
                authnum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n     Author of book with numeral " + str(book[0]) + " was not found. ", "Message")
                continue
            sqlQuery = "SELECT numeral, name FROM 'bookstore.publisher' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (book[1],) )
                publnum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n     Publisher of book with numeral " + str(book[0]) + " was not found. ", "Message")
                continue
        bs.notify("\n  Checking book -> book_warehouse -> warehouse...", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        for book in books:
            sqlQuery = "SELECT warehouse_num FROM 'bookstore.book_warehouse' WHERE book_num=?"
            cur.execute(sqlQuery, (book[0],) )
            warehouses_book = cur.fetchall()
            if len(warehouses_book) == 0:
                bs.notify_OK("\n  Book with numeral " + str(book[0]) + " has no assigned warehouse. ", "Message")
                continue
            for warehouse_book in warehouses_book:
                sqlQuery = "SELECT numeral, code FROM 'bookstore.warehouse' WHERE numeral=?"
                try:
                    cur.execute(sqlQuery, (warehouse_book[0],) )
                    whnum = cur.fetchone()[0]
                except TypeError:
                    bs.notify_OK("\n Warehouse of book with numeral " + str(book[0]) + " was not found. ", "Message")
                    continue
        # 2.Check book_author -> book
        #         book_author -> author
        bs.notify("\n  Checking book_author -> book\n" + 
                    "  Checking book_author -> author...", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        sqlQuery = "SELECT id, book_num, author_num FROM 'bookstore.book_author' ORDER BY id"
        cur.execute(sqlQuery)
        books_authors = cur.fetchall()
        for book_author in books_authors:
            sqlQuery = "SELECT numeral FROM 'bookstore.book' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (book_author[1],) )
                bknum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n  Book in book_author with id=" + str(book_author[0]) + " was not found. ", "Message")
                continue
            sqlQuery = "SELECT numeral FROM 'bookstore.author' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (book_author[2],) )
                authnum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n  Author in book_author with id=" + str(book_author[0]) + " was not found. ", "Message")
                continue
        # 3.Check book_warehouse -> book
        #         book_warehouse -> warehouse
        bs.notify("\n  Checking book_warehouse -> book\n" + 
                    "  Checking book_warehouse -> warehouse...", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        sqlQuery = "SELECT id, book_num, warehouse_num FROM 'bookstore.book_warehouse' ORDER BY id"
        cur.execute(sqlQuery)
        books_warehouses = cur.fetchall()
        for book_warehouse in books_warehouses:
            sqlQuery = "SELECT numeral FROM 'bookstore.book' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (book_warehouse[1],) )
                bknum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n  Book in book_warehouse with id=" + str(book_author[0]) + " was not found. ", "Message")
                continue
            sqlQuery = "SELECT numeral FROM 'bookstore.warehouse' WHERE numeral=?"
            try:
                cur.execute(sqlQuery, (book_warehouse[2],) )
                whnum = cur.fetchone()[0]
            except TypeError:
                bs.notify_OK("\n  Warehouse in book_warehouse with id=" + str(book_author[0]) + " was not found. ", "Message")
                continue
        # 4.Check book_author duplicates
        bs.notify("\n  Checking book_author duplicates...", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        sqlQuery = "SELECT id, book_num FROM 'bookstore.book_author' ORDER BY book_num"
        cur.execute(sqlQuery)
        books_authors = cur.fetchall()
        last_book = None
        for book_author in books_authors:
            if last_book == None:
                last_book = book_author[1]
            else:
                if book_author[1] == last_book:
                    bs.notify_OK("\n  Book in book_author with id=" + str(book_author[0]) + " is duplicated.\n" + 
                                   "  (Duplicated record will be deleted)", "Message")
                    sqlQuery = "DELETE FROM 'bookstore.book_author' WHERE id=?"
                    cur.execute(sqlQuery, (book_author[0], ) )
                    conn.commit()
                    continue
                else:
                    last_book = book_author[1]
        # 5.Check book_warehouse duplicates
        bs.notify("\n  Checking book_warehouse duplicates...", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        sqlQuery = "SELECT id, book_num, warehouse_num FROM 'bookstore.book_warehouse' ORDER BY book_num, warehouse_num"
        cur.execute(sqlQuery)
        books_warehouses = cur.fetchall()
        last_book = None
        last_warehouse = None
        for book_warehouse in books_warehouses:
            if last_book == None:
                last_book = book_warehouse[1]
                last_warehouse = book_warehouse[2]
                continue
            else:
                if book_warehouse[1] == last_book:
                    if book_warehouse[2] == last_warehouse:
                        bs.notify_OK("\n  Book in book_warehouse with id=" + str(book_warehouse[0]) + " is duplicated.\n" + 
                                       "  (Duplicated record will be deleted)", "Message")
                        sqlQuery = "DELETE FROM 'bookstore.book_warehouse' WHERE id=?"
                        cur.execute(sqlQuery, (book_warehouse[0],) )
                        conn.commit()
                        continue
                else:
                    last_book = book_warehouse[1]
                    last_warehouse = book_warehouse[2]

        bs.notify_OK("\n     Database integrity check finished.\n", "Message")
        self.exitDBintegrityCheck()

    def exitDBintegrityCheck(self):
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
