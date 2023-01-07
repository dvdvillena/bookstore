#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     bookListing.py - Book reporting
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import curses
import locale
import os
import sqlite3
import subprocess
import textwrap
from datetime import datetime

import icu
import npyscreen
from npyscreen import fmForm, wgmultiline

import bsWidgets as bs
import config

EXITED_DOWN  =  1   # copied from npyscreen
REMEMBER_FILTERS = config.REMEMBER_FILTERS  # remember the last listing filter subset

TAB = chr(curses.ascii.TAB)
CR  = chr(curses.ascii.CR)
SP  = chr(curses.ascii.SP)
LF  = chr(curses.ascii.LF)

if config.system_release == "10":   LF = ''     # Windows 8.1 notepad program needs LF

helpText = "A listing utility for the book database.\n\n\
* Searching is SQL LIKE-based. Filter fields must not be empty. First items in the filters must be ORs (|), then the NOTs (!=).\n\n\
* A text program will open the report and wait for you to close it to return to the bookstore. \
If config.SAVE_REPORTS=False, automatically deletes the reports after created in the /Reports folder.\n\n\
* Filter syntax allows for:\n\n\
%ab% | %cd%  -> (book_title LIKE '%ab%' OR book_title LIKE '%cd%')\n\n\
!= %ab%      -> (book_title NOT LIKE '%ab%')\n\n\
%a% != %ab%  -> (book_title LIKE '%a%') AND (book_title NOT LIKE '%ab%')\n\n\
%ab% | %cd% != %def%  -> (book_title LIKE '%ab%' OR book_title LIKE '%cd%') AND (book_title NOT LIKE '%def%')\n\n\
%ab% | %cd% != %def% != %efg%  -> (book_title LIKE '%ab%' OR book_title LIKE '%cd%') AND (book_title NOT LIKE '%def%') AND (book_title NOT LIKE '%efg%')\n\n\
!= %ab% %cde% != %fg%  -> (book_title NOT LIKE '%ab% %cde%') AND (book_title NOT LIKE '%fg%')	-> Beware the lacking '!='\n\n"


class BookListingForm(npyscreen.FormBaseNew):
    "Form for the book listing."
    def __init__(self, name="BookListing", parentApp=None, framed=None, help=None, color='FORMDEFAULT',\
    widget_list=None, cycle_widgets=False, ok_button_function=None, cancel_button_function=None, *args, **keywords):

        """ Creates the father, npyscreen.FormBaseNew. """
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets=cycle_widgets, *args, **keywords)

    def create(self):
        """The standard constructor will call the method .create(), which you should override to create the Form widgets."""
        self.framed = True   # framed form
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exitBookListing   # Escape exit
        
        # Form title
        version = config.program_version
        pname, version = config.pname, config.program_version
        self.formTitle = pname + " " + version + " - Book listing "
        self.title = self.add(bs.MyFixedText, name="BookListingTitle", value=self.formTitle,\
            relx=2, rely=0, editable=False)  # Form title line
        #-------------------------------------------------------------------------------------------------------------------------
        self.bookFilterFld = self.add(bs.MyTitleText, name="Book filter:", value="", relx=13,\
            rely=3, begin_entry_at=17, fixed_length=False, editable=True)
        self.bookFilterFld.value = "%"
        self.authorFilterFld = self.add(bs.MyTitleText, name="Author filter:", value="",\
            relx=15, rely=5, begin_entry_at=18, fixed_length=False, editable=True)
        self.authorFilterFld.value = "%"
        self.publisherFilterFld = self.add(bs.MyTitleText, name="Publisher filter:", value="",\
            relx=17, rely=7, begin_entry_at=20, use_two_lines=False, use_max_space=True, fixed_length=False, editable=True)
        self.publisherFilterFld.value = "%"
        self.genreFilterFld = self.add(bs.MyTitleText, name="Book genre filter:", value="",\
            relx=19, rely=9, begin_entry_at=21, use_two_lines=False, use_max_space=True, fixed_length=False, editable=True)
        self.genreFilterFld.value = "%"
        self.warehouseFilterFld = self.add(bs.MyTitleText, name="Warehouse filter:", value="",\
            relx=21, rely=11, begin_entry_at=22, use_two_lines=False, use_max_space=True, fixed_length=False, editable=True)
        self.warehouseFilterFld.value = "%"
        #-------------------------------------------------------------------------------------------------------------------------
        self.infoTxt = self.add(bs.MyMultiLineEdit, name="", value="", relx=5, rely=13, max_height=5, editable=False)
        info = "          Filters are case-insensitive" + CR + \
               "          % wildcard: Represents zero or more characters" + CR + \
               "          _ wildcard: Represents a single character" + CR + \
               "OR operator: %Pérez% | %Galdós% -> LIKE %Pérez% OR LIKE %Galdós%" + CR + \
               "NOT operator: %Pérez% != %Galdós% -> LIKE %Pérez% AND NOT LIKE %Galdós%"
        self.infoTxt.value = info
        #-------------------------------------------------------------------------------------------------------------------------
        self.orderValues = [("Book title",),("Author and title",),("Publisher and title",),("Genre and title",),("Warehouse and title",)]
        self.orderFld = self.add(bs.TitleChooser, name="Order by:", value="", values=self.orderValues, popupType="narrow",\
            relx=21, rely=19, begin_entry_at=12, use_max_space=False, max_width=34, editable=True)
        self.orderLabel=self.add(bs.MyFixedText, name="OrderLabel", value="[+]", relx=56, rely=19, min_width=4, max_width=4, \
            min_height=0, max_height=0, use_max_space=False, editable=False)
        #-------------------------------------------------------------------------------------------------------------------------
        self.ok_button=self.add(bs.MyMiniButtonPress, name="Generate listing", relx=18, rely=21, editable=True)
        self.ok_button.when_pressed_function = self.Generatebtn_function
        self.cancel_button=self.add(bs.MyMiniButtonPress, name="Cancel", relx=46, rely=21, editable=True)
        self.cancel_button.when_pressed_function = self.Cancelbtn_function
        
        self.statusLine=self.add(npyscreen.FixedText, name="BookListingStatus", value="", relx=2, rely=23, use_max_space=True, editable=False)
        self.statusLine.value = "Input values for filtered listing of books"

    def initialize(self):
        "Initializes the form. Called from main menu."
        if not REMEMBER_FILTERS:
            self.bookFilterFld.value = "%"
            self.authorFilterFld.value = "%"
            self.publisherFilterFld.value = "%"
            self.genreFilterFld.value = "%"
            self.warehouseFilterFld.value = "%"
            self.orderFld.value = self.orderValues[0][0]   # "Book title" by default

    def Generatebtn_function(self):
        "Generate button function."
        self.strip_fields()     # Get rid of spaces
        error = self.check_fields_values()
        if error:
            self.error_message(error)
            return
        else:
            self.generateListing()

    def Cancelbtn_function(self):
        "Cancel button function."
        self.exitBookListing()

    def get_editw_number(self, fieldName):
        "Returns the .editw number of fieldName"
        curses.flushinp()
        for w in self._widgets_by_id:
            if self._widgets_by_id[w].name == fieldName:
                return w

    def check_fields_values(self):
        "Checking for wrong values in the fields."

        # Fields cannot be empty
        emptyField = False
        if self.bookFilterFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Book filter:") - 1
        elif self.authorFilterFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Author filter:") - 1
        elif self.publisherFilterFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Publisher filter:") - 1
        elif self.genreFilterFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Book genre filter:") - 1
        elif self.warehouseFilterFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Warehouse filter:") - 1
        elif self.orderFld.value == "":
            emptyField = True
            self.editw = self.get_editw_number("Order by:") - 1
        if emptyField:
            self.ok_button.editing = False
            errorMsg = "Error:  Mandatory field is empty"
            return errorMsg

        if (self.orderFld.value.strip(),) not in self.orderValues:
            self.ok_button.editing = False
            errorMsg = "Error:  Wrong order"
            self.editw = self.get_editw_number("Order by:") - 1
            return errorMsg

    def error_message(self, errorMsg):
        self.statusLine.value = errorMsg
        self.statusLine.display()
        curses.beep()

    def strip_fields(self):
        "Required trimming of spaces."
        self.bookFilterFld.value = self.bookFilterFld.value.strip()
        self.authorFilterFld.value = self.authorFilterFld.value.strip()
        self.publisherFilterFld.value = self.publisherFilterFld.value.strip()
        self.genreFilterFld.value = self.genreFilterFld.value.strip()
        self.warehouseFilterFld.value = self.warehouseFilterFld.value.strip()

    def get_field_list(self, field):
        "Returns a list from an enumeration text field."
        fieldList = field.split(",")
        if len(fieldList) > 1:
            for index, elem in enumerate(fieldList):
                elem = elem.strip()
                fieldList[index] = elem
            non_duplicates_list = list(dict.fromkeys(fieldList))
            non_duplicates_list.sort()
            fieldList = non_duplicates_list
        return fieldList
    
    def get_fieldLikeSentence(self, field):
        "Returns a LIKE sentence for a specific field."
        """
        Filter fields cannot be empty. They can contain alphanumeric, percent, comma and dot.
        First items in the filters must be the ORs, then the NOTs.\n\
        Filter syntax:
        %ab% | %cd%						-> (book_title LIKE '%ab%' OR book_title LIKE '%cd%')
        != %ab%							-> (book_title NOT LIKE '%ab%')
        %a% != %ab%						-> (book_title LIKE '%a%') AND (book_title NOT LIKE '%ab%') 
        %ab% | %cd% != %def% 			-> (book_title LIKE '%ab%' OR book_title LIKE '%cd%') AND (book_title NOT LIKE '%def%')
        %ab% | %cd% != %def% != %efg%	-> (book_title LIKE '%ab%' OR book_title LIKE '%cd%') AND (book_title NOT LIKE '%def%') AND (book_title NOT LIKE '%efg%')
        != %ab% %cde% != %fg%			-> (book_title NOT LIKE '%ab% %cde%') AND (book_title NOT LIKE '%fg%')	-> Beware the lacking !=
        """

        if field.name == "Book filter:":
            tablefld = "'bookstore.Book'.book_title"
        elif field.name == "Author filter:":
            tablefld = "'bookstore.Author'.name"
        elif field.name == "Publisher filter:":
            tablefld = "'bookstore.Publisher'.name"
        elif field.name == "Book genre filter:":
            tablefld = "'bookstore.Book'.genre_id"
        elif field.name == "Warehouse filter:":
            tablefld = "'bookstore.Warehouse'.code"

        # First, we upper() the NOTs and ORs:
        fvalue = field.value.replace("not", "NOT").replace("or", "OR")

        # Get the NOT_list:
        NOT_list = []
        fieldList = fvalue.split("!=")
        fieldList = fieldList[1:]   # There's a '!=' or something else: discarded
        for elem in fieldList:
            elem = elem.strip()
            NOT_list.append(elem)
        
        # Get the OR_list:
        OR_list = []
        fieldList = fvalue.split("!=")
        if fieldList[0] != "":  # Not begins by '!=', so it's OR
            
            fieldList = fieldList[0].split("|")  # get rid of NOTs and split

            for elem in fieldList:
                elem = elem.strip()
                OR_list.append(elem)
        
        # Build the fieldLikeSentence
        fieldLikeSentence = "("     # first parentheses

        # OR part of fieldLikeSentence
        if len(OR_list) > 0:
            first_elem = True
            for elem in OR_list:
                if first_elem == False:
                    fieldLikeSentence += " OR "
                fieldLikeSentence += tablefld + " LIKE '" + elem + "'"
                first_elem = False
            fieldLikeSentence += ")"

        # NOT part of fieldLikeSentence
        if len(NOT_list) > 0:
            if len(OR_list) > 0:
                fieldLikeSentence += " AND ("
            first_elem = True
            for elem in NOT_list:
                if first_elem == False:
                    fieldLikeSentence += " AND ("
                fieldLikeSentence += tablefld + " NOT LIKE '" + elem + "')"
                first_elem = False

        return fieldLikeSentence

    def generateListing(self):
        "Search and list books."

        conn = config.conn 
        cur = conn.cursor()

        flist = "'bookstore.Book'.book_title, 'bookstore.Author'.name, 'bookstore.Book'.year, 'bookstore.Publisher'.name, \
            'bookstore.Warehouse'.code, 'bookstore.Book'.genre_id"
        
        bookLikeSentence = self.get_fieldLikeSentence(self.bookFilterFld)
        if bookLikeSentence == False:
            bs.notify_OK("\n   Syntax error in book filter.  \n","Message", form_color='STANDOUT', wrap=True, wide=False)
            self.editw = self.get_editw_number("Book filter:") - 1
            return
        authorLikeSentence = self.get_fieldLikeSentence(self.authorFilterFld)
        if authorLikeSentence == False:
            bs.notify_OK("\n   Syntax error in author filter.  \n","Message", form_color='STANDOUT', wrap=True, wide=False)
            self.editw = self.get_editw_number("Author filter:") - 1
            return
        publisherLikeSentence = self.get_fieldLikeSentence(self.publisherFilterFld)
        if publisherLikeSentence == False:
            bs.notify_OK("\n   Syntax error in publisher filter.  \n","Message", form_color='STANDOUT', wrap=True, wide=False)
            self.editw = self.get_editw_number("Publisher filter:") - 1
            return
        genreLikeSentence = self.get_fieldLikeSentence(self.genreFilterFld)
        if genreLikeSentence == False:
            bs.notify_OK("\n   Syntax error in genre filter.  \n","Message", form_color='STANDOUT', wrap=True, wide=False)
            self.editw = self.get_editw_number("Book genre filter:") - 1
            return
        warehouseLikeSentence = self.get_fieldLikeSentence(self.warehouseFilterFld)
        if warehouseLikeSentence == False:
            bs.notify_OK("\n   Syntax error in warehouse filter.  \n","Message", form_color='STANDOUT', wrap=True, wide=False)
            self.editw = self.get_editw_number("Warehouse filter:") - 1
            return

        if self.warehouseFilterFld.value == "%":
            warehouseLikeSentence = warehouseLikeSentence[:-1] + " OR 'bookstore.Warehouse'.code IS NULL)"  # adjustment for books with no warehouses
        else:
            warehouseLikeSentence = warehouseLikeSentence[:-1] + ")"

        # To distinguish between lines with same title, different publisher:
        groupSentence = " GROUP BY 'bookstore.Book'.book_title, 'bookstore.Book'.publisher_num, 'bookstore.Book_warehouse'.warehouse_num"

        orderSentence = " ORDER BY "
        
        if self.orderFld.value == "Book title":
            orderBy = "book title"
            orderSentence += "'bookstore.Book'.book_title"
        elif self.orderFld.value == "Author and title":
            orderBy = "author"
            orderSentence += "'bookstore.Author'.name, 'bookstore.Book'.book_title"
        elif self.orderFld.value == "Publisher and title":
            orderBy = "publisher"
            orderSentence += "'bookstore.Publisher'.name, 'bookstore.Book'.book_title"
        elif self.orderFld.value == "Genre and title":
            orderBy = "genre"
            orderSentence += "'bookstore.Book'.genre_id, 'bookstore.Book'.book_title"
        elif self.orderFld.value == "Warehouse and title":
            orderBy = "warehouse"
            orderSentence += "'bookstore.Warehouse'.code, 'bookstore.Book'.book_title"
        else:
            orderBy = "book title"

        sqlQuery = "SELECT "+flist+" FROM 'bookstore.Book_author' \
            INNER JOIN 'bookstore.Book' ON 'bookstore.Book'.numeral = 'bookstore.Book_author'.book_num \
            INNER JOIN 'bookstore.Author' ON 'bookstore.Author'.numeral = 'bookstore.Book_author'.author_num \
            INNER JOIN 'bookstore.Publisher' ON 'bookstore.Publisher'.numeral = 'bookstore.Book'.publisher_num \
            LEFT JOIN 'bookstore.Book_warehouse' ON 'bookstore.Book_warehouse'.book_num = 'bookstore.Book_author'.book_num \
            LEFT JOIN 'bookstore.Warehouse' ON 'bookstore.Warehouse'.numeral = 'bookstore.Book_warehouse'.warehouse_num \
            WHERE " + bookLikeSentence + " AND " + authorLikeSentence + " AND " + publisherLikeSentence + \
            " AND " +  genreLikeSentence + " AND " + warehouseLikeSentence + groupSentence + orderSentence

        try:
            cur.execute(sqlQuery)
            conn.commit()
            rows = cur.fetchall()
        except sqlite3.OperationalError as e:
            bs.notify_OK("\n    sqlite3.OperationalError: \n"+str(e),"Message", form_color='STANDOUT', wrap=True, wide=False)
            return

        report = ""

        # Listing header
        book_title = "Book title".ljust(34)
        author = "Author".ljust(26)
        year = "Year".ljust(6)
        publisher = "Publisher".ljust(24)
        warehouse = "Warehouse".ljust(24)
        genre = "Genre".ljust(11)
        header = book_title + author + year + publisher + warehouse + genre + CR + LF + "-" * 125 + CR + LF
        
        report += header

        # Compress and combine same book with different warehouses
        compress_dict = {}

        for row in rows:

            title = row[0]
            author = row[1]
            year = row[2]
            publisher = row[3]
            warehouse = row[4]
            genre = row[5]

            if orderBy == "book title":
                index = title + "_" + publisher
            elif orderBy == "author":
                index = author + "_" + title + "_" + publisher
            elif orderBy == "publisher":
                index = publisher + "_" + title
            elif orderBy == "genre":
                index = str(genre) + "_" + title + "_" + publisher
            elif orderBy == "warehouse":
                index = warehouse
                if index == None:
                    index = "None_" + title + "_" + publisher
                else:
                    index = warehouse + "_" + title + "_" + publisher

            if orderBy != "warehouse":  # can compress books by warehouse
                try:
                    if compress_dict[index]:
                        try:
                            wrhouse = compress_dict[index][4] + ", " + warehouse
                        except TypeError:   # it's None
                            wrhouse = ""
                    new_row = (title, author, year, publisher, wrhouse, genre)
                    compress_dict[index] = new_row
                except KeyError:
                    compress_dict[index] = row
            else:
                compress_dict[index] = row

        rows = list(compress_dict.values())
        
        # ICU ordering of the ordering field
        # We need PyICU (=icu) to order unicode strings in Spanish, Catalan, French...
        collator = icu.Collator.createInstance(icu.Locale(locale.getlocale()[0]))

        if orderBy == "book title":
            index_list = [i[0] + "_" + i[3] for i in rows]
        elif orderBy == "author":
            index_list = [i[1] + "_" + i[0] + "_" + i[3] for i in rows]
        elif orderBy == "publisher":
            index_list = [i[3] + "_" + i[0] for i in rows]
        elif orderBy == "genre":
            index_list = [str(i[5]) + "_" + i[0] + "_" + i[3] for i in rows]
        elif orderBy == "warehouse":
            index_list = []
            for i in rows:
                if i[4] == None:
                    index_list.append("None_" + i[0] + "_" + i[3])
                else:
                    index_list.append(i[4]+"_" + i[0] + "_" + i[3])

        index_list.sort(key=collator.getSortKey)

        new_rows = []
        for item in index_list:
            new_rows.append(compress_dict[item])

        for row in new_rows:
            book_title = row[0][:33].ljust(34)
            author = row[1][:25].ljust(26)
            year = str(row[2])[:6].ljust(6)
            publisher = row[3][:23].ljust(24)
            if row[4] != None:
                warehouse = row[4][:23].ljust(24)
            else:
                warehouse = "".ljust(24)

            genre = config.genreList[row[5] - 1].ljust(11)
            
            report += book_title + author + year + publisher + warehouse + genre + CR + LF
        
        report += "-" * 125 + CR + LF   # final line

        # Text file creation
        DataPath = config.dataPath + "Reports/"
        now = datetime.now().strftime('%Y%m%d%H%M%S.%f')[2:-7]
        filename = DataPath + "book_listing-" + now + ".txt"
        try:
            with open(filename, 'w') as f:
                f.write(report)
        except FileNotFoundError:
            message = "The report directory does not exist."
            if bs.notify_ok_cancel(message, title="", wrap=True, editw = 1,):
                self.exitBookListing()

        # Text file display through an external app
        viewer = config.textViewer

        #subprocess.Popen([viewer, filename])   # doesn't wait for completion
        subprocess.run([viewer, filename])      # waits for completion (closing)
        if not config.SAVE_REPORTS:
            try:
                os.remove(filename)
            except FileNotFoundError:   # whatever
                pass

    def exitBookListing(self):
        config.parentApp.setNextForm("MAIN")
        config.parentApp.switchFormNow()

    def textfield_exit(self):
        "Exit from a text field with Escape"
        pass    # do nothing = don't exit

    def view_report(self, report, title="Report", form_color="STANDOUT", scroll_exit=False, autowrap=False):
        "Optional on-terminal report viewer."
        F = fmForm.Form(name=title, color=form_color)
        mlw = F.add(wgmultiline.Pager, scroll_exit=True, autowrap=autowrap)
        mlw_width = mlw.width-1
    
        report_lines = []
        for line in report.splitlines():
            line = textwrap.wrap(line, mlw_width)
            if line == []:
                report_lines.append('')
            else:
                report_lines.extend(line)
        mlw.values = report_lines
        F.edit()
        del mlw
        del F

    def widget_was_exited(self):
        "Hooked from bs.MyTextfield.h_exit_up() and h_exit_down()."
        if self.bookFilterFld.value.strip() == "":
            self.bookFilterFld.value = "%"
        if self.authorFilterFld.value.strip() == "":
            self.authorFilterFld.value = "%"
        if self.publisherFilterFld.value.strip() == "":
            self.publisherFilterFld.value = "%"
        if self.genreFilterFld.value.strip() == "":
            self.genreFilterFld.value = "%"
        if self.warehouseFilterFld.value.strip() == "" :
            self.warehouseFilterFld.value = "%"

    def is_editable_field(self, widget=None):
        "Hooked from bs.MyAutocomplete.filter_char()"
        if widget.name == "Order by:" :
            return True
        else:
            return False

    def create_popup_window(self, widget=None):
        "Hooked from bs.MyAutocomplete.get_choice()"
        if widget.name == "Order by:":
            tmp_window = bs.MyPopup(self, name=widget.name, framed=True, show_atx=42, show_aty=13, columns=32, lines=10, shortcut_len=None)
        return tmp_window

    def scan_value_in_list(self, widget=None):
        "Hook from bs.MyAutocomplete.when_check_value_changed()"
        widget_value = widget.value
        if widget.name == "Order by:" :
            if widget.cursor_position != 0:
                widget_value = widget.value[:widget.cursor_position]
                found_value = widget.find_value_literal(widget_value)
                if found_value != widget_value:     # not found
                    widget_value = found_value
        return widget_value

    def get_parentField(self, widget=None):
        "Hook from bs.MyPopup.__init__()"
        parentField = None
        if widget.name == "Order by:" :
            parentField = self.orderFld
        return parentField 

