#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     bookSelector.py - Selector and maintenance options for books
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################
# Form with following widgets:
#   .editw = 0 --> screen title
#   .editw = 1 --> book record grid
#   .editw = 2 --> status literal / options line at screen bottom
#   .editw = 3 --> 1-letter option input field
#   .editw = 4 --> Detail input field for 6-digit Numeral, and for search literal, initially hidden
##############################################################################

import datetime
import decimal
import sqlite3
import time
from decimal import Decimal
import sys

import npyscreen
import numpy

import bsWidgets as bs
import config
from book import BookForm
from config import SCREENWIDTH as WIDTH

REMEMBER_ROW = True    # remember the last row selected when coming from main menu
REMEMBER_SUBSET = config.REMEMBER_SUBSET  # remember the last 'Find' result subset
DATEFORMAT = config.dateFormat  # program-wide
FIELD_LIST = ["numeral","title","author","year","publisher","date","isbn"]  # only screen fields, not DB
DBTABLENAME = "'bookstore.book'"

helpText =  "The book selector is a grid of database table rows (records).\n\n" +\
    "* Use the arrow keys, Page Up/Down and Home/End to navigate the grid.\n\n" +\
    "* Under the grid there's a bottom line with the operating F+CRUD options. " +\
    "You can switch between the record grid and the options line with TAB key.\n\n" +\
    "* F+CRUD = Find, Create, Read, Update and Delete. You can reach the functions by the single " +\
    "keypress of a letter, from the record grid or from the bottom line. " +\
    "Then you are asked for a 'Numeral' unique row identifier, to access the record.\n\n" +\
    "* Of all the record selector screens, this is the most complex, as it uses variable column widths, " +\
    "and a pair of extra columns in a second screen to the right (accessible through the right-arrow key).\n\n" +\
    "* The 'Find' function looks for a string in the rows. If a field/column is not specified, " +\
    "it searches in all the columns. You can use the notation Field:String to search in a single column. For example: Numeral:17\n" +\
    "You can use '=', '<' and '>' after the ':' as well: Year:>1999 Year:=2004\n" +\
    "The search is based on the database LIKE statement, so a search for '7' will return the 7 and 17 Numerals. " +\
    "If you want the exact match use numeral:=7  An empty string search restores the grid with the whole recordset. " +\
    "By default, the record grid 'remembers' the result of the last search. This behaviour can be changed by variable. "    


class BookSelectForm(npyscreen.FormBaseNew):
    "Book selector and FCRUD options."
    def __init__(self, name="", parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None, \
        cycle_widgets=True, *args, **keywords):
        # Creates the father, npyscreen.FormBaseNew.
        config.parentApp = parentApp
        
        # goes to _FormBase:
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

        self.ndecimals = config.ndecimals   # to round the DB price

    def create(self):
        "The standard constructor will call the method .create(), which you should override to create the Form widgets."
        self.framed = False   # frameless form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exitBookSelector   # Escape exit
        
        # Form title - Screen title line
        pname, version = config.pname, config.program_version
        self.form_title = pname + " " + version + " - Book selector"
        self.today = self.get_today()
        self.formTitle=self.add(bs.MyTextfield, name="BookTitle", value=None, relx=0, rely=0, \
            use_max_space=True, width=WIDTH, max_width=WIDTH, maximum_string_length=WIDTH, editable=False)
        
        # Books grid
        self.grid = bs.MyGrid(screen=self, name="BookGrid")      # (All attributes are set later)
        self.grid.editing=True
        self.columnTitles = ["Numeral","      Title","  Author","Year","  Publisher"," Date","  ISBN/SKU"]
        self.col_widths = [8, 29, 24, 5, 14, 9, 71]  # first (left) screen fields must add up to WIDTH
        
        self.grid = self.add(self.grid.__class__, name="BookGrid", col_titles=self.columnTitles, col_widths=self.col_widths, \
                relx=0, rely=1, height=22, width=WIDTH, min_height=22, min_width=WIDTH, editable=True, hidden=False, \
                values=None, select_whole_line=True, always_show_cursor=True, column_width=13)
        
        # Status and Options bottom line
        self.optionsLiteral="[Tab] option:     F=Find   C=Create   R=Read   U=Update   D=Delete     Esc=Quit"
        self.statusLiteral = self.optionsLiteral
        self.statusLine = self.add(bs.MyTextfield, name="statusLine", value=self.statusLiteral, relx=0, rely=24, \
            use_max_space=True, width=WIDTH, max_width=WIDTH, maximum_string_length=WIDTH, min_height=0, max_height=0, editable=False)
        # For the Find option:
        self.findStatusLiteral = "Search literal (or field:literal):                            -> Empty=full set"
        
        # Option input field, automatic 1-character
        self.inputOpt = self.add(bs.OptionField, name='OptionFld', value="", relx=14, rely=24,
                                        width=0, height=0, max_width=3, max_height=0, editable=True, use_max_space=True)
        self.inputOpt.value = ""
        self.inputOpt.check_value_change=True

        # Detail input field for 6-digit numeral, and also for Find-literal
        self.inputDetail = self.add(bs.DetailField, screenForm=BookForm, name='DetailFld', value="", relx=26, rely=24,
                                        width=8, height=0, max_width=8, max_height=0, 
                                        editable=True, hidden=True, use_max_space=True)
        
    def set_up_title(self, filerows, full_set=None):
        "Build the screen title"
        if full_set == True:
            self.formTitle.value = self.form_title + " - Full set: " + str(len(filerows)) + " rows"
        else:
            self.formTitle.value = self.form_title + " - [Find] subset: " + str(len(filerows)) + " rows"
        self.formTitle.value = self.formTitle.value + " "*(WIDTH - len(self.formTitle.value) - len(self.today)) + self.today

    def get_today(self):
        sep = DATEFORMAT[2]
        if DATEFORMAT[0] == "d":
            format = "%d"+sep+"%m"+sep+"%Y"
        else:
            format = "%m"+sep+"%d"+sep+"%Y"
        today = datetime.datetime.today().strftime(format)
        if len(DATEFORMAT) == 8:
            today = today[:6] + today[8:]
        return today

    def getRowListForScreen(self, filerows):
        "Memory row list to screen row list for grid."
        if len(filerows) > 0:
            self.screenFileRows = numpy.array(filerows)  # I need numpy to...
            self.screenFileRows = self.screenFileRows[:, 1:]  # ...cut the first field ("id")
            return self.screenFileRows.tolist()          # and again to list
        else:
            empty_list = [["","","","","",""]]
            return empty_list

    def readDBTable(self):
        "Reads the full table and returns a list of list-rows."
        cur = config.conn.cursor()
        while True:     # multiuser DB locking loop
            try:
                cur.execute("SELECT * FROM " + DBTABLENAME + " ORDER BY numeral")
                break   # go on
            except sqlite3.OperationalError:
                bs.notify_OK("\n    Database is locked, please wait.", "Message")
        filerows = cur.fetchall()
        rows = []        
        for row in filerows:
            id = row[0]
            numeral = row[1]
            bookTitle = row[2]
            author = self.get_author_name(numeral)
            year = row[6]
            publisher = self.get_publisher_name(row[7])
            date = self.DBtoScreenDate(row[8], DATEFORMAT)   # = creation date
            isbn = row[5]
            cRow = [id, numeral, bookTitle, author, year, publisher, date, isbn]
            rows.append(cRow)    # included book.id
        self.set_up_title(filerows, full_set=True)
        return rows # it's a list of lists
    
    def fill_grid(self):
        "Read the DB table and put it into the grid."
        config.fileRows = self.readDBTable()        # full row set: it's a list of lists
        self.screenFileRows = self.getRowListForScreen(config.fileRows)     # it's a list of lists
        self.grid.values = self.screenFileRows

    def update_grid(self):
        "Updates the affected row in the book grid and RAM config table list. Called from outside this module."
        # After a change, creation or multiple deletion, the grid displays the full set :
        if not REMEMBER_SUBSET or \
            config.last_table != DBTABLENAME or \
                (config.last_table == DBTABLENAME and config.last_operation == "Create") or \
                    (config.last_table == DBTABLENAME and config.last_operation == "Delete" or \
                        config.last_operation == "DeleteMultipleRecords"):
            self.fill_grid()
            if config.last_table != DBTABLENAME:
                config.last_table = DBTABLENAME
                self.grid.set_highlight_row(None)    # simply selects the first one
        else:   # remember Find subset, etc...
            if config.last_operation != "Delete":
                if config.fileRow is not None:  # it's not initializing
                    for row in config.fileRows:
                        if row[0] == config.fileRow[0]:     # ID field
                            row[1] = config.fileRow[1]      # Numeral
                            row[2] = config.fileRow[2]      # BookTitle
                            row[3] = config.fileRow[4]      # Author
                            row[4] = config.fileRow[7]      # Year
                            row[5] = config.fileRow[8]      # Publisher
                            if len(config.fileRow[9]) == 23:    # we come from the main menu
                                row[6] = self.DBtoScreenDate(config.fileRow[9], DATEFORMAT)
                            else:   # we come from the book form
                                row[6] = config.fileRow[9]  # Date = creation date
                            row[7] = config.fileRow[6]      # ISBN/SKU
                            break
                    screenFileRows = self.getRowListForScreen(config.fileRows)
                    self.grid.values = screenFileRows
                    self.set_up_title(config.fileRows, full_set=False)
                
        if not REMEMBER_ROW:
            self.grid.set_highlight_row(None)    # simply selects the first one

    def create_row(self):
        "It's been keypressed C/c=Create."
        # Let's display an empty book record
        self.inputDetail.option = "Create"
        self.inputOpt.value = "C"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the C
        # Disable option input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        self.grid.editing = False
        self.inputDetail.relx = 26 # just in case
        self.ask_option()  # for when we are back to this screen
        config.parentApp.setNextForm("BOOK")
        config.parentApp.switchFormNow()
        BookForm.set_createMode()

    def read_row(self):
        "It's been keypressed R/r=Read."
        # (Must ask for the searched numeral confirmation)
        self.inputDetail.option = "Read"
        self.inputOpt.value = "R"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the R
        # Disable option input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        
        # Reset previous status line field
        self.statusLiteral = "Enter numeral to read:" + (59 * " ")
        self.statusLine.value = self.statusLiteral
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 8
        self.inputDetail.max_width = 8
        self.inputDetail.maximum_string_length = 6
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exiting
        self.inputDetail.how_exited = True     # A default value
        self.editw = 4      # Swap to numeral input field

        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def update_row(self):
        "It's been keypressed U/u=Update."
        # (Must ask for the searched numeral confirmation)
        self.inputDetail.option = "Update"
        self.inputOpt.value = "U"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the U
        # Disable option input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        
        # Reset previous status line field
        self.statusLiteral = "Enter numeral to update:" + (57 * " ")
        self.statusLine.value = self.statusLiteral
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 8
        self.inputDetail.max_width = 8
        self.inputDetail.maximum_string_length = 6
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exiting
        self.inputDetail.how_exited = True     # A default value
        self.editw = 4      # Swap to numeral input field
        
        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()
    
    def find_row(self):
        "It's been keypressed F/f=Find."
        # (Have to ask for the searched literal)
        self.inputDetail.option = "Find"
        self.inputOpt.value = "F"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the F
        # Disable option input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True

        # Reset previous status line field
        self.statusLiteral = self.findStatusLiteral
        self.statusLine.value = self.statusLiteral
        self.statusLine.relx=0
        self.statusLine.width=36
        self.statusLine.max_width=36
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        self.inputDetail.is_find_literal = True   # change to find-literal field
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 35
        self.inputDetail.width = 27
        self.inputDetail.max_width = 27
        self.inputDetail.maximum_string_length = 27
        self.inputDetail.value = ""
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exiting
        self.inputDetail.how_exited = True     # A default value
        self.editw = 4      # Swap to numeral input field

        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def delete_row(self):
        "It's been keypressed D/d=Delete."
        # (Must ask for the searched numeral for delete confirmation)
        self.inputDetail.option = "Delete"
        self.inputOpt.value = "D"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the D
        # Disable option input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True

        # Reset previous status line field
        self.statusLiteral = "Enter numeral to delete:" + (57 * " ")
        self.statusLine.value = self.statusLiteral
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 8
        self.inputDetail.max_width = 8
        self.inputDetail.maximum_string_length = 6
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exiting
        self.inputDetail.how_exited = True     # A default value
        self.editw = 4      # Swap to numeral input field
        
        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def read_record(self, numeral):
        "Search for the required record and store it in a reachable variable. Called from the Detail-field widget."
        config.screenRow = 0
        config.fileRow = []
        for row in config.fileRows:
            if row[1] == numeral:
                cur = config.conn.cursor()
                # ...and I read again 'cause there can be more fields in the form than in the grid list
                sqlQuery = "SELECT * FROM " + DBTABLENAME + " WHERE numeral=?"
                while True:     # multiuser DB locking loop...
                    try:
                        cur.execute(sqlQuery, (str(numeral),) )
                        break   # go on
                    except sqlite3.OperationalError:
                        bs.notify_OK("\n    Database is locked, please wait.", "Message")
                filerow = cur.fetchone()
                config.fileRow.append(filerow[0])   # id
                config.fileRow.append(filerow[1])   # numeral
                config.fileRow.append(filerow[2])   # book title
                config.fileRow.append(filerow[3])   # original title
                # filerow has no author value, it is found through intermediate table:
                config.fileRow.append(self.get_author_name(filerow[1]))   # author
                config.fileRow.append(filerow[4])   # description
                config.fileRow.append(filerow[5])   # isbn/sku
                config.fileRow.append(filerow[6])   # year
                config.fileRow.append(self.get_publisher_name(filerow[7]))   # publisher
                config.fileRow.append(filerow[8])   # creation_date
                config.fileRow.append(filerow[9])   # genre
                config.fileRow.append(filerow[10])  # cover_type
                # rounding of price decimals
                price = filerow[11]
                ctx = decimal.getcontext()
                ctx.prec = 6
                ctx.rounding = decimal.ROUND_HALF_DOWN  # rounds if entered more than self.ndecimals decimals
                price = str(round(Decimal(price), self.ndecimals))
                config.fileRow.append(price)
                self.grid.edit_cell = [config.screenRow, 0]  # highlight the selected row
                # If the searched index is greater than the first displayed index
                if config.screenRow > self.grid.begin_row_display_at:
                    self.grid.ensure_cursor_on_display_down_right(None)
                else:   # If the searched index is smaller than the first displayed index
                    self.grid.ensure_cursor_on_display_up(None)
                return True
            config.screenRow += 1
        bs.notify("\n        Record not found", form_color='STANDOUT', wrap=True, wide=False)
        time.sleep(0.6)     # let it be seen
        return False    # not found

    def exitBookSelector(self):
        "Escape key was pressed: isinstance(self, BookSelectForm) = True; we always come from the OptionField."
        get_out = False
        if self.statusLine.value != self.optionsLiteral:    # it's not the option statusline; it's the detail field
            # we come from DetailField : we have to restore the option statusline and come back to the OptionField
            self.hide_detail()
            self.ask_option()
        else:           # we come from the OptionField, we have to exit to main menu
            self.inputOpt.value = ""
            self.inputOpt.update(clear=True)
            get_out = True
        if get_out:     # get out of this form
            config.parentApp.setNextForm("MAIN")
            config.parentApp.switchFormNow()

    def pre_edit_loop(self):
        #print("pre_edit_loop()!!!")
        pass

    def post_edit_loop(self):
        #print("post_edit_loop()!!!")
        pass

    def _during_edit_loop(self):
        #print("during_edit_loop()!!!")
        pass
    
    def hide_detail(self):
        "Hides the DetailField."
        self.inputDetail.editable = False
        self.inputDetail.hidden = True

    def reset_statusLine(self):
        self.hide_detail()
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLiteral = self.optionsLiteral
        self.statusLine.value = self.statusLiteral
        self.statusLine.update(clear=True)
        self.statusLine.display()
    
    def ask_option(self):
        "Resets status line and option input field."
        self.reset_statusLine()        
        self.inputOpt.hidden=False
        self.inputOpt.editable=True
        self.inputOpt.value = ""
        self.inputOpt.display()
        self.inputOpt.how_exited = False    # don't touch it. Escape-exit issue.
        self.editw = 3             # go to the OptionField

    def looks_like_a_date(self, literal, format):
        "Find-literal date check. Returns True/False."
        isDate = False
        if len(literal) == 8 or len(literal) == 10:
            sep = format[2]
            if literal[2] == sep and literal[5] == sep:
                if format[0] == "d":
                    day = literal[:2]
                    month = literal[3:5]
                elif format[0] == "m":
                    month = literal[:2]
                    day = literal[3:5]
                year = literal[6:]
                if day.isnumeric() and month.isnumeric() and year.isnumeric():
                    if len(year) == 2:
                        if int(year) > 69:           # Hmm...
                            century = "19"
                        else:
                            century = "20"
                        year = century + year
                    try:
                        datetime.datetime(int(year), int(month), int(day))
                        isDate = True
                    except ValueError:
                        pass
            else:
                if literal[2] in ["-","/"] and literal[5] in ["-", "/"]:    # Wrong separators
                    bs.notify("\n    Error in date separators.", "Message")
                    time.sleep(0.3)     # let it be seen
        return isDate

    def screenToDBdate(self, literal, format):
        "Converts a screen simple date into a DB timestamp. Date must be already checked."
        sep = format[2]
        if format[0] == "d":
            day = literal[:2]
            month = literal[3:5]
        elif format[0] == "m":
            month = literal[:2]
            day = literal[3:5]
        year = literal[6:]
        if len(year) == 2:
            if int(year) > 69:           # Hmm...
                century = "19"
            else:
                century = "20"
            year = century + year
        DBdate = year+"-"+month+"-"+day+" 00:00:00.000"
        return DBdate

    def find_DB_rows(self, find_literal):
        "SQL-Based Find function: Executes SQL query for Find option."
        # Accepting:
        #   - A literal without ":" (searches all the field/columns).
        #   - A literal with ":" like in field:literal.
        #   - Date literals with "/" or "-" separators.
        #   - A literal with one comparator "=/</>" after field: as in field:<literal
        field = False
        if ":" in find_literal:     # like, simplifying
            pos = find_literal.find(":")
            field_list = FIELD_LIST
            field = find_literal[:pos]
            literal = find_literal[pos+1:].strip()
            if field.strip().lower() not in field_list or literal == "":
                bs.notify_OK(" Find: Wrong field or literal", "Message")
                return False
        else:
            literal = find_literal

        comparator = False
        if literal[0] in ["=","<",">"]:
            comparator = literal[0]
            literal = literal[1:]
        if comparator and not field:
            bs.notify_OK("Find: Must specify field: when using a comparator", "Message")
            return False

        date_literal = None
        if self.looks_like_a_date(literal, DATEFORMAT):    # Date check
            date_literal = self.screenToDBdate(literal, DATEFORMAT)
        else:
            if field in ["date"]:
                bs.notify_OK("Find: Error in date literal", "Message")
                return False

        fieldStr = "'bookstore.book'.id, 'bookstore.book'.numeral, 'bookstore.book'.book_title, 'bookstore.author'.name, \
            'bookstore.book'.year, 'bookstore.publisher'.name, 'bookstore.book'.creation_date, 'bookstore.book'.isbn"
        sqlQuery = "SELECT " + fieldStr + " FROM " + DBTABLENAME + \
            " INNER JOIN 'bookstore.book_author' ON 'bookstore.book_author'.book_num = 'bookstore.book'.numeral " + \
            " INNER JOIN 'bookstore.author' ON 'bookstore.author'.numeral = 'bookstore.book_author'.author_num " + \
            " INNER JOIN 'bookstore.publisher' ON 'bookstore.publisher'.numeral = 'bookstore.book'.publisher_num "
            
        if field == "numeral":
            field = "'bookstore.book'.numeral"
        elif field == "title":
            field = "book_title"
        elif field == "author":
            field = "'bookstore.author'.name"
        elif field == "publisher":
            field = "'bookstore.publisher'.name"
        elif field == "date":
            field = "'bookstore.book'.creation_date"

        if not comparator:
            if field == False:  # no field specified, so search all fields
                # Small trick for dates:
                if date_literal:
                    if date_literal in "00:00:00.000":
                        date_literal = "X"   # to not find it
                    whereStr = "WHERE 'bookstore.book'.creation_date LIKE ?" \
                        " COLLATE NOCASE ORDER BY 'bookstore.book'.numeral"
                    literal = date_literal
                else:
                    whereStr = "WHERE 'bookstore.book'.numeral LIKE ?" \
                        " OR 'bookstore.book'.book_title LIKE ?" \
                        " OR 'bookstore.author'.name LIKE ?" \
                        " OR 'bookstore.book'.year LIKE ?" \
                        " OR 'bookstore.publisher'.name LIKE ?" \
                        " OR 'bookstore.book'.creation_date LIKE ?" \
                        " OR 'bookstore.book'.isbn LIKE ?" \
                        " COLLATE NOCASE ORDER BY 'bookstore.book'.numeral"
            else:   # field != False
                if date_literal:
                    literal = date_literal
                whereStr = "WHERE " + field + " LIKE ? COLLATE NOCASE ORDER BY 'bookstore.book'.numeral"

        elif comparator:
            if date_literal:
                literal = date_literal
            whereStr = "WHERE " + field + " " + comparator + " ? COLLATE NOCASE ORDER BY 'bookstore.book'.numeral"

        sqlQuery += whereStr
        
        cur = config.conn.cursor()
        try:
            if comparator:
                pass    # leave literal without percents
            else:
                literal = "%" + literal + "%"
            values = ()
            for i in range(sqlQuery.count("?")):    # setting the parameters for SQL
                values += (literal,)
            cur.execute(sqlQuery, values)

        except sqlite3.OperationalError as e:   # some inputs like '\' 
            bs.notify_OK("\n    sqlite3.OperationalError: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
            return False            

        filerows = cur.fetchall()
        if len(filerows) == 0:
            bs.notify("\n    No matching records found","Message", form_color='STANDOUT', wrap=True, wide=False)
            return False
        rows = []        
        for row in filerows:
            id = row[0]
            numeral = row[1]
            title = row[2]
            author = row[3]
            year = str(row[4])
            publisher = row[5]
            date = self.DBtoScreenDate(row[6], DATEFORMAT)  # = creation date
            isbn = row[7]
            cRow = [id, numeral, title, author, year, publisher, date, isbn]
            rows.append(cRow)
        config.fileRows = rows
        self.screenFileRows = self.getRowListForScreen(config.fileRows)     # it's a list of lists
        self.grid.values = self.screenFileRows
        self.set_up_title(filerows, full_set=False)

        return True

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

    def get_author_name(self, book_num):
        "Returns author name."
        cur = config.conn.cursor()
        sqlQuery = "SELECT * FROM 'bookstore.book_author' WHERE book_num=?"
        try:
            cur.execute( sqlQuery, (str(book_num),) )
        except sqlite3.Error as e:
            bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
            return "DB Error"            
        filerows = cur.fetchall()
        if len(filerows) == 0:
            bs.notify("\n    Author/book relationship was not found","Message", form_color='STANDOUT', wrap=True, wide=False)
            return "Not found"
        for row in filerows:
            is_main_author = row[3]
            if is_main_author:  # = is main author
                author_num = row[2]
                sqlQuery = "SELECT * FROM 'bookstore.author' WHERE numeral=?"
                try:
                    cur.execute( sqlQuery, (str(author_num),) )
                except sqlite3.Error as e:
                    bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
                    return "DB Error"
                filerow = cur.fetchone()
                if filerow == None:
                    bs.notify("\n    Author was not found","Message", form_color='STANDOUT', wrap=True, wide=False)
                    return "Not found"
                author_name = filerow[2]
                return author_name
        return "Not found"

    def get_publisher_name(self, publisher_num):
        "Returns publisher name."
        cur = config.conn.cursor()
        sqlQuery = "SELECT name FROM 'bookstore.publisher' WHERE numeral=?"
        try:
            cur.execute(sqlQuery, (str(publisher_num),) )
        except sqlite3.Error as e:
            bs.notify_OK("\n    sqlite3.Error: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
            return "DB Error"            
        filerows = cur.fetchone()
        if filerows == None:
            bs.notify("\n    Publisher was not found","Message", form_color='STANDOUT', wrap=True, wide=False)
            return "Not found"
        else:
            return filerows[0]

    def textfield_exit(self):
        "Exit from Detail field with Escape"
        self.exitBookSelector()
        #pass    # do nothing = don't exit
