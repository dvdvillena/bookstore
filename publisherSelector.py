#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     publisherSelector.py - Selector and options for publisher maintenance
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################
# Form with the following widgets:
#   .editw = 0 --> screen title
#   .editw = 1 --> record grid
#   .editw = 2 --> bottom line with status literal and options
#   .editw = 3 --> 1-letter option input field
#   .editw = 4 --> Detail input field for 3-digit Numeral, and for search literal, initially hidden
##############################################################################

import datetime
import sqlite3
import time

import npyscreen
import numpy

import bsWidgets as bs
import config
from config import SCREENWIDTH as WIDTH
from publisher import PublisherForm

REMEMBER_ROW = True    # remember the last row selected when coming from main menu
REMEMBER_SUBSET = config.REMEMBER_SUBSET  # remember the last found subset
DATEFORMAT = config.dateFormat  # program-wide
FIELD_LIST = ["numeral", "name", "address", "phone", "url"]     # only screen fields
DBTABLENAME = "'bookstore.Publisher'"

helpText =  "Another record selector screen for the publishers.\n\n" \
    "* There is not much more to add to what has already been said about the other selectors. " \
    "Please see the Books and Authors help screens.\n\n" \
    "* The book record only stores the numeral value of the Publisher."


class PublisherSelectForm(npyscreen.FormBaseNew):
    "Publisher selector and FCRUD options."
    def __init__(self, name="", parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None, \
        cycle_widgets=True, *args, **keywords):
        # Creates the father, npyscreen.FormBaseNew.
        config.parentApp = parentApp
        
        # goes to _FormBase:
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

    def create(self):
        "The standard constructor will call the method .create(), which you should override to create the Form widgets."
        self.framed = False   # frameless form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exitPublisherSelector   # Escape exit
        
        # Form title - Screen title line
        pname, version = config.pname, config.program_version
        self.form_title = pname + " " + version + " - Publisher selector"
        self.today = self.get_today()
        self.formTitle=self.add(bs.MyTextfield, name="PublisherTitle", value=None, relx=0, rely=0, \
            use_max_space=True, width=WIDTH, max_width=WIDTH, maximum_string_length=WIDTH, editable=False)

        # Publishers Grid
        self.grid = bs.MyGrid(screen=self, name="PublisherGrid")      # (All attributes get filled later)
        self.grid.editing=True
        self.columnTitles = ["Numeral","     Name","   Address"," Phone","   URL"]
        self.col_widths = [8, 28, 21, 12, 11]    # fields must add up to WIDTH

        self.grid = self.add(self.grid.__class__, name="PublisherGrid", col_titles=self.columnTitles, col_widths=self.col_widths, \
                relx=0, rely=1, height=22, width=WIDTH, min_height=22, min_width=WIDTH, editable=True, hidden=False, \
                values=None, select_whole_line=True, always_show_cursor=True, column_width=14)
        
        # Status and Options bottom line
        self.optionsLiteral="[Tab] option:     F=Find   C=Create   R=Read   U=Update   D=Delete     Esc=Quit"
        self.statusLiteral = self.optionsLiteral
        self.statusLine = self.add(bs.MyTextfield, name="statusLine", value=self.statusLiteral, relx=0, rely=24, \
            use_max_space=True, width=WIDTH, max_width=WIDTH, maximum_string_length=WIDTH, min_height=0, max_height=0, editable=False)
        # For the Find option
        self.findStatusLiteral = "Search literal (or field:literal):                            -> Empty=full set"
        
        # Option input field, automatic 1-character
        self.inputOpt = self.add(bs.OptionField, name='OptionFld', value="", relx=14, rely=24,
                                        width=0, height=0, max_width=3, max_height=0, editable=True, use_max_space=True)
        self.inputOpt.value = ""
        self.inputOpt.check_value_change=True

        # Detail input field for 3-digit numeral, and also for Find-literal
        self.inputDetail = self.add(bs.DetailField, screenForm=PublisherForm, name='DetailFld', value="", relx=26, rely=24,
                                        width=5, height=0, max_width=5, max_height=0, 
                                        editable=True, hidden=True, use_max_space=True)

    def set_up_title(self, filerows, full_set=None):
        "Build the screen title"
        if full_set == True:
            self.formTitle.value = self.form_title + " - Full set: " + str(len(filerows)) + " rows"
        else:
            self.formTitle.value = self.form_title + " - [Find] subset: " + str(len(filerows)) + " rows"
        self.formTitle.value = self.formTitle.value + " "*(WIDTH - len(self.formTitle.value) - len(self.today)) + self.today

    def get_today(self):
        "For the screen title line."
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
            empty_list = [["","","","",""]]
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
            name = row[2]
            address = row[3]
            phone = row[4]
            url = row[5]
            cRow = [id, numeral, name, address, phone, url]
            rows.append(cRow)    # including Publisher.id
        self.set_up_title(filerows, full_set=True)
        return rows # it's a list of lists

    def fill_grid(self):
        "Read the DB table and put it into the grid."
        config.fileRows = self.readDBTable()        # full row set: it's a list of lists
        self.screenFileRows = self.getRowListForScreen(config.fileRows)     # it's a list of lists
        self.grid.values = self.screenFileRows

    def update_grid(self):
        "Updates the affected row in the publisher grid and RAM config table list."
        # After a change or creation, grid displays full set :
        if not REMEMBER_SUBSET or config.last_table != DBTABLENAME or \
                (config.last_table == DBTABLENAME and config.last_operation == "Create") :
            self.fill_grid()
            config.last_table = DBTABLENAME
        else:   # remember Find subset
            if config.fileRow is not None:  # it's not initializing
                for row in config.fileRows:
                    if row[0] == config.fileRow[0]:     # ID field
                        row[1] = config.fileRow[1]      # update grid row
                        row[2] = config.fileRow[2]
                        row[3] = config.fileRow[3]
                        row[4] = config.fileRow[4]
                        row[5] = config.fileRow[5]
                        break
                screenFileRows = self.getRowListForScreen(config.fileRows)
                self.grid.values = screenFileRows
                self.set_up_title(config.fileRows, full_set=False)
        if not REMEMBER_ROW:
            self.grid.set_highlight_row(None)    # select the first one
    
    def create_row(self):
        "It's been keypressed C/c=Create."
        # Lets display the empty publisher form:
        self.inputDetail.option = "Create"
        self.inputOpt.value = "C"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the C
        # Disable options input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        self.grid.editing = False
        self.inputDetail.relx = 26  # just in case
        self.ask_option()  # for when we get back to this screen

        config.parentApp.setNextForm("PUBLISHER")
        config.parentApp.switchFormNow()
        PublisherForm.set_createMode()

    def read_row(self):
        "It's been keypressed R/r=Read."
        # (Must ask to confirm the searched numeral)
        self.inputDetail.option = "Read"
        self.inputOpt.value = "R"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the R
        # Disable options input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        
        # Reset former status line field
        self.statusLiteral = "Enter numeral to read:" + (59 * " ")
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.value = self.statusLiteral
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 5
        self.inputDetail.max_width = 5
        self.inputDetail.maximum_string_length = 3
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exit
        self.inputDetail.how_exited = True     # self.find_next_editable, to default value
        self.editw = 4      # Change to numeral input field

        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def update_row(self):
        "It's been keypressed U/u=Update."
        # (Must ask to confirm the searched numeral)
        self.inputDetail.option = "Update"
        self.inputOpt.value = "U"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the U
        # Disable options input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True
        
        # Reset former status line field
        self.statusLiteral = "Enter numeral to update:" + (57 * " ")
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.value = self.statusLiteral
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 5
        self.inputDetail.max_width = 5
        self.inputDetail.maximum_string_length = 3
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exit
        self.inputDetail.how_exited = True     # self.find_next_editable, to default value
        self.editw = 4      # Change to numeral input field
        
        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()
    
    def find_row(self):
        "It's been keypressed F/f=Find."
        # (Must ask the searched literal)
        self.inputDetail.option = "Find"
        self.inputOpt.value = "F"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the F
        # Disable options input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True

        # Reset former status line field
        self.statusLiteral = self.findStatusLiteral
        self.statusLine.relx=0
        self.statusLine.width=36
        self.statusLine.max_width=36
        self.statusLine.value = self.statusLiteral
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
        self.inputDetail.editing = True    # grid exit
        self.inputDetail.how_exited = True     # self.find_next_editable, to default value
        self.editw = 4      # Change to literal input field

        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def delete_row(self):
        "It's been keypressed D/d=Delete."
        # (Must ask to confirm the searched numeral to delete)
        self.inputDetail.option = "Delete"
        self.inputOpt.value = "D"
        self.inputOpt.display()
        time.sleep(0.1)     # shows the D
        # Disable options input field
        self.inputOpt.editing = False
        self.inputOpt.editable = False
        self.inputOpt.hidden = True

        # Reset former status line field
        self.statusLiteral = "Enter numeral to delete:" + (57 * " ")
        self.statusLine.relx=0
        self.statusLine.width=79
        self.statusLine.max_width=79
        self.statusLine.value = self.statusLiteral
        self.statusLine.update(clear=True)
        self.statusLine.display()

        self.grid.editing = False

        searchedNumeral = config.currentRow
        self.inputDetail.hidden = False
        self.inputDetail.editable = True
        self.inputDetail.relx = 26
        self.inputDetail.width = 5
        self.inputDetail.max_width = 5
        self.inputDetail.maximum_string_length = 3
        self.inputDetail.value = str(searchedNumeral)
        self.inputDetail.check_value_change=True
        self.inputDetail.editing = True    # grid exit
        self.inputDetail.how_exited = True     # self.find_next_editable, to default value
        self.editw = 4      # Change to numeral input field
        
        self.edit() # waiting for Enter/Esc in the field -see its method get_and_use_key_press()

    def read_record(self, numeral):
        "Search for the required record and store it in a reachable variable. Called from the Detail-field widget."
        config.screenRow = 0
        config.fileRow = []
        for row in config.fileRows:
            if row[1] == numeral:
                cur = config.conn.cursor()
                while True:     # multiuser DB locking loop
                    try:
                        # I could just use .append(row[0]) below, but I read again to allow for record locking
                        sqlQuery = "SELECT * FROM " + DBTABLENAME + " WHERE numeral=?"
                        cur.execute(sqlQuery, (str(numeral),) )
                        break   # go on
                    except sqlite3.OperationalError:
                        bs.notify_OK("\n    Database is locked, please wait.", "Message")
                filerow = cur.fetchone()
                config.fileRow.append(filerow[0])
                config.fileRow.append(filerow[1])
                config.fileRow.append(filerow[2])
                config.fileRow.append(filerow[3])
                config.fileRow.append(filerow[4])
                config.fileRow.append(filerow[5])
                self.grid.edit_cell = [config.screenRow, 0]  # highlight the selected row
                # If the searched index is greater than the first index displayed on screen
                if config.screenRow > self.grid.begin_row_display_at:
                    self.grid.ensure_cursor_on_display_down_right(None)
                else:   # If the searched index is smaller than the first index displayed on screen
                    self.grid.ensure_cursor_on_display_up(None)
                return True
            config.screenRow += 1
        return False    # not found

    def exitPublisherSelector(self):
        "Escape key was pressed: isinstance(self, PublisherSelectForm) = True; we always come from the OptionField."
        get_out = False
        if self.statusLine.value != self.optionsLiteral:    # it's not the options statusline; it's the numeral field
            # we come from DetailField : we must restore the options statusline and get back to the OptionField
            self.hide_detail()
            self.ask_option()
        else:           # we come from the OptionField, we must exit to the main menu
            self.inputOpt.value = ""
            self.inputOpt.update(clear=True)
            self.ask_option()  # in case we'll return from main menu
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

    def find_DB_rows(self, find_literal):
        "SQL-Based Find function: Executes SQL query for Find option."
        # Accepting:
        #   - A literal without ":" (searches in all the field/columns).
        #   - A literal with ":" like in field:searched_literal.
        #   - Date literals with "/" or "-" separators.
        #   - A literal with one comparator "</>" only after field:>searched_literal.
        field = False
        if ":" in find_literal:     # like, simplifying
            pos = find_literal.find(":")
            field_list = FIELD_LIST
            field = find_literal[:pos]
            literal = find_literal[pos+1:]
            if field.lower() not in field_list or literal == "":
                bs.notify_OK(" Find: Wrong field or literal", "Message")
                return False
        else:
            literal = find_literal

        comparator = False
        if literal[0] in ["=","<",">"]:
            comparator = literal[0]
            literal = literal[1:]
        if comparator and not field:
            bs.notify_OK(" Find: Must specify 'field:' when using a comparator", "Message")
            return False

        sqlQuery = "SELECT * FROM " + DBTABLENAME + " WHERE "
        if not comparator:
            if field == False:  # no field specified, so search all fields
                whereStr = "numeral LIKE ? OR name LIKE ? OR address LIKE ?" +\
                    " OR phone LIKE ? OR url LIKE ? COLLATE NOCASE ORDER BY numeral"
            else:
                whereStr = field + " LIKE ? COLLATE NOCASE ORDER BY numeral"
        elif comparator:
            whereStr = field + " " + comparator + " ? COLLATE NOCASE ORDER BY numeral"

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
            cRow = [row[0], row[1], row[2], row[3], row[4], row[5]]     # cRow="Converted row"
            rows.append(cRow)    # including Publisher.id
        config.fileRows = rows
        self.screenFileRows = self.getRowListForScreen(config.fileRows)     # it's a list of lists
        self.grid.values = self.screenFileRows
        self.set_up_title(filerows, full_set=False)
        return True

    def textfield_exit(self):
        "Exit from Detail field with Escape"
        self.exitPublisherSelector()
        #pass    # do nothing = don't exit
