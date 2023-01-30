#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     book.py - Book record form
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import curses
import decimal
import locale
import sqlite3
import time
from decimal import Decimal

import icu
import npyscreen

import bsWidgets as bs
import config

DATEFORMAT = config.dateFormat
DBTABLENAME = "'bookstore.book'"

global form

helpText =  "The book form is a typical record selector form.\n\n" +\
    "* The text input fields, like 'Title' now accept most of the characters used in Western languages.\n\n" \
    "* New autocomplete fields, like 'Author' are available. They are suffixed by a [+] mark. These fields " \
    "are designed to accept a predefined range of values, and in the case of 'Author', it can also " \
    "programmatically expand that range. The plus (+) key displays a popup list of values available. " \
    "They can be stored in a list variable or they can be read from a DB table, as in this case. " \
    "They can be automatically prefixed by a number or not, and they are 'called' into the input field " \
    "by alphabetical elimination. Note the correct sorting of the accented names in the popup list.\n" \
    "If you ask for the values list, you'll be warned to choose a correct value, but you can write a new " \
    "one, i.e. a new author, and it will be added to the authors table. As the author is mandatory, " \
    "you cannot leave it empty.\n\n" \
    "* 'Public. year' is a year field that accepts the minus sign (to the left, thank you).\n\n" \
    "* Both 'Genre' and 'Cover type' are autocomplete fields, filled by simply pressing a number. " \
    "Internally, only the numerical value is stored in the database.\n\n" \
    "* 'Warehouses' is an enumeration autocomplete field, it manages a comma-separated list of predefined values. " \
    "The rationale of a book being in several warehouses is that you can have more than one copy.\n\n" \
    "* 'Price' is a money field, designed to accept digits and point/comma."


class BookForm(npyscreen.FormBaseNew):
    "Book record on screen for maintenance."
    def __init__(self, name="Book", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
        widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        # Creates the father, npyscreen.FormBaseNew.
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

        global form
        form = self

        self.selectorForm = self.parentApp._Forms['BOOKSELECTOR']

    def create(self):
        "The standard constructor will call the method .create(), which you should override to create the Form widgets."
        self.framed = True   # framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_book   # Escape exit
        
        # Form title

        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Book record "
        self.formTitleFld=self.add(bs.MyFixedText, name="BookTitle", value=self.formTitle, relx=2, rely=0, editable=False)  # Screen title line

        # Form fields

        self.numeralFld=self.add(bs.MyTitleText, name="Numeral:", value="", relx=10, rely=4, begin_entry_at=15, editable=False)

        self.bookTitleFld=self.add(bs.MyTitleText, name="Title:", value="", relx=10, rely=5, begin_entry_at=15, \
            fixed_length=False, editable=False)
        self.originalTitleFld=self.add(bs.MyTitleText, name="Orig. title:", value="", relx=10, rely=6, \
            begin_entry_at=15, fixed_length=False, editable=False)

        self.authorValues = self.get_all_authors()
        self.authorFld=self.add(bs.TitleChooser, name="Author:", value="", values=self.authorValues, popupType="narrow", \
            relx=10, rely=7, width=6, min_width=8, max_width=49, begin_entry_at=15, use_max_space=False, use_two_lines=False,\
            height=0, max_height=0, check_value_change=True, editable=False)
        self.authorLabel=self.add(bs.MyFixedText, name="AuthorLabel", value="[+]", relx=58, rely=7, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)

        self.descriptionFld=self.add(bs.MyTitleText, name="Description:", value="", relx=10, rely=8, begin_entry_at=15, editable=False)
        
        self.isbnFld=self.add(bs.MyTitleText, name="ISBN/SKU:", value="", relx=10, rely=9, begin_entry_at=15, editable=False)

        self.yearFld=self.add(bs.MyTitleYear, name="Public. year:", value="", relx=10, rely=10, begin_entry_at=15, 
            width=22, max_width=22, use_max_space=False, use_two_lines=False, editable=False)

        self.publisherValues = self.get_all_publishers()
        self.publisherFld=self.add(bs.TitleChooser, name="Publisher:", value="", values=self.publisherValues, popupType="narrow", \
            relx=10, rely=11, width=6, min_width=8, max_width=49, begin_entry_at=15, use_max_space=False, use_two_lines=False,\
            height=0, max_height=0, check_value_change=True, editable=False)
        self.publisherLabel=self.add(bs.MyFixedText, name="PublisherLabel", value="[+]", relx=58, rely=11, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)

        self.creationDateFld=self.add(bs.TitleDateField, name="Creation date:", value="", format=DATEFORMAT, 
            relx=10, rely=12, begin_entry_at=15, editable=False)

        self.genreValues = config.genreList
        self.genreFld=self.add(bs.TitleChooser, name="Genre:", value="", values=self.genreValues, popupType="narrow",\
            relx=10, rely=13, begin_entry_at=15, use_max_space=False, max_width=30, editable=False)
        self.genreLabel=self.add(bs.MyFixedText, name="GenreLabel", value="[+]", relx=58, rely=13, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)

        self.coverTypeValues = config.coverTypeList

        self.coverTypeFld=self.add(bs.TitleChooser, name="Cover type:", value="", values=self.coverTypeValues, popupType="narrow",\
            relx=10, rely=14, begin_entry_at=15, use_max_space=False, max_width=49, editable=False)
        self.coverTypeLabel=self.add(bs.MyFixedText, name="CoverTypeLabel", value="[+]", relx=58, rely=14, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)

        self.warehousesValues = self.get_all_warehouses()
        self.warehousesFld=self.add(bs.TitleChooser, name="Warehouses:", value="", values=self.warehousesValues, popupType="narrow", \
            relx=10, rely=15, width=6, min_width=8, max_width=49, begin_entry_at=15, use_max_space=False, use_two_lines=False,\
            height=0, max_height=0, check_value_change=True, editable=False)
        self.warehousesLabel=self.add(bs.MyFixedText, name="WarehousesLabel", value="[+]", relx=58, rely=15, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)

        self.priceLabel = "Price " + config.currency_symbol + ":"
        self.ndecimals = config.ndecimals
        self.priceFld=self.add(bs.MyTitleMoney, name=self.priceLabel, value="", relx=15, rely=17, width=20, max_width=20, height=0, \
            begin_entry_at=10, use_max_space=False, use_two_lines=False, ndecimals=self.ndecimals, fixed_length=True, editable=False)

        # Form buttons

        self.ok_button=self.add(bs.MyMiniButtonPress, name="  OK  ", relx=26, rely=20, editable=True)
        self.cancel_button=self.add(bs.MyMiniButtonPress, name="Cancel", relx=42, rely=20, editable=True)

        # Status line

        self.statusLine=self.add(npyscreen.FixedText, name="BookStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)

    def reload(self):
        ".init and .create functions are only executed once. We need a function to execute every time we come from main_menu->selector."
        # Reload authors into the chooser field
        self.authorValues = self.get_all_authors()
        chooser = self.authorFld.entry_widget
        chooser.load_values(self.authorValues)
        self.authorFld.update(clear=True)
        # Reload publishers into the chooser field
        self.publisherValues = self.get_all_publishers()
        chooser = self.publisherFld.entry_widget
        chooser.load_values(self.publisherValues)
        self.publisherFld.update(clear=True)
        chooser = self.warehousesFld.entry_widget
        chooser.load_values(self.warehousesValues)

    def get_all_authors(self):
        "Returns a list of authors from DB"
        conn = config.conn
        cur = conn.cursor()
        cur.execute("SELECT name FROM 'bookstore.Author' ORDER BY name")
        filerows = cur.fetchall()
        author_list = []
        for row in filerows:
            author_list.append((row[0],))    # authors = [('literal',)]
        # We need PyICU (=icu) to order unicode strings in Spanish, Catalan, French...
        collator = icu.Collator.createInstance(icu.Locale(locale.getlocale()[0]))
        aux_list = [i[0] for i in author_list]
        aux_list.sort(key=collator.getSortKey)
        author_list = [(i,) for i in aux_list]
        return author_list
        
    def get_all_publishers(self):
        "Returns a list of publishers from DB"
        conn = config.conn
        cur = conn.cursor()
        cur.execute("SELECT numeral, name FROM 'bookstore.Publisher' ORDER BY name")
        filerows = cur.fetchall()
        publisher_list = []
        publisher_dict = {}
        for row in filerows:
            numeral = row[0]
            name = row[1]
            publisher_list.append(name)
            publisher_dict[name] = numeral 
        # We need PyICU (=icu) to order unicode strings in spanish+catalan
        collator = icu.Collator.createInstance(icu.Locale(locale.getlocale()[0]))
        aux_list = [i for i in publisher_list]
        aux_list.sort(key=collator.getSortKey)

        publisher_list = [(publisher_dict[i],i) for i in aux_list]
        
        return publisher_list

    def get_all_warehouses(self):
        "Gets and returns all warehouses from the database."
        conn = config.conn
        cur = conn.cursor()
        cur.execute("SELECT code FROM 'bookstore.Warehouse' ORDER BY code")
        filerows = cur.fetchall()
        # We need PyICU (=icu) to order unicode strings in spanish+catalan
        collator = icu.Collator.createInstance(icu.Locale(locale.getlocale()[0]))
        aux_list = [i[0] for i in filerows]
        aux_list.sort(key=collator.getSortKey)
        wh_list = [(i,) for i in aux_list]
        return wh_list

    def get_book_warehouses(self):
        "Read all the warehouses of this book."
        conn = config.conn
        cur = conn.cursor()
        book_num = self.numeralFld.value
        sqlQuery = "SELECT warehouse_num FROM 'bookstore.book_warehouse' WHERE book_num=? ORDER BY warehouse_num"
        cur.execute(sqlQuery, (book_num,) )
        filerows = cur.fetchall()
        warehousesField = self.set_warehouses_field(filerows)
        return warehousesField

    def set_warehouses_field(self, filerows):
        "Sets a string enumerating the warehouse(s) code(s) of this book."
        conn = config.conn
        cur = conn.cursor()
        whList = []
        count = 0
        for wh in filerows:
            sqlQuery = "SELECT code FROM 'bookstore.warehouse' WHERE numeral=? ORDER BY numeral"
            cur.execute(sqlQuery, ( str(wh[0]),) )
            try:
                filerow = cur.fetchone()
                whList.append(filerow)
            except TypeError:
                bs.notify_OK("\n     Publisher of numeral " + str(wh[0]) + " was not found. ", "Message")

        fieldString = ""
        for wh in whList:
            if count > 0:
                fieldString += ", "
            count += 1
            fieldString += wh[0]
        
        return fieldString

    def backup_fields(self):
        "Fill backup variables"
        self.bu_numeral = self.numeralFld.value
        self.bu_bookTitle = self.bookTitleFld.value
        self.bu_originalTitle = self.originalTitleFld.value
        self.bu_author = self.authorFld.value
        self.bu_description = self.descriptionFld.value
        self.bu_isbn = self.isbnFld.value
        self.bu_year = self.yearFld.value
        self.bu_publisher = self.publisherFld.value  
        self.bu_creationDate = self.creationDateFld.value  
        self.bu_genre = self.genreFld.value  
        self.bu_coverType = self.coverTypeFld.value  
        self.bu_warehouses = self.warehousesFld.value  
        self.bu_price = self.priceFld.value  

    def update_fileRow(self):
        "Updates accessible record variable."
        if self.current_option != "Delete":
            id = config.fileRow[0]
            for row in config.fileRows:
                if row[0] == id:
                    config.fileRow = []
                    config.fileRow.append(row[0])
                    config.fileRow.append(int(self.numeralFld.value))
                    config.fileRow.append(self.bookTitleFld.value)
                    config.fileRow.append(self.originalTitleFld.value)
                    config.fileRow.append(self.authorFld.value)
                    config.fileRow.append(self.descriptionFld.value)
                    config.fileRow.append(self.isbnFld.value)
                    config.fileRow.append(self.yearFld.value)
                    config.fileRow.append(self.publisherFld.value)
                    config.fileRow.append(self.creationDateFld.value)
                    config.fileRow.append(self.genreFld.value)
                    config.fileRow.append(self.coverTypeFld.value)
                    price = self.priceFld.value.replace(",", ".")   # here, no matter config.decimal_symbol
                    config.fileRow.append(Decimal(price))
                    break
        elif self.current_option == "Delete":
            pass

    def exit_book(self):
        "Only for escape-exit, handler version."
        self.exitBook(modified=False)

    def exitBook(self, modified):
        "Exit record form."
        if modified:    # modify grid if needed
            self.update_fileRow()
            self.selectorForm.update_grid()
            self.backup_fields()
        self.selectorForm.grid.update()

        # To unlock the database (for Create) we must disconnect and re-connect:
        config.conn.close()
        self.parentApp.connect_database()

        config.parentApp.setNextForm("BOOKSELECTOR")
        config.parentApp.switchFormNow()

    def get_last_numeral(self, table_name):
        "Get the last numeral in the table."
        cur = config.conn.cursor()
        sqlQuery = "SELECT Numeral FROM " + table_name + " ORDER BY Numeral DESC LIMIT 1"
        cur.execute(sqlQuery)
        try:
            numeral = cur.fetchone()[0]
        except TypeError:   # there are no rows
            numeral = 0
        return numeral

    def set_createMode():
        "Setting the book form to create a new record."
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
        form.reload()   # reloading chooser fields, etc in case we've changed the other tables
        form.current_option = "Create"
        form.numeralFld.editable = True
        form.numeralFld.maximum_string_length = 6
        form.numeralFld.value = str(form.get_last_numeral(DBTABLENAME) + 1)
        form.bookTitleFld.editable = True
        form.bookTitleFld.value = ""
        form.originalTitleFld.editable = True
        form.originalTitleFld.value = ""
        form.authorFld.editable = True
        form.authorFld.value = ""
        form.descriptionFld.editable = True
        form.descriptionFld.value = ""
        form.isbnFld.editable = True
        form.isbnFld.value = ""
        form.yearFld.editable = True
        form.yearFld.value = ""
        form.publisherFld.editable = True
        form.publisherFld.value = ""
        form.creationDateFld.editable = True
        form.creationDateFld.value = form.selectorForm.today
        form.genreFld.editable = True
        form.genreFld.value = ""
        form.coverTypeFld.editable = True
        form.coverTypeFld.value = ""
        form.warehousesFld.editable = True
        form.warehousesFld.value = ""
        form.priceFld.editable = True
        form.priceFld.value = ""
        form.priceFld.maximum_string_length = 8
        form.ok_button.when_pressed_function = form.createOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.createCancelbtn_function
        form.statusLine.value = "Creating a new record"
        form.backup_fields()
        form.editw = form.get_editw_number("Title:")
        config.last_operation = "Create"

    def set_readOnlyMode():
        "Setting the book form for read only display."
        global form
        form.current_option = "Read"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.bookTitleFld.editable = False
        form.originalTitleFld.editable = False
        form.authorFld.editable = False
        form.descriptionFld.editable = False
        form.isbnFld.editable = False
        form.yearFld.editable = False
        form.publisherFld.editable = False
        form.creationDateFld.editable = False
        form.genreFld.editable = False
        form.coverTypeFld.editable = False
        form.warehousesFld.value = form.get_book_warehouses()
        form.warehousesFld.editable = False
        form.priceFld.editable = False
        form.ok_button.when_pressed_function = form.readOnlyOKbtn_function
        form.ok_button.name = "OK"  # name changes between calls
        form.cancel_button.when_pressed_function = form.readOnlyCancelbtn_function
        form.statusLine.value = "Read-Only mode"
        form.editw = form.get_editw_number("OK")
        config.last_operation = "Read"

    def set_updateMode():
        "Setting the book form for update editing."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.reload()   # reloading chooser fields, etc in case we've changed other tables
        form.current_option = "Update"
        form.convertDBtoFields()
        form.numeralFld.editable = True
        form.numeralFld.maximum_string_length = 6
        form.bookTitleFld.editable = True
        form.originalTitleFld.editable = True
        form.authorFld.editable = True
        form.descriptionFld.editable = True
        form.isbnFld.editable = True
        form.isbnFld.maximum_string_length = 17     # Four hyphens included
        form.yearFld.editable = True
        form.yearFld.maximum_string_length = 5      # 4 digits + minus sign
        form.publisherFld.editable = True
        form.creationDateFld.editable = True
        form.genreFld.editable = True
        form.coverTypeFld.editable = True
        form.warehousesFld.editable = True
        form.warehousesFld.value = form.get_book_warehouses()
        form.priceFld.editable = True
        form.priceFld.maximum_string_length = 8
        form.ok_button.when_pressed_function = form.updateOKbtn_function
        form.ok_button.name = "Save"  # name changes between calls
        form.cancel_button.when_pressed_function = form.updateCancelbtn_function
        form.statusLine.value = "Update mode: editing record"
        form.backup_fields()
        form.editw = form.get_editw_number("Title:")
        config.last_operation = "Update"

    def set_deleteMode():
        "Setting the book form for deleting."
        global form
        conn = config.conn
        conn.isolation_level = 'EXCLUSIVE'  # Database locking: SQLite3 admits just one writing process
        conn.execute('BEGIN EXCLUSIVE TRANSACTION')     # exclusive access starts here. Nothing else can r/w the DB.
        form.current_option = "Delete"
        form.convertDBtoFields()
        form.numeralFld.editable = False
        form.bookTitleFld.editable = False
        form.originalTitleFld.editable = False
        form.authorFld.editable = False
        form.descriptionFld.editable = False
        form.isbnFld.editable = False
        form.yearFld.editable = False
        form.publisherFld.editable = False
        form.creationDateFld.editable = False
        form.genreFld.editable = False
        form.coverTypeFld.editable = False
        form.warehousesFld.value = form.get_book_warehouses()
        form.warehousesFld.editable = False
        form.priceFld.editable = False
        form.ok_button.when_pressed_function = form.deleteOKbtn_function
        form.ok_button.name = "Delete"
        form.cancel_button.when_pressed_function = form.deleteCancelbtn_function
        form.statusLine.value = "Delete mode"
        form.editw = form.get_editw_number("Delete")
        config.last_operation = "Delete"

    def convertDBtoFields(self):
        "Convert DB fields into screen fields (strings)."
        self.numeralFld.value = str(config.fileRow[1])
        self.bookTitleFld.value = config.fileRow[2]
        self.originalTitleFld.value = config.fileRow[3]
        self.authorFld.value = self.selectorForm.get_author_name(config.fileRow[1])
        self.descriptionFld.value = config.fileRow[5]
        self.isbnFld.value = config.fileRow[6]
        self.yearFld.value = str(config.fileRow[7])
        self.publisherFld.value = config.fileRow[8]
        self.creationDateFld.value = self.DBtoScreenDate(config.fileRow[9], DATEFORMAT)
        self.genreFld.value = str(config.fileRow[10])+"-"+self.genreValues[config.fileRow[10] - 1]
        self.coverTypeFld.value = str(config.fileRow[11])+"-"+self.coverTypeValues[config.fileRow[11] - 1]
        price = str(config.fileRow[12])
        if config.decimal_symbol == ",":
            price = price.replace(".", ",")     # screen value only
        self.priceFld.value = price

    def strip_fields(self):
        "Required trimming of leading and trailing spaces."
        self.numeralFld.value = self.numeralFld.value.strip()
        self.bookTitleFld.value = self.bookTitleFld.value.strip()
        self.originalTitleFld.value = self.originalTitleFld.value.strip()
        self.authorFld.value = self.authorFld.value.strip()
        self.descriptionFld.value = self.descriptionFld.value.strip()
        self.isbnFld.value = self.isbnFld.value.strip()
        self.yearFld.value = self.yearFld.value.strip()
        self.publisherFld.value = self.publisherFld.value.strip()
        self.creationDateFld.value = self.creationDateFld.value.strip()
        self.genreFld.value = self.genreFld.value.strip()
        self.coverTypeFld.value = self.coverTypeFld.value.strip()
        self.priceFld.value = self.priceFld.value.strip()
    
    def save_mem_record(self):
        "Save new record (from Create) to global variable."
        config.fileRow = []
        config.fileRow.append(None)    # ID field is incremental, fulfilled later
        config.fileRow.append(int(self.numeralFld.value))
        config.fileRow.append(self.bookTitleFld.value)
        config.fileRow.append(self.originalTitleFld.value)
        config.fileRow.append(self.authorFld.value)
        config.fileRow.append(self.descriptionFld.value)
        config.fileRow.append(self.isbnFld.value)
        config.fileRow.append(int(self.yearFld.value))
        config.fileRow.append(self.publisherFld.value)
        config.fileRow.append(self.creationDateFld.value)
        config.fileRow.append(self.genreFld.value)
        config.fileRow.append(self.coverTypeFld.value)
        ctx = decimal.getcontext()
        ctx.prec = 6
        ctx.rounding = decimal.ROUND_HALF_DOWN  # rounds if enters more than self.ndecimals decimals
        price = self.priceFld.value.replace(",", ".")   # here, no matter config.decimal_symbol
        price = str(round(Decimal(price), self.ndecimals))
        config.fileRow.append(Decimal(price))
    
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
                self.save_created_book()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.exitBook(modified=False)

    def createCancelbtn_function(self):
        "Cancel button function under Create mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard creation?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitBook(modified=False)
        else:
            self.exitBook(modified=False)
   
    def readOnlyOKbtn_function(self):
        "OK button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitBook(modified=False)

    def readOnlyCancelbtn_function(self):
        "Cancel button function under Read mode."
        self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
        self.exitBook(modified=False)

    def delete_book(self):
        "Button based Delete function for D=Delete."

        conn = config.conn
        cur = conn.cursor()
        id = config.fileRow[0]
        numeral = config.fileRow[1]

        # Delete book record
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
        
        # Delete book_author relationship table row(s)
        sqlQuery = "DELETE FROM 'bookstore.book_author' WHERE book_num = " + str(numeral)
        cur.execute(sqlQuery)
        conn.commit()

        # Delete book_warehouse relationship table row(s)
        sqlQuery = "DELETE FROM 'bookstore.book_warehouse' WHERE book_num = " + str(numeral)
        cur.execute(sqlQuery)
        conn.commit()

        self.exitBook(modified=True)

    def deleteOKbtn_function(self):
        "OK button function under Delete mode."
        # Ask for confirmation to delete
        message = "\n   Select OK to confirm deletion"
        if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            self.delete_book()
            try:
                numeral = config.fileRow[1]
            except IndexError:  # there are no rows in the table
                numeral = None
            self.selectorForm.grid.set_highlight_row(numeral)
        else:
            self.exitBook(modified=False)

    def deleteCancelbtn_function(self):
        "Cancel button function under Delete mode."
        bs.notify("\n   Record was NOT deleted", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        time.sleep(0.4)     # let it be seen
        self.exitBook(modified=False)

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
        elif self.bookTitleFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("Title:") - 1
        elif self.authorFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("Author:") - 1
        elif self.isbnFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("ISBN/SKU:") - 1
        elif self.yearFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("Public. year:") - 1
        elif self.publisherFld.value == "":  
            emptyField = True
            self.editw = self.get_editw_number("Publisher:") - 1
        elif self.creationDateFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Creation date:") - 1
        elif self.genreFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Genre:") - 1
        elif self.coverTypeFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Cover type:") - 1
        elif self.priceFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number(self.priceLabel) - 1
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

        # wrong value check: year field
        try:
            a = int(self.yearFld.value)     # includes negative years
        except ValueError:
            self.editw = self.get_editw_number("Public. year:") - 1
            self.ok_button.editing = False
            errorMsg = "Error: Year must be integer"
            return errorMsg

        # wrong date check:
        if not self.creationDateFld.check_value_is_ok():
            self.ok_button.editing = False
            self.editw = self.get_editw_number("Creation date:") - 1
            errorMsg = "Error: Incorrect date; format is "+self.creationDateFld.format
            return errorMsg

        # wrong value check: price field
        price = self.priceFld.value.replace(",", ".")   # here, no matter config.decimal_symbol
        try:
            ctx = decimal.getcontext()
            ctx.prec = 6
            ctx.rounding = decimal.ROUND_HALF_DOWN  # rounds if entered more than self.ndecimals decimals
            price = str(round(Decimal(price), self.ndecimals))
        except decimal.InvalidOperation:
            self.editw = self.get_editw_number(self.priceLabel) - 1
            self.ok_button.editing = False
            errorMsg = "Error: The price is wrong"
            return errorMsg

        # repeated value check: numeral and isbn fields
        if self.numeralFld.value != self.bu_numeral or self.isbnFld.value != self.bu_isbn:
            for row in config.fileRows:
                self.ok_button.editing = False
                # Already exists and it's not itself
                if row[1] == int(self.numeralFld.value) and self.numeralFld.value != self.bu_numeral:
                    self.editw = self.get_editw_number("Numeral:") - 1
                    errorMsg = "Error:  Numeral already exists"
                    return errorMsg
                # Already exists and it's not itself
                if row[2] == self.isbnFld.value and self.isbnFld.value != self.bu_isbn:
                    self.editw = self.get_editw_number("ISBN/SKU:") - 1
                    errorMsg = "Error:  ISBN/SKU already exists"
                    return errorMsg

    def exist_changes(self):
        "Checking for changes to the fields."
        exist_changes = False
        if self.numeralFld.value != self.bu_numeral or \
            self.bookTitleFld.value != self.bu_bookTitle or \
            self.originalTitleFld.value != self.bu_originalTitle or \
            self.authorFld.value != self.bu_author or \
            self.descriptionFld.value != self.bu_description or \
            self.isbnFld.value != self.bu_isbn or \
            self.yearFld.value != self.bu_year or \
            self.publisherFld.value != self.bu_publisher or \
            self.creationDateFld.value != self.bu_creationDate or \
            self.genreFld.value != self.bu_genre or \
            self.coverTypeFld.value != self.bu_coverType or \
            self.warehousesFld.value != self.bu_warehouses or \
            self.priceFld.value != self.bu_price :
            exist_changes = True
        return exist_changes    

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def get_publisher_num(self):
        "Finds publisher numeral or gets a new one."
        pub_list = self.get_all_publishers()
        for p in pub_list:
            if p[1].lower() == self.publisherFld.value.lower():
                return p[0]     # = publisher.numeral
        # not found:
        # it can be a typo error:
        message = "\n  Publisher was not found. Create it as a new one?"
        if not bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
            return None
        num = self.get_last_numeral("'bookstore.publisher'") + 1
        conn = config.conn
        cur = conn.cursor()
        sqlQuery = "INSERT INTO 'bookstore.publisher' (numeral,name,address,phone,url) VALUES (?,?,?,?,?)"
        values = (num, self.publisherFld.value, "", "", "")  # some fields are filled empty
        cur.execute(sqlQuery, values)
        conn.commit()
        bs.notify_OK("\n      A new publisher was created.\n      Remember to fulfill all the data in its file.", "Message")
        return num

    def save_created_book(self):
        "Button based Save function for C=Create."

        conn = config.conn
        cur = conn.cursor()
        # Check if author exists, to create intermediate book_author table:
        try:
            sqlQuery = "SELECT id, numeral, name FROM 'bookstore.author' WHERE name=?"
            cur.execute(sqlQuery, (self.authorFld.value,) )
            row = cur.fetchone()
            self.author_numeral = row[1]
        except TypeError:   # author does not exist
            message = "\n   Author was not found. Create it as a new one?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.author_numeral = self.get_last_numeral("'bookstore.author'") + 1
                sqlQuery = "INSERT INTO 'bookstore.author' (numeral, name, address, bio, url) VALUES (?,?,?,?,?)"
                values = (int(self.author_numeral), self.authorFld.value, "", "", "")  # some fields are filled empty
                cur.execute(sqlQuery, values)
                conn.commit()
                bs.notify_OK("\n      A new author was created.\n      Remember to fulfill all the data in its file.", "Message")
            else:
                bs.notify_OK("\n      Getting back to book form.\n      Choose or enter a valid author.", "Message")
                return

        # creation of book_author intermediate table
        sqlQuery = "INSERT INTO 'bookstore.book_author' (book_num, author_num, is_main_author) VALUES (?,?,?)"
        values = (int(self.numeralFld.value), int(self.author_numeral), 1)
        cur.execute(sqlQuery, values)
        conn.commit()
        conn.isolation_level = None     # free the multiuser lock

        # Create the book record
        
        publisher_num = self.get_publisher_num()    # Publisher is a direct reference to another table
        if publisher_num == None:
            return  # back to form
        DBcreationDate = self.screenToDBDate(self.creationDateFld.value, self.creationDateFld.format)
        genre = int(self.genreFld.value[0])   # initial only
        cover_type = int(self.coverTypeFld.value[0])   # initial only
        price = self.priceFld.value.replace(",", ".")   # here, no matter config.decimal_symbol
        price = float(Decimal(price))
        columns = " (numeral,book_title,original_title,description,isbn,year,publisher_num,creation_date,genre_id,cover_type,price) "
        sqlQuery = "INSERT INTO " + DBTABLENAME + columns + " VALUES (?,?,?,?,?,?,?,?,?,?,?)"
        values = (int(self.numeralFld.value), self.bookTitleFld.value, self.originalTitleFld.value, self.descriptionFld.value, \
            self.isbnFld.value, int(self.yearFld.value), publisher_num, DBcreationDate, genre, cover_type, price)
        cur.execute(sqlQuery, values)
        conn.commit()
        config.fileRow[0] = cur.lastrowid
        bs.notify("\n       Record created", title="Message", form_color='STANDOUT', wrap=True, wide=False)

        # Manage book warehouses:
        # warehouses existence check and update of book_warehouse intermediate table:
        if self.warehousesFld.value != self.bu_warehouses:
            whList = list(self.warehousesFld.value.split(","))
            for wh in whList:
                if wh == "":    # clean up the list for extra commas
                    continue
                try:
                    sqlQuery = "SELECT numeral, code FROM 'bookstore.warehouse' WHERE code=?"
                    cur.execute(sqlQuery, (wh.strip(),) )
                    row = cur.fetchone()
                    warehouse_num = row[0]  # jumps to except if does not exist
                    # Create the book_warehouse if it doesn't exist:
                    sqlQuery = "SELECT * FROM 'bookstore.book_warehouse' WHERE book_num=? AND warehouse_num=?"
                    cur.execute(sqlQuery, (self.numeralFld.value, str(warehouse_num),) )
                    row = cur.fetchone()
                    if row == None:   # book_warehouse does not exist, create it
                        sqlQuery = "INSERT INTO 'bookstore.book_warehouse' (book_num, warehouse_num, bookshelf, stock) VALUES (?,?,?,?)"
                        values = (int(self.numeralFld.value), int(warehouse_num), None, None)
                        cur.execute(sqlQuery, values)
                        conn.commit()
                except TypeError:   # warehouse does not exist, we don't create it at this point.
                    message = "\n   Warehouse '" + wh + "' was not found. Create it beforehand."
                    bs.notify_OK(message, title="", wrap=True, editw = 1,)
                    continue

        # update config.fileRows:
        new_record = []
        new_record.append(config.fileRow[0])
        new_record.append(int(self.numeralFld.value))
        new_record.append(self.bookTitleFld.value)
        new_record.append(self.originalTitleFld.value)
        new_record.append(self.authorFld.value)
        new_record.append(self.descriptionFld.value)
        new_record.append(self.isbnFld.value)
        new_record.append(self.yearFld.value)
        new_record.append(self.publisherFld.value)
        new_record.append(self.creationDateFld.value)
        new_record.append(self.genreFld.value)
        new_record.append(self.coverTypeFld.value)
        new_record.append(Decimal(price))
        config.fileRows.append(new_record)
        self.exitBook(modified=True)

    def save_updated_book(self):
        "Button based Save function for U=Update."

        conn = config.conn
        cur = conn.cursor()

        # if numeral has changed (already checked for non-existence), update book_author and book_warehouse intermediate tables
        if self.numeralFld.value != self.bu_numeral:

            columns = "book_num=?"
            new_numeral = int(self.numeralFld.value)
            old_numeral = int(self.bu_numeral)
            sqlQuery = "UPDATE 'bookstore.book_author' SET " + columns + " WHERE book_num=?"
            values = (new_numeral, old_numeral)
            try:
                cur.execute(sqlQuery, values)
                conn.commit()
            except sqlite3.IntegrityError:
                bs.notify_OK("\n     Numeral of book already exists. ", "Message")
                return

            sqlQuery = "UPDATE 'bookstore.book_warehouse' SET " + columns + " WHERE book_num=?"
            values = (new_numeral, old_numeral)
            cur.execute(sqlQuery, values)
            conn.commit()

        # Check if author has changed, and if exists, to update intermediate book_author table
        if self.authorFld.value != self.bu_author:
            try:
                sqlQuery = "SELECT id, numeral, name FROM 'bookstore.author' WHERE name=?"
                cur.execute(sqlQuery, (self.authorFld.value,) )
                row = cur.fetchone()
                self.author_numeral = row[1]
            except TypeError:   # author does not exist
                message = "\n   Author was not found. Create it as a new one?"
                if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                    self.author_numeral = self.get_last_numeral("'bookstore.author'") + 1
                    sqlQuery = "INSERT INTO 'bookstore.author' (numeral, name, address, bio, url) VALUES (?,?,?,?,?)"
                    values = (self.author_numeral, self.authorFld.value, "", "", "")  # some fields are filled empty
                    cur.execute(sqlQuery, values)
                    conn.commit()
                    bs.notify_OK("\n      A new author was created.\n      Remember to fulfill all the data in its file.", "Message")
                else:
                    bs.notify_OK("\n      Getting back to book form.\n      Choose or enter a valid author.", "Message")
                    return
            # update of book_author intermediate table
            try:
                columns = "book_num=?, author_num=?, is_main_author=?"
                if self.numeralFld.value == self.bu_numeral:
                    numeral = int(self.numeralFld.value)
                else:
                    numeral = int(self.bu_numeral)
                sqlQuery = "UPDATE 'bookstore.book_author' SET " + columns + " WHERE book_num=?"
                values = (numeral, self.author_numeral, 1, numeral)
                cur.execute(sqlQuery, values)
                conn.commit()
            except TypeError:   # book_author does not exist, create it
                sqlQuery = "INSERT INTO 'bookstore.book_author' (book_num, author_num, is_main_author) VALUES (?,?,?)"
                values = (int(self.numeralFld.value), self.author_numeral, 1)
                cur.execute(sqlQuery, values)
                conn.commit()

        # Publisher is a direct reference to another table
        publisher_num = self.get_publisher_num()
        if publisher_num == None:
            return  # back to form
        DBcreationDate = self.screenToDBDate(self.creationDateFld.value, self.creationDateFld.format)
        genre = int(self.genreFld.value[0])   # initial only
        cover_type = int(self.coverTypeFld.value[0])   # initial only

        # Manage book warehouses:
        # warehouses existence check and update of book_warehouse intermediate table
        if self.warehousesFld.value != self.bu_warehouses:
            whList = list(self.warehousesFld.value.split(","))
            for wh in whList:
                if wh == "":    # clean up the list for extra commas
                    continue
                try:
                    sqlQuery = "SELECT numeral, code FROM 'bookstore.warehouse' WHERE code=?"
                    cur.execute(sqlQuery, ( wh.strip(),) )
                    row = cur.fetchone()
                    warehouse_num = row[0]  # jumps to except if does not exist
                    # Create the book_warehouse if it doesn't exist:
                    sqlQuery = "SELECT * FROM 'bookstore.book_warehouse' WHERE book_num=? AND warehouse_num=?"
                    cur.execute(sqlQuery, (self.numeralFld.value, str(warehouse_num),) )
                    row = cur.fetchone()
                    if row == None:   # book_warehouse does not exist, create it
                        sqlQuery = "INSERT INTO 'bookstore.book_warehouse' (book_num, warehouse_num, bookshelf, stock) VALUES (?,?,?,?)"
                        values = (int(self.numeralFld.value), int(warehouse_num), None, None)
                        cur.execute(sqlQuery, values)
                        conn.commit()
                except TypeError:   # warehouse does not exist, we don't create it at this point.
                    message = "\n   Warehouse '" + wh + "' was not found. Create it beforehand."
                    bs.notify_OK(message, title="", wrap=True, editw = 1,)
                    continue
            
            # Deletion of erased book_warehouses:
            diffList = self.make_differences_list(self.warehousesFld.value, self.bu_warehouses)
            conn = config.conn
            cur = conn.cursor()
            for wh in diffList:
                if wh[0] == "-":    # it's a deletion
                    wh = wh[1:]

                    message = "\n   Select OK to delete warehouse '" + wh + "' for this book."
                    if not bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                        bs.notify_OK("\n  Nothing was deleted.", "Message")
                        return
                    sqlQuery = "SELECT numeral FROM 'bookstore.warehouse' WHERE code=?"
                    cur.execute(sqlQuery, (wh,) )
                    row = cur.fetchone()                                        
                    book_num = self.numeralFld.value
                    warehouse_num = str(row[0])
                    cur.execute("DELETE FROM 'bookstore.book_warehouse' WHERE book_num="+book_num+" AND warehouse_num="+warehouse_num)
                    conn.commit()

        # Update the Book record

        price = self.priceFld.value.replace(",", ".")   # here, no matter config.decimal_symbol
        price = float(Decimal(price))
        columns = "numeral=?, book_title=?, original_title=?, description=?, isbn=?, year=?, publisher_num=?, creation_date=?, genre_id=?, cover_type=?, price=?"
        sqlQuery = "UPDATE " + DBTABLENAME + " SET " + columns + " WHERE id=?"
        values = (int(self.numeralFld.value), self.bookTitleFld.value, self.originalTitleFld.value, self.descriptionFld.value, self.isbnFld.value, \
            int(self.yearFld.value), publisher_num, DBcreationDate, genre, cover_type, price, config.fileRow[0])
        cur.execute(sqlQuery, values)
        conn.commit()
        bs.notify("\n       Record saved", title="Message", form_color='STANDOUT', wrap=True, wide=False)
        self.exitBook(modified=True)

    def updateOKbtn_function(self):
        "OK button function under Update mode."
        self.strip_fields()     # Get rid of spaces
        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        else:
            if self.exist_changes():
                self.save_updated_book()
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            else:
                self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
                self.exitBook(modified=False)

    def updateCancelbtn_function(self):
        "Cancel button function under Update mode."
        self.strip_fields()     # Get rid of spaces        
        if self.exist_changes():
            message = "\n      Discard changes?"
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitBook(modified=False)
        else:
            self.selectorForm.grid.set_highlight_row(int(self.numeralFld.value))
            self.exitBook(modified=False)

    def screenToDBDate(self, screenDate, screenFormat):
        "Converts a simple screen date to a DB timestamp"
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

    def make_differences_list(self, new_field, old_field):
        "Accepts two comma-separated string-fields of values and returns a differences list like [new_value, -old_value]."
        "For enumeration text fields."
        diffList = []    # setting up a differences list
        if new_field != old_field:  # there are changes 
            oldList0 = list(old_field.split(","))
            oldList = []
            for c in oldList0:
                if c != "": # extra commas do this
                  oldList.append(c.strip())
            newList0 = list(new_field.split(","))
            newList = []
            for c in newList0:
                if c != "": # extra commas do this
                    newList.append(c.strip())
            for c in newList:
                if c not in oldList:
                    try:
                        diffList.append(int(c)) # is an int
                    except ValueError:
                        try:
                            diffList.append(float(c)) # is a float
                        except ValueError:
                            diffList.append(c) # is a string

            for c in oldList:
                if c not in newList:
                    try:
                        diffList.append(0 - int(c)) # is an int
                    except ValueError:
                        try:
                            diffList.append(0 - float(c)) # is a float
                        except ValueError:
                            diffList.append("-" + c) # is a string: negative of a string!
        return diffList
        
    def textfield_exit(self):
        "Exit from a text field with Escape"
        pass    # do nothing = don't exit

    def is_editable_field(self, widget=None):
        "Hooked from bs.MyAutocomplete.filter_char()"
        if widget.name == "Author:" or widget.name == "Publisher:" or widget.name == "Warehouses:" :
            return True
        else:
            return False

    def not_first_keypress(self, widget=None):
        "Hooked from bs.MyAutocomplete.h_exit_up()"
        if widget.name == "Author:" :
            widget.first_keypress = False
        elif widget.name == "Publisher:" :
            widget.first_keypress = False
        elif widget.name == "Genre:" :
            widget.first_keypress = False
        elif widget.name == "Cover type:" :
            widget.first_keypress = False
        elif widget.name == "Warehouses:" :
            widget.first_keypress = False

    def create_popup_window(self, widget=None):
        "Hooked from bs.MyAutocomplete.get_choice()"
        if widget.name == "Author:" :
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=39, show_aty=3, columns=36, lines=14, shortcut_len=None)
        elif widget.name == "Publisher:" :
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=39, show_aty=6, columns=39, lines=14, shortcut_len=None)
        elif widget.name == "Genre:" :
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=39, show_aty=6, columns=30, lines=10, shortcut_len=1)
        elif widget.name == "Cover type:" :
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=30, show_aty=5, columns=40, lines=10, shortcut_len=1)
        elif widget.name == "Warehouses:" :
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=36, show_aty=6, columns=40, lines=12, shortcut_len=None)
        return tmp_window

    def more_than_one_item(self, widget=None, field_val=None):
        "Hooked from bs.MyAutocomplete.get_choice(). Returns None when it's an enum field with more than one value."
        field_val = field_val
        if widget.name == "Warehouses:" :       # it's an enum field and...
            if len(field_val.split(",")) > 1:   # ...there's more than one item in the enum field, so...
                field_val = None                # ...don't select anyone and highlight first item in the popup.
        return field_val

    def scan_value_in_list(self, widget=None):
        "Hooked from bs.MyAutocomplete.when_check_value_changed()"
        widget_value = widget.value
        if widget.name == "Author:" or widget.name == "Publisher:" :
            if widget.cursor_position != 0:
                widget_value = widget.value[:widget.cursor_position]
                found_value = widget.find_value_literal(widget_value)
                if found_value != widget_value:     # value is not found...
                    if found_value != False:    # ...and list is not empty
                        widget_value = found_value
        return widget_value
        
    def append_value_to_enum(self, widget=None, chosen_value=None):
        "Hooked from bs.Chooser.auto_complete(). Append a chosen value to an enum field."
        value = widget.value
        chosen_value = chosen_value
        if widget.name == "Warehouses:":    # it's an enum field and...
            if value != "":
                if widget.values[chosen_value] not in value:    # ...the chosen value is not in it...
                    value += ", " + widget.values[chosen_value] # ...so append it.
                    return value
                else:
                    return value
        if chosen_value == -1:      # no values on the list and CR pressed
            value = ""   
        else:
            if len(widget.values) > 0:
                value = widget.values[chosen_value]
            else:   # empty values list
                value = ""
        return value

    def get_parentField(self, widget=None):
        "Hooked from bs.MyPopup.__init__()"
        parentField = None
        if widget.name == "Author:" :
            parentField = self.authorFld
        elif widget.name == "Publisher:" :
            parentField = self.publisherFld
        elif widget.name == "Warehouses:" :
            parentField = self.warehousesFld
        return parentField
