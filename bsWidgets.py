#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     bsWidgets.py - npyscreen-based (b)ook(s)tore widgets
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import curses
import datetime
import locale
import sys
import time

import npyscreen
from npyscreen import fmForm
from npyscreen import wggrid as grid
from npyscreen import wgmultiline as multiline
from npyscreen import wgtextbox as textbox

import config
#import inspect
from config import SCREENWIDTH as WIDTH

ALLOW_NEW_INPUT = True
EXITED_UP    = -1
EXITED_DOWN  = 1
RAISEERROR   = 'RAISEERROR'
EXITED_ESCAPE= 127


def notify_ok_cancel(message, title="", form_color='CURSOR_INVERSE', wrap=True, editw = 0,):
    "Display a question message. Returns True if OK button pressed, False if Cancel button pressed."
    curses.flushinp()   # flush all keyboard input at this point
    message = npyscreen.utilNotify._prepare_message(message)
    F   = npyscreen.utilNotify.ConfirmCancelPopup(name=title, color=form_color)
    F.preserve_selected_widget = True
    F.show_aty = 9
    mlw = F.add(npyscreen.wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = npyscreen.utilNotify._wrap_message_lines(message, mlw_width)
    mlw.values = message
    F.editw = editw
    F.edit()
    return F.value

def notify(message, title="Message", form_color='STANDOUT', wrap=True, wide=False,):
    "Display a message for a time, then close it."
    curses.flushinp()   # flush all keyboard input at this point
    message = npyscreen.utilNotify._prepare_message(message)
    if wide:
        F = MiniPopup(name=title, color=form_color)
    else:
        F   = MiniPopup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(npyscreen.wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = npyscreen.utilNotify._wrap_message_lines(message, mlw_width)
    mlw.values = message
    F.display()
    time.sleep(0.6)     # let it be seen

def notify_OK(message, title="Message", form_color='STANDOUT', wrap=True, wide=False, editw = 0,):
    "Display a message until OK button is pressed."
    curses.flushinp()   # flush all keyboard input at this point
    message = npyscreen.utilNotify._prepare_message(message)
    if wide:
        F = npyscreen.fmPopup.PopupWide(name=title, color=form_color)
    else:
        F   = npyscreen.fmPopup.Popup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(npyscreen.wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = npyscreen.utilNotify._wrap_message_lines(message, mlw_width)
    else:
        message = message.split("\n")
    mlw.values = message
    F.editw = editw
    F.edit()


class NotEnoughSpaceForWidget(Exception):
    pass


class MiniPopup(npyscreen.Popup):
    DEFAULT_LINES      = 12
    DEFAULT_COLUMNS    = 51
    SHOW_ATX           = 13
    SHOW_ATY           = 7
    

class MyFixedText(textbox.FixedText):
    "DV: My own version with self.how_exited incorporated."

    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False, invert_highlight_color=True, **keywords):
        super().__init__(screen, value, highlight_color, highlight_whole_widget, invert_highlight_color, **keywords)

        self.how_exited = EXITED_DOWN   # for editw = n


class MyTextfield(textbox.TextfieldBase):
    "My own TextfieldBase, to support Windows/unicode."
    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False, invert_highlight_color=True, fixed_length=True, **keywords):
       
        super().__init__(screen, value, highlight_color, highlight_whole_widget, invert_highlight_color, **keywords)    # to TextfieldBase -> Widget

        self.fixed_length = fixed_length    # added to allow fixed/non-fixed length scrollable fields
    
    def show_brief_message(self, message):
        curses.beep()
        keep_for_a_moment = self.value
        self.value = message
        self.editing=False
        self.display()
        curses.napms(1200)
        self.editing=True
        self.value = keep_for_a_moment

    def when_check_value_changed(self):
        "Manages input length according to self.maximum_string_length"
        if self.fixed_length:   # fixed_length means the field is not horiz-scrollable
            if len(self.value) > self.maximum_string_length:
                self.value = self.value[:self.maximum_string_length]
                # No literal added here.
                self.update(clear=True)
        else:
            pass    # no fixed length means the field is horiz-scrollable

    def filter_char(self, char):
        "Filters some keys for the terminal."

        match char:
            case ( 459 ):       # Numeric pad enter key
                char = 13
            case ( 465 ):       # Numeric pad plus key
                char = 43
            case ( 464 ):       # Numeric pad minus key
                char = 45
            case ( 463 ):       # Numeric pad asterisk key
                char = 42
            case ( 458 ):       # Numeric pad slash key
                char = 47
            case ( 331 ):       # Insert key
                char = False
            case ( 262 ):       # Home key
                pass    # go on
            case ( 339 ):       # Page Up key
                char = False
            case ( 338 ):       # Page Down key - And french Œ !
                char = False
            case ( 358 ):       # End key
                pass    # go on
            case ( curses.ascii.ESC ):       # Escape key
                # numeral/find field :
                if "DetailField" in repr(self):     # Detail field
                    pass    # go on
                elif "MyTextfield" in repr(self):   # "regular" text field
                    pass    # go on
                else:
                    char = False
        return char

    def _get_ch(self):
        """
        >>>---> DV: Heavily modified to display non-ascii characters under Python 3.10
                    (See original in wgwidget.py)
        """
        #try:
        #    # Python3.3 and above - returns unicode
        #    ch = self.parent.curses_pad.get_wch()
        #    self._last_get_ch_was_unicode = True
        #except AttributeError:
            
        # For now, disable all attempt to use get_wch()
        # but everything that follows could be in the except clause above.
        
        # DV: For GNU/Linux:
        if config.system == "Linux":     
        
            # Try to read utf-8 if possible.
            _stored_bytes =[]
            self._last_get_ch_was_unicode = True
            global ALLOW_NEW_INPUT
            if ALLOW_NEW_INPUT == True and locale.getpreferredencoding() == 'UTF-8':
                ch = self.parent.curses_pad.getch()
                if ch <= 127:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                elif ch <= 193:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                # if we are here, we need to read 1, 2 or 3 more bytes.
                # all of the subsequent bytes should be in the range 128 - 191, 
                # but we'll risk not checking...
                elif 194 <= ch <= 223: 
                        # 2 bytes
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif 224 <= ch <= 239: 
                        # 3 bytes 
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                elif 240 <= ch <= 244: 
                        # 4 bytes 
                        _stored_bytes.append(ch) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif ch >= 245:
                    # probably a control character
                    self._last_get_ch_was_unicode = False
                    return ch
                
                ch = bytes(_stored_bytes).decode('utf-8', errors='strict')

            else:
                ch = self.parent.curses_pad.getch()
                self._last_get_ch_was_unicode = False

            # This line should not be in the except clause.
            return ch
        
        # >>> DV: for Windows:
        elif config.system == "Windows":
            if ALLOW_NEW_INPUT == True:
                ch = self.parent.curses_pad.getch()
                rtn_ch = ch
                self._last_get_ch_was_unicode = False
                return rtn_ch

    def get_and_use_key_press(self):    
        "Adapted from class Widget. Substitutes entirely the original function."

        # Enter raw mode. In raw mode, normal line buffering and processing of interrupt, quit, suspend, 
        #     and flow control keys are turned off; characters are presented to curses input functions one by one.
        curses.raw()
        # Enter cbreak mode: normal line buffering is turned off and characters are available to be read one by one.
        curses.cbreak()
        # meta: if flag is True, allow 8-bit characters to be input. If flag is False, allow only 7-bit chars.
        curses.meta(True)
        
        self.parent.curses_pad.keypad(1)
        if self.parent.keypress_timeout:
            curses.halfdelay(self.parent.keypress_timeout)
            ch = self._get_ch()
            if ch == -1:
                return self.try_while_waiting()
        else:
            self.parent.curses_pad.timeout(-1)
            ch = self._get_ch()

        ch = self.filter_char(ch)
        if ch == False:     # Useless keys 
            return

        # handle escape-prefixed rubbish.
        if ch == curses.ascii.ESC:
            #self.parent.curses_pad.timeout(1)
            self.parent.curses_pad.nodelay(1)
            ch2 = self.parent.curses_pad.getch()
            if ch2 != -1: 
                ch = curses.ascii.alt(ch2)
            self.parent.curses_pad.timeout(-1) # back to blocking mode
            #curses.flushinp()

        self.handle_input(ch)
        if self.check_value_change:
            self.when_check_value_changed()
        if self.check_cursor_move:
            self.when_check_cursor_moved()
        
        self.try_adjust_widgets()

    def edit(self):
        self.editing = 1
        if self.cursor_position is False:
            self.cursor_position = 0
            #self.cursor_position = len(self.value or '')
        self.parent.curses_pad.keypad(1)
        
        self.how_exited = False     # self.do_nothing = pass

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        #self.display() # don't uncomment: DetailField escape issue
        self.cursor_position = False
        return self.how_exited, self.value
   
    def display_value(self, value):
        "It's the display_value() from TextfieldBase."
        if value == None:
            return ''
        else:
            try:
                str_value = str(value)
            except UnicodeEncodeError:
                str_value = self.safe_string(value)
                return str_value
            except ReferenceError:                
                return ">*ERROR*ERROR*ERROR*<"
            return self.safe_string(str_value)
   
    def _get_string_to_print(self):
        "From TextfieldBase, adapted to right-screen."
        string_to_print = self.display_value(self.value)

        if not string_to_print:
            return None
       
        string_to_print = string_to_print[self.begin_at:self.maximum_string_length + self.begin_at - self.left_margin]
        
        string_to_print = self.display_value(self.value)[self.begin_at:self.maximum_string_length + self.begin_at - self.left_margin]

        return string_to_print

    def _print(self):
        "Adaptation of _print() from TextfieldBase."

        string_to_print = self._get_string_to_print()

        if not string_to_print:
            if self.parent.name == "BookSelector" or \
                self.parent.name == "AuthorSelector" or \
                self.parent.name == "PublisherSelector" or \
                self.parent.name == "WarehouseSelector" or \
                self.parent.name == "UserSelector" :
                if self.name != "DetailFld":
                    self.value = " "        # DV: for empty fields of selector-grids, to get a full highlighted row
                    string_to_print = " "   # DV: for empty fields of selector-grids, to get a full highlighted row
                else:
                    return None
            else:
                return None

        string_to_print = string_to_print[self.begin_at:self.maximum_string_length + self.begin_at - self.left_margin]
        
        string_to_print = self.display_value(self.value)[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        
        column = 0
        place_in_string = 0
        if self.syntax_highlighting:
            self.update_highlighting(start=self.begin_at, end=self.maximum_string_length+self.begin_at-self.left_margin)
            while column <= (self.maximum_string_length - self.left_margin):
                if not string_to_print or place_in_string > len(string_to_print)-1:
                    break
                width_of_char_to_print = self.find_width_of_char(string_to_print[place_in_string])
                if column - 1 + width_of_char_to_print > self.maximum_string_length:
                    break 
                try:
                    highlight = self._highlightingdata[self.begin_at+place_in_string]
                except:
                    highlight = curses.A_NORMAL                
                self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin, 
                    self._print_unicode_char(string_to_print[place_in_string]), 
                    highlight
                    )
                column += self.find_width_of_char(string_to_print[place_in_string])
                place_in_string += 1
        else:
            if self.do_colors():
                if self.show_bold and self.color == 'DEFAULT':
                    color = self.parent.theme_manager.findPair(self, 'BOLD') | curses.A_BOLD
                elif self.show_bold:
                    color = self.parent.theme_manager.findPair(self, self.color) | curses.A_BOLD
                elif self.important:
                    color = self.parent.theme_manager.findPair(self, 'IMPORTANT') | curses.A_BOLD
                else:
                    color = self.parent.theme_manager.findPair(self)
            else:
                if self.important or self.show_bold:
                    color = curses.A_BOLD
                else:
                    color = curses.A_NORMAL

            while column <= (self.maximum_string_length - self.left_margin):
                if not string_to_print or place_in_string > len(string_to_print)-1:
                    if self.highlight_whole_widget:
                        if (self.relx+column+self.left_margin < WIDTH):    # DV: modified
                            self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin, 
                                ' ', 
                                color
                                )
                        column += width_of_char_to_print
                        place_in_string += 1
                        continue
                    else:
                        break

                width_of_char_to_print = self.find_width_of_char(string_to_print[place_in_string])
                if column - 1 + width_of_char_to_print > self.maximum_string_length:
                    break

                self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin,
                    self._print_unicode_char(string_to_print[place_in_string]), 
                    color
                    )

                column += width_of_char_to_print
                place_in_string += 1
            pass
        

    ###########################################################################################
    # Handlers and methods

    def set_up_handlers(self):
        "Adapted from npyscreen.Textfield"
        super(MyTextfield, self).set_up_handlers()    
    
        # For OS X
        del_key = curses.ascii.alt('~')
        
        self.handlers.update({curses.KEY_LEFT:    self.h_cursor_left,
                           curses.KEY_RIGHT:   self.h_cursor_right,
                   curses.KEY_DC:      self.h_delete_right,
                   curses.ascii.DEL:   self.h_delete_left,
                   curses.ascii.BS:    self.h_delete_left,
                   curses.KEY_BACKSPACE: self.h_delete_left,
                   # mac os x curses reports DEL as escape oddly
                   # no solution yet                   
                   "^K":              self.h_erase_right,
                   "^U":              self.h_erase_left,
                   curses.ascii.ESC:  self.h_escape_exit,
                   curses.KEY_HOME:   self.h_cursor_home,
                   curses.KEY_END:    self.h_cursor_end,
                   curses.KEY_F1:     self.parent.h_display_help,
            })

        self.complex_handlers.extend((
                        (self.t_input_isprint, self.h_addch),
                        # (self.t_is_ck, self.h_erase_right),
                        # (self.t_is_cu, self.h_erase_left),
                        ))

    def t_input_isprint(self, inp):
        # DV: for Linux:
        if config.system == "Linux":
            if self._last_get_ch_was_unicode and inp not in '\n\t\r':
                return True
            if curses.ascii.isprint(inp) and \
            (chr(inp) not in '\n\t\r'): 
                return True
            else: 
                return False
        # DV: for Windows:
        elif config.system == "Windows":
            if chr(inp).isprintable():
                return True
            else:
                return False        
        
    def h_addch(self, inp):
        "Copied from npyscreen.Textfield"
        if self.editable:
            #self.value = self.value[:self.cursor_position] + curses.keyname(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.keyname(input))
            
            # workaround for the metamode bug:
            if self._last_get_ch_was_unicode == True and isinstance(self.value, bytes):
                # probably dealing with python2.
                ch_adding = inp
                self.value = self.value.decode()
            elif self._last_get_ch_was_unicode == True:
                ch_adding = inp
            else:
                try:
                    ch_adding = chr(inp)
                except TypeError:
                    ch_adding = input
            self.value = self.value[:self.cursor_position] + ch_adding \
                + self.value[self.cursor_position:]
            self.cursor_position += len(ch_adding)

            # or avoid it entirely:
            #self.value = self.value[:self.cursor_position] + curses.ascii.unctrl(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.ascii.unctrl(input))

    def h_exit_up(self, _input):
        """Called when user leaves the widget to the previous widget"""
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_UP
        try:
            self.parent.widget_was_exited()  # for bookListing.py
        except AttributeError:
            pass

    def h_exit_down(self, _input):
        """Called when user leaves the widget to the next widget"""
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_DOWN
        try:
            self.parent.widget_was_exited()  # for bookListing.py
        except AttributeError:
            pass
   
    def h_cursor_left(self, input):
        self.cursor_position -= 1

    def h_cursor_right(self, input):
        self.cursor_position += 1

    def h_delete_left(self, input):
        if self.editable and self.cursor_position > 0:
            self.value = self.value[:self.cursor_position-1] + self.value[self.cursor_position:]
        
        self.cursor_position -= 1
        self.begin_at -= 1
    
    def h_delete_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position] + self.value[self.cursor_position+1:]

    def h_erase_left(self, input):
        if self.editable:
            self.value = self.value[self.cursor_position:]
            self.cursor_position=0
    
    def h_erase_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position]
            self.cursor_position = len(self.value)
            self.begin_at = 0
    
    def h_cursor_home(self, input):
        self.cursor_position = 0
        
    def h_cursor_end(self, input):
        self.cursor_position = len(self.value)

    def h_escape_exit(self, ch):
        "Esc key was pressed"
        self.parent.textfield_exit()
        
    def handle_mouse_event(self, mouse_event):
        #mouse_id, x, y, z, bstate = mouse_event
        #rel_mouse_x = x - self.relx - self.parent.show_atx
        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.cursor_position = rel_x + self.begin_at
        self.display()

    def space_available(self):
        """The space available left on the screen, returned as rows, columns"""
        if self.use_max_space:
            y, x = self.parent.useable_space(self.rely, self.relx)
        else:
            y, x = self.parent.widget_useable_space(self.rely, self.relx)
        return y,x
    
    def set_size(self):
        "From wgwidget.py: Set the size of the object, reconciling the user's request with the space available"
        
        my, mx = self.space_available()
        #my = my+1 # Probably want to remove this.
        ny, nx = self.calculate_area_needed()
        
        max_height = self.max_height
        max_width  = self.max_width
        # What to do if max_height or max_width is negative
        if max_height not in (None, False) and max_height < 0:
            max_height = my + max_height
        if max_width not in (None, False) and max_width < 0:
            max_width = mx + max_width
            
        if max_height not in (None, False) and max_height <= 0:
            raise NotEnoughSpaceForWidget("Not enough space for requested size")  
        if max_width not in (None, False) and max_width <= 0:
            raise NotEnoughSpaceForWidget("Not enough space for requested size")
        
        if ny > 0:
            if my >= ny: 
                self.height = ny
            else: 
                self.height = RAISEERROR
        elif max_height:
            if max_height <= my: 
                self.height = max_height
            else: 
                self.height = self.request_height
        else: 
            self.height = (self.request_height or my)
        
        #if mx <= 0 or my <= 0:
        #    raise Exception("Not enough space for widget")

        if nx > 0:                 # if a minimum space is specified....
            if mx >= nx:           # if max width is greater than needed space 
                self.width = nx    # width is needed space
            else: 
                self.width = RAISEERROR    # else raise an error
        elif self.max_width:       # otherwise if a max width is speciied
            if max_width <= mx: 
                self.width = max_width
            else: 
                self.width = RAISEERROR
        else: 
            self.width = self.request_width or mx   # if both exist, chooses the first

        if self.height == RAISEERROR or self.width == RAISEERROR:
            # Not enough space for widget
            raise NotEnoughSpaceForWidget("Not enough space: max y and x = %s , %s. Height and Width = %s , %s " % (my, mx, self.height, self.width) ) # unsafe. Need to add error here.
        
    def set_text_widths(self):
        "Modified for fixed texts. Why the cursor if not editable?"
        if self.editable == True:   # DV
            if self.on_last_line:
                self.maximum_string_length = self.width - 1  # Leave room for the cursor
            else:   
                self.maximum_string_length = self.width - 1  # Leave room for the cursor at the end of the string
        elif self.editable == False:
            self.maximum_string_length = self.width - 0     # DV: Don't leave room for the cursor


class MyTitleText(npyscreen.TitleText):
    "My own TitleText adapted for Windows/Unicode. Created only to include MyTextfield"
    _entry_type = MyTextfield   # My own text input field

    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class TitleText->Widget :
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        self.how_exited = EXITED_DOWN   # for editw = n
    
    def set_name(self, name):
        "To change the label/name of the text field in real time."
        self.label_widget.value = name


class TitleDateField(MyTitleText):
    "Formatted date input field."
        
    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class MyTitleText:
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        
        self.format = self.check_format(format)
        if self.format == "FormatError":
            self.value = self.format
        self.hidden = False     # do not touch it

    def check_format(self, format):    
        if format not in config.dateAcceptedFormats:
            return "FormatError"
        else:
            return format

    def check_value_is_ok(self):
        date = self.value
        if self.format[0] == "d":
            day = date[:2]
            month = date[3:5]
        else:
            month = date[:2]
            day = date[3:5]
        year = date[6:]
        try:
            date = datetime.date(int(year), int(month), int(day))
        except ValueError:
            return False
        return True


class TitleDateTimeField(MyTitleText):
    "Formatted date+time input field."
        
    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class MyTitleText:
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        
        self.format = self.check_format(format)
        if self.format == "FormatError":
            self.value = self.format
        self.hidden = False     # do not touch it

    def check_format(self, format):    
        if format not in config.datetimeAcceptedFormats:
            return "FormatError"
        else:
            return format

    def check_value_is_ok(self):
        date = self.value
        if self.format[0] == "d":
            day = date[:2]
            month = date[3:5]
        else:
            month = date[:2]
            day = date[3:5]
        if "yyyy" in self.format:
            year = date[6:10]
        else:
            year = date[6:8]

        try:
            hour = date[9:]
            pos = hour.index(":")
            h = hour[:pos]
            m = hour[pos+1:]
            if len(h) != 2 or len(m) != 2:
                return False
            hour += ":00"
            d = datetime.date(int(year), int(month), int(day))
            t = time.strptime(hour, '%H:%M:%S')        
        except ValueError:
            return False
        return True


class TitleTimeField(MyTitleText):
    "Formatted time input field."
    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class MyTitleText:
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        
        self.format = self.check_format(format)
        if self.format == "FormatError":
            self.value = self.format
        self.hidden = False     # do not touch it

    def check_format(self, format):    
        if format not in config.timeAcceptedFormats:
            return "FormatError"
        else:
            return format

    def check_value_is_ok(self):
        t1 = self.value

        if len(t1) != 8 and len(t1) != 5:
            return False
        
        if len(t1) == 5:    # we let enter only 5 figures ("HH:MM")
            try:
                t2 = time.strptime(t1, '%H:%M')
            except ValueError:
                return False
            return True

        if len(t1) == 8:
            try:
                t2 = time.strptime(t1, '%H:%M:%S')
            except ValueError:
                return False
            return True


class MyGridColTitles(grid.SimpleGrid):
    "Adapted from npyscreen.GridColTitles. Necessary for col_margin=0"
    
    additional_y_offset   = 2
  
    _contained_widgets = MyTextfield     # DV: modified
    _col_widgets = MyTextfield
    
    def __init__(self, screen, col_titles=None, col_margin=0, *args, **keywords):   # DV: modified
        if col_titles:
            self.col_titles = col_titles
        else:
            self.col_titles = []
        self.col_margin = col_margin    # DV: modified
        super(MyGridColTitles, self).__init__(screen, col_margin=self.col_margin, *args, **keywords)  # DV: modified: va a SimpleGrid.__init__()
    
    def update(self, clear=True):
        "From SimpleGrid, adapted to a righthand screen with a wide-screen notes/description column."
        if clear == True:
            self.clear()
        if self.begin_col_display_at < 0:
            self.begin_col_display_at = 0
        if self.begin_row_display_at < 0:
            self.begin_row_display_at = 0
        if (self.editing or self.always_show_cursor) and not self.edit_cell:
            self.edit_cell = [0,0]
        row_indexer = self.begin_row_display_at
        for widget_row in self._my_widgets:
            column_indexer = self.begin_col_display_at
            for cell in widget_row:
                cell.grid_current_value_index = (row_indexer, column_indexer)
                if self.parent.name == "BookSelector" and self.form.right_screen:
                    if column_indexer != 5 and column_indexer != 6:
                        continue    # in the 2nd screen, disallow to keep displaying columns over the only two valid
                self._print_cell(cell, )
                column_indexer += 1
            row_indexer += 1


class MyGrid(MyGridColTitles):
    "My GridColTitles version."
    def __init__(self, screen, col_titles=None, col_widths=[], col_margin=0, *args, **keywords):
        self.form = screen
        self.col_widths = col_widths
        self.col_margin = col_margin
        self.form.right_screen = False

        super().__init__(screen, col_titles, col_margin, *args, **keywords)     # go to MyGridColTitles.__init__  
    
    def make_contained_widgets(self):
        "Adapted from GridColTitles+SimpleGrid to accept specified column width. Parameter col_widths is optional."
        
        if len(self.col_widths) == 0:     # first time in empty initialization, or non-specified col_widths
            if self.column_width_requested:
                # don't need a margin for the final column
                self.columns = (self.width + self.col_margin) // (self.column_width_requested + self.col_margin)
            elif self.columns_requested:
                self.columns = self.columns_requested
            else:
                self.columns = self.default_column_number
        elif len(self.col_widths) > 0:      # with specified column widths
            #self.columns = len(self.col_widths)
            self.columns = 0
            acum = 0
            for i in range(len(self.col_widths)):
                acum += self.col_widths[i]
                self.columns += 1
                if acum == WIDTH:
                    break

        column_width = (self.width + self.col_margin - self.additional_x_offset) // self.columns
        column_width -= self.col_margin
        self._column_width = column_width
        if column_width < 1: raise Exception("Too many columns for space available")                

        # Column titles: -------------------------------------------------------------------
        self._my_col_titles = []
        x_offset = 0
        for title_cell in range(self.columns):
            if len(self.col_widths) == 0:     # first time in empty initialization, or non-specified col_widths
                x_offset = title_cell * (self._column_width+self.col_margin)
                column_width = self._column_width
            else:   # with specified column widths
                column_width = self.col_widths[title_cell]

            self._my_col_titles.append(self._col_widgets(self.parent, rely=self.rely, relx = self.relx + x_offset, \
                width=column_width+self.col_margin, height=1))
            x_offset += (column_width + self.col_margin)
        
        # Data rows: -------------------------------------------------------------------
        if len(self.col_widths) == 0:     # first time in empty initialization, or non-specified col_widths
            if self.column_width_requested:
                # don't need a margin for the final column
                self.columns = (self.width + self.col_margin) // (self.column_width_requested + self.col_margin)
            elif self.columns_requested:
                self.columns = self.columns_requested
            else:
                self.columns = self.default_column_number
            self._my_widgets = []
            for h in range( (self.height - self.additional_y_offset) // self.row_height ):
                h_coord = h * self.row_height
                row = []
                for cell in range(self.columns):
                    x_offset = cell * (self._column_width + self.col_margin)
                    row.append(self._contained_widgets(self.parent, rely=h_coord+self.rely + self.additional_y_offset, \
                        relx = self.relx + x_offset + self.additional_x_offset, width=column_width, height=self.row_height))
                self._my_widgets.append(row)
        else:   # with specified column widths
            self._my_widgets = []
            for h in range( (self.height - self.additional_y_offset) // self.row_height ):
                h_coord = h * self.row_height
                row = []
                x_offset = 0
                for cell in range(self.columns):
                    column_width = self.col_widths[cell]
                    row.append(self._contained_widgets(self.parent, rely=h_coord+self.rely + self.additional_y_offset, \
                        relx = self.relx + x_offset + self.additional_x_offset, width=column_width, height=self.row_height))
                    x_offset += (column_width + self.col_margin)
                self._my_widgets.append(row)

    def h_scroll_left(self, inpt):
        "Adapted to full-line selection and bi-screen."
        if self.begin_col_display_at > 0:
            self.begin_col_display_at -= self.columns
        if self.begin_col_display_at < 0:
            self.begin_col_display_at = 0
        if self.edit_cell[1] > 0:
            self.edit_cell[1] = self.edit_cell[1] - self.columns    # DV
        self.form.right_screen = False    # meaning the screen on the right hand

        # Hacking grid column sizes
        self.make_contained_widgets()   # refresh screen
        self.on_select(inpt)

    def h_scroll_right(self, inpt):
        "Adapted from SimpleGrid to bi-screen."
        # If displayed columns < total columns :
        number_of_displayed_columns = self.begin_col_display_at + self.columns
        total_columns = len(self.values[self.edit_cell[0]])
        if number_of_displayed_columns < total_columns : # DV
            self.begin_col_display_at += self.columns   # increments first displayed column
            self.form.right_screen = True    # meaning the screen on the right hand

            # Hacking grid right-screen column sizes
            if self.parent.name == "BookSelector":
                for row in range(len(self._my_widgets)):
                    self._my_widgets[row][0].maximum_string_length = self.col_widths[-2]
                    self._my_widgets[row][1].maximum_string_length = self.col_widths[-1]
                    self._my_widgets[row][1].relx = self.col_widths[-2]

        self.on_select(inpt)
    
    def set_up_handlers(self):  # Adapted from class SimpleGrid.
        """This function should be called somewhere during object initialisation (which all library-defined widgets do).\
            You might like to override this in your own definition, but in most cases the add_handers or add_complex_handlers \
            methods are what you want."""
        #called in __init__
        self.handlers = {
                    curses.KEY_UP:      self.h_move_line_up,
                    #curses.KEY_LEFT:    self.h_move_cell_left,
                    curses.KEY_LEFT:    self.h_scroll_left,    # Adjusted
                    curses.KEY_DOWN:    self.h_move_line_down,
                    #curses.KEY_RIGHT:   self.h_move_cell_right,
                    curses.KEY_RIGHT:   self.h_scroll_right,    # Adjusted
                    '^Y':               self.h_scroll_left,
                    '^U':               self.h_scroll_right,    # for VS Code IDE
                    curses.KEY_NPAGE:   self.h_move_page_down,
                    curses.KEY_PPAGE:   self.h_move_page_up,
                    curses.KEY_HOME:    self.h_show_beginning,
                    curses.KEY_END:     self.h_show_end,
                    curses.ascii.TAB:   self.h_exit,
                    curses.KEY_BTAB:    self.h_exit_up,
                    ord("f"):           self.h_exit,
                    ord("F"):           self.h_exit,
                    ord("c"):           self.h_exit,
                    ord("C"):           self.h_exit,
                    ord("r"):           self.h_exit,
                    ord("R"):           self.h_exit,
                    ord("u"):           self.h_exit,
                    ord("U"):           self.h_exit,
                    ord("d"):           self.h_exit,
                    ord("D"):           self.h_exit,
                    curses.ascii.ESC:   self.h_exit,
                    curses.KEY_MOUSE:   self.h_exit_mouse,
                }
        self.complex_handlers = []
        
    def h_exit(self, ch):
        "Exit from grid with accepted keys, TAB included. Adapted from class SimpleGrid."
        self.editing = False    # exit from grid
        self.how_exited = True  # self.find_next_editable, # A default value
        try:
            config.currentRow = config.fileRows[self.edit_cell[0]][1]
        except IndexError:  # there are no rows in the table
            pass

        selectorForm = self.form
        match ch:
            case ( 102 | 70 ):          # "F/f=Find"
                selectorForm.find_row()
            case ( 99 | 67 ):           # "C/c=Create"
                selectorForm.create_row()
            case ( 114 | 82 ):          # "R/r=Read"
                selectorForm.read_row()
            case ( 117 | 85 ):          # "U/u=Update"
                selectorForm.update_row()
            case ( 100 | 68 ):          # "D/d=Delete"
                selectorForm.delete_row()

    def update(self, clear=True):
        "Adapted for bi-screen."
        super(MyGrid, self).update(clear = True)    # goes to MyGridColTitles.update() and to SimpleGrid.update()
        
        _title_counter = 0
        for title_cell in self._my_col_titles:
            if self.parent.name == "BookSelector":
                if self.form.right_screen:
                    if title_cell.value.strip() in ["Date","ISBN/SKU"]:
                        pass    # to the try
                    elif title_cell.value.strip() == "":  # coming from the form, on the right-screen
                        # Hacking grid right-screen column sizes
                        for row in range(len(self._my_widgets)):
                            self._my_widgets[row][0].maximum_string_length = self.col_widths[-2]
                            self._my_widgets[row][1].maximum_string_length = self.col_widths[-1]
                            self._my_widgets[row][1].relx = self.col_widths[-2]
                            pass
                    elif title_cell.value.strip() not in ["Numeral","Title"]:
                        continue    # rest of left-screen fields
            try:
                title_text = self.col_titles[self.begin_col_display_at+_title_counter]
            except IndexError:
                title_text = None
            title_cell.value = title_text
            title_cell.update()
            _title_counter += 1
            
        self.parent.curses_pad.hline(self.rely+1, self.relx, curses.ACS_HLINE, self.width)
        self.parent.curses_pad.hline(self.height+1, self.relx, curses.ACS_HLINE, self.width)    # DV added bottom line

    def empty_the_grid(self):
        self.values = []
        form = self.form
        form.formTitle.value = form.form_title + " - [Find] subset: No records found"
        form.formTitle.value = form.formTitle.value + " "*(WIDTH - len(form.formTitle.value) - 1 -len(form.today)) + form.today
    
    def set_highlight_row(self, row_reference):
        "Searchs and highlights current grid row."
        config.screenRow = 0
        if row_reference != None:
            filerows = config.fileRows
            for row in filerows:     # (it's already updated)
                if row[1] == row_reference:
                    self.edit_cell = [config.screenRow, 0]  # highlight selected row
                    config.currentRow = row_reference
                    # If the searched index is greater than the first index displayed on screen
                    if config.screenRow > self.begin_row_display_at:
                        self.ensure_cursor_on_display_down_right(None)
                    else:   # # If the searched index is smaller than the first displayed index
                        self.ensure_cursor_on_display_up(None)
                    break
                config.screenRow += 1
        elif row_reference == None:
            self.edit_cell = [0, 0] # the first one
            config.currentRow = ""
            try:
                filerows = config.fileRows
                if filerows[self.edit_cell[0]]:  # if there is a row...
                    config.currentRow = filerows[self.edit_cell[0]][1]    # ...get the row reference
                # If the searched index is greater than the first index displayed on screen
                if config.screenRow > self.begin_row_display_at:
                    self.ensure_cursor_on_display_down_right(None)
                else:   # If the searched index is smaller than the first index displayed on screen
                    self.ensure_cursor_on_display_up(None)
            except IndexError:  # there are no rows in the table
                pass

    def h_show_beginning(self, inpt):
        "DV: Modified to remain in the left or right screen."
        #self.begin_col_display_at = 0
        self.begin_row_display_at = 0
        self.edit_cell = [0, 0]
        self.on_select(inpt)
    
    def ensure_cursor_on_display_down_left(self, inpt=None):
        "Newly created."
        while self.begin_row_display_at  + len(self._my_widgets) - 1 < self.edit_cell[0]:
            self.h_scroll_display_down(inpt)
            
    def h_show_end(self, inpt):
        "Modified to remain in left screen."
        self.edit_cell = [len(self.values) - 1 , len(self.values[-1]) - 1]
        self.ensure_cursor_on_display_down_left()
        self.on_select(inpt)


class OptionField(textbox.Textfield):
    "A single-character input field for the options line."
    def __init__(self, screen, name, value, relx, rely, width, height, max_width, max_height, editable, use_max_space, **keywords):
        
        self.how_exited = True  # self.find_next_editable, # A default value
        self.selectorForm = screen

        super().__init__(screen, value='',
                        relx=relx,
                        rely=rely,
                        width=width,
                        height=height,
                        max_width=max_width,
                        max_height=max_height,
                        editable=editable,
                        use_max_space=use_max_space,
                        highlight_color='CURSOR', 
                        highlight_whole_widget=False, 
                        invert_highlight_color=False, **keywords)   # goes to TextfieldBase
    
    def when_check_cursor_moved(self):
        "When key is pressed on the field."
        self.check_one_letter_option()
        self.update(clear=True)

    def when_value_edited(self):
        "When field input is completed."
        pass

    def check_one_letter_option(self):
        self.optionsLit = "FfCcRrUuDd"
        if self.value not in self.optionsLit:
            curses.beep()       
            self.value = ""
            self.update()

    def when_check_value_changed(self):
        "Manages one-letter option, no need for length check."
        match self.value:
            case ( "F" | "f" ):          # "F/f=Find"
                self.update(clear=True)
                self.selectorForm.find_row()
            case ( "C" | "c" ):           # "C/c=Create"
                self.update(clear=True)
                self.selectorForm.create_row()
            case ( "R" | "r" ):          # "R/r=Read"
                self.update(clear=True)
                self.selectorForm.read_row()
            case ( "U" | "u" ):          # "U/u=Update"
                self.update(clear=True)
                self.selectorForm.update_row()
            case ( "D" | "d" ):          # "D/d=Delete"
                self.update(clear=True)
                self.selectorForm.delete_row()


class DetailField(MyTextfield):
    "Detail input field for Numeral and Find-literal fields."
    def __init__(self, screen, screenForm, name, value, relx, rely, width, height, max_width, max_height, editable, use_max_space, **keywords):
        
        self.form = screen  # for external calls
        self.name = name
        self.is_find_literal = False    # to convert to a literal searching field.
        self.how_exited = True      # self.find_next_editable, # A default value
        self.option = None  # to store FCRUD option
        self.formScreen = screenForm    # Record screen form

        super().__init__(screen, value='',         # goes to TextfieldBase->Widget
                        relx=relx,
                        rely=rely,
                        width=width,
                        height=height,
                        max_width=max_width,
                        max_height=max_height,
                        editable=editable,
                        use_max_space=use_max_space,
                        highlight_color='CURSOR', 
                        highlight_whole_widget=False, 
                        invert_highlight_color=False, **keywords)

    def when_check_cursor_moved(self):
        "When key is pressed on the field."
        if not self.is_find_literal:
            self.check_length(self.maximum_string_length)  # 6-digit Numeral
            self.check_only_numbers()
    
    def when_value_edited(self):
        "Input completed on the field."
        if not self.is_find_literal:
            self.check_length(self.maximum_string_length)  # 6-digit Numeral
            self.check_only_numbers()

    def check_only_numbers(self):
        if not self.value == "":
            if not self.value.isdecimal():
                # Error is not shown and keeps editing the field:
                longitud = len(self.value)
                self.value = self.value[:longitud-1]  # cut the last character
                self.update()
                curses.beep()

    def check_length(self, length):
        if len(self.value) > length:
            curses.beep()
            self.value = self.value[:length]
            self.update()
    
    def get_and_use_key_press(self):    
        "Adapted from class Widget. Substitutes entirely the original function."
        
        # Enter raw mode. In raw mode, normal line buffering and processing of interrupt, quit, suspend, 
        #     and flow control keys are turned off; characters are presented to curses input functions one by one.
        curses.raw()
        # Enter cbreak mode: normal line buffering is turned off and characters are available to be read one by one.
        curses.cbreak()
        # meta: if flag is True, allow 8-bit characters to be input. If flag is False, allow only 7-bit chars.
        curses.meta(True)

        self.parent.curses_pad.keypad(1)
        if self.parent.keypress_timeout:
            curses.halfdelay(self.parent.keypress_timeout)
            ch = self._get_ch()
            if ch == -1:
                return self.try_while_waiting()
        else:
            self.parent.curses_pad.timeout(-1)
            ch = self._get_ch()

        ch = self.filter_char(ch)

        # handle escape-prefixed rubbish.
        if ch == curses.ascii.ESC:
            self.parent.curses_pad.nodelay(1)
            ch2 = self.parent.curses_pad.getch()
            if ch2 != -1: 
                ch = curses.ascii.alt(ch2)
            self.parent.curses_pad.timeout(-1) # back to blocking mode

        self.handle_input(ch)
        if self.check_value_change:
            self.when_check_value_changed()
        if self.check_cursor_move:
            self.when_check_cursor_moved()
        
        self.try_adjust_widgets()

        # Enter-key on Numeral/Find-literal field:
        if ch == curses.ascii.CR or ch == curses.ascii.NL:  # Windows or GNU/Linux
            if self.value != "":
                if self.option == "Find":    # Find results go to grid, not to vertical file form
                    if self.form.find_DB_rows(self.value):
                        self.form.grid.set_highlight_row(None)    # select the first one
                    else:
                        # Empty the grid if no row found?
                        self.form.grid.empty_the_grid()
                        return              
                elif self.option != "Find": 
                    self.goto_Form(self.value)
            elif self.value == "":
                if self.option == "Find":    # Find with no literal: return to full-set grid
                    form = self.form
                    #form.formTitle.value = form.form_title
                    grid = form.grid
                    config.fileRows = form.readDBTable()        # it's a list of lists
                    self.screenFileRows = form.getRowListForScreen(config.fileRows)     # it's a list of lists
                    grid.values = self.screenFileRows
                    grid.set_highlight_row(None)  # First row
        elif ch == curses.ascii.ESC:
            self.editing = False
    
    def goto_Form(self, numeral):
        "Search for the required record and store it in a globally-accessible variable."
        try:
            selectorForm = self.form
            if not selectorForm.read_record(int(numeral)):
                notify("\n        Record not found", form_color='STANDOUT', wrap=True, wide=False)
                time.sleep(0.6)     # let it be seen
                return
        except ValueError:
            notify("\n        Bad value for Numeral", form_color='STANDOUT', wrap=True, wide=False)
            time.sleep(0.6)     # let it be seen
            return

        # we come from DetailField: before we get to the next screen, we have to restore...
        # ...the options statusline and return to the OptionField
        self.form.hide_detail()
        self.form.ask_option()

        if "BookForm" in repr(self.formScreen):
            nextForm = "BOOK"
        elif "AuthorForm" in repr(self.formScreen):
            nextForm = "AUTHOR"
        elif "PublisherForm" in repr(self.formScreen):
            nextForm = "PUBLISHER"
        elif "WarehouseForm" in repr(self.formScreen):
            nextForm = "WAREHOUSE"
        elif "UserForm" in repr(self.formScreen):
            nextForm = "USER"

        config.parentApp.setNextForm(nextForm)
        config.parentApp.switchFormNow()

        # set_createMode() is called from create_row()
        if self.option == "Read":
            self.formScreen.set_readOnlyMode()
        elif self.option == "Update":
            self.formScreen.set_updateMode()
        elif self.option == "Delete":
            self.formScreen.set_deleteMode()


class YearField(MyTextfield):
    "A year field. Only inputs numbers, minus, and of course navigation keys."

    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False, invert_highlight_color=True, \
        fixed_length=True, ndecimals=None, **keywords):
       
        super().__init__(screen, value, highlight_color, highlight_whole_widget, invert_highlight_color, **keywords)    # to TextfieldBase -> Widget

    ###########################################################################################
    # Handlers and methods

    def filter_char(self, char):
        "Filters keys for the MoneyField in the terminal."

        match char:
            case ( 8 ):         # BS
                pass    # go on
            case ( curses.ascii.TAB ):     # Tab
                pass
            case ( curses.KEY_BTAB ): # Back-Tab
                pass
            case ( curses.ascii.CR | curses.ascii.NL ):        # CR for Win, NL for GNU/linux
                pass
            case num if 48 <= num < 58:     # numbers 0-9: enabled
                pass    # go on
            case ( 45 | 464 ):              # Minus keys
                char = 45
            case ( 262 ):             # Home key
                pass
            case ( 263 ):             # Backspace in linux
                pass
            case ( 358 | 360 ):       # End key in linux
                pass
            case ( 260 | 452 ):       # Left arrow
                pass
            case ( 261 | 454 ):       # Right arrow
                pass
            case ( 258 | 456 ):       # Down arrow
                pass
            case ( 259 | 450 ):       # Up arrow
                pass
            case ( 459 ):             # Numeric pad enter key
                char = 13
            case ( 330 | 462 ):       # Del/Supr key
                pass
            case _:
                char = False    # everything else is disabled
        return char


class MyTitleYear(npyscreen.TitleText):
    "My own TitleText adapted for Windows/Unicode. Created only to include YearField"
    _entry_type = YearField   # My own text input field

    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class TitleText->Widget :
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        self.how_exited = EXITED_DOWN   # for editw = n


class MoneyField(MyTextfield):
    "Decimal money field with 2 decimals. Only inputs numbers, arrows, home, end, and dot/comma keys."

    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False, invert_highlight_color=True, \
        fixed_length=True, ndecimals=None, **keywords):
       
        super().__init__(screen, value, highlight_color, highlight_whole_widget, invert_highlight_color, **keywords)    # to TextfieldBase -> Widget

        self.ndecimals = ndecimals    # mantissa

    ###########################################################################################
    # Handlers and methods

    def edit(self):
        self.editing = 1
        self.old_value = self.value      # DV: modified
        self.first_keypress = True

        if self.cursor_position is False:
            self.cursor_position = 0    # DV: modified
        self.parent.curses_pad.keypad(1)

        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.display()
        self.cursor_position = False
        return self.how_exited, self.value

    def filter_char(self, char):
        "Filters keys for the MoneyField in the terminal"

        self.printable_char = False
        match char:
            case ( 8 ):         # BS
                pass    # go on
            case ( curses.ascii.TAB ):     # Tab
                self.first_keypress = True
            case ( curses.ascii.CR | curses.ascii.NL ):        # CR for Win, NL for GNU/linux
                pass
            case ( 44 | 46 ):   # comma | point
                if chr(44) in self.value or chr(46) in self.value:
                    char = False
                else:
                    self.printable_char = True
                    pass
            case num if 48 <= num < 58:     # numbers 0-9: enabled
                self.printable_char = True
                pass       # go on
            case ( 262 ):             # Home key
                self.first_keypress = True
            case ( curses.KEY_BTAB ): # Back-Tab
                self.first_keypress = True
            case ( 263 ):             # Backspace in linux
                pass
            case ( 358 | 360 ):       # End key in linux
                pass
            case ( 260 | 452 ):       # Left arrow
                pass
            case ( 261 | 454 ):       # Right arrow
                pass
            case ( 258 | 456 ):       # Down arrow
                self.first_keypress = True
            case ( 259 | 450 ):       # Up arrow
                self.first_keypress = True
            case ( 459 ):             # Numeric pad enter key
                char = 13
            case ( 330 | 462 ):       # Del/Supr key
                pass
            case _:
                char = False    # everything else is disabled
        return char

    def when_check_value_changed(self):
        "Manages initial-keypress(es) option."

        if self.fixed_length:   # fixed_length means the field is not horiz-scrollable
            if len(self.value) > self.maximum_string_length:
                self.value = self.value[:self.maximum_string_length]
                # No literal added here.
                self.update(clear=True)
        else:
            pass    # no fixed length means the field is horiz-scrollable

        if self.value == "":    # for button mouse click
            return

        if self.printable_char:
            if self.first_keypress and self.cursor_position == 1:
                self.value = self.value[0]
                self.first_keypress = False
                self.update(clear=True)


class MyTitleMoney(npyscreen.TitleText):
    "My own TitleText adapted for Windows/Unicode. Created only to include MoneyField"
    _entry_type = MoneyField   # My own text input field

    def __init__(self, screen, begin_entry_at=16, field_width=None, value=None, format=None, use_two_lines=None, hidden=False, \
                                            labelColor='LABEL', allow_override_begin_entry_at=True, **keywords):
        # goes to class TitleText->Widget :
        super().__init__(screen, begin_entry_at, field_width, value, use_two_lines, hidden, labelColor, \
                                                        allow_override_begin_entry_at, **keywords)
        self.how_exited = EXITED_DOWN   # for editw = n


class MyMultiLineEdit(npyscreen.MultiLineEdit):
    "My version of MultiLineEdit with adjusted key bindings."
    def __init__(self, screen, autowrap=True, slow_scroll=True, scroll_exit=True, value=None, **keywords):
        super().__init__(screen, **keywords)    # to MultiLineEdit

        self.how_exited = EXITED_DOWN   # for editw = n

    def filter_char(self, char):
        "Filters some keys for the terminal"
        
        match char:
            case ( 459 ):       # Numeric pad enter key
                char = 13
            case ( 465 ):       # Numeric pad plus key
                char = 43
            case ( 464 ):       # Numeric pad minus key
                char = 45
            case ( 463 ):       # Numeric pad asterisk key
                char = 42
            case ( 458 ):       # Numeric pad slash key
                char = 47
            case ( 331 ):       # Insert key
                char = False
            case ( 262 ):       # Home key
                pass    # go on
            case ( 339 ):       # Page Up key
                char = False
            case ( 338 ):       # Page Down key
                char = False
            case ( 358 ):       # End key
                pass    # go on
            case ( curses.ascii.ESC ):       # Escape key
                char = False
        return char

    def _get_ch(self):
        """
        >>>---> DV: Heavily modified to display non-ascii characters under Python 3.10
                    (See original in wgwidget.py)
        """
        #try:
        #    # Python3.3 and above - returns unicode
        #    ch = self.parent.curses_pad.get_wch()
        #    self._last_get_ch_was_unicode = True
        #except AttributeError:
            
        # For now, disable all attempt to use get_wch()
        # but everything that follows could be in the except clause above.
        
        # DV: For GNU/Linux:
        if config.system == "Linux":     
        
            # Try to read utf-8 if possible.
            _stored_bytes =[]
            self._last_get_ch_was_unicode = True
            global ALLOW_NEW_INPUT
            if ALLOW_NEW_INPUT == True and locale.getpreferredencoding() == 'UTF-8':
                ch = self.parent.curses_pad.getch()
                if ch <= 127:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                elif ch <= 193:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                # if we are here, we need to read 1, 2 or 3 more bytes.
                # all of the subsequent bytes should be in the range 128 - 191, 
                # but we'll risk not checking...
                elif 194 <= ch <= 223: 
                        # 2 bytes
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif 224 <= ch <= 239: 
                        # 3 bytes 
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                elif 240 <= ch <= 244: 
                        # 4 bytes 
                        _stored_bytes.append(ch) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif ch >= 245:
                    # probably a control character
                    self._last_get_ch_was_unicode = False
                    return ch
                
                ch = bytes(_stored_bytes).decode('utf-8', errors='strict')
            else:
                ch = self.parent.curses_pad.getch()
                self._last_get_ch_was_unicode = False

            # This line should not be in the except clause.
            return ch
        
        # >>> DV: for Windows:
        elif config.system == "Windows":
            if ALLOW_NEW_INPUT == True:
                ch = self.parent.curses_pad.getch()
                rtn_ch = ch
                self._last_get_ch_was_unicode = False
                return rtn_ch

    def get_and_use_key_press(self):    
        "Adapted from class Widget. Substitutes entirely the original function."

        # Enter raw mode. In raw mode, normal line buffering and processing of interrupt, quit, suspend, 
        #     and flow control keys are turned off; characters are presented to curses input functions one by one.
        curses.raw()
        # Enter cbreak mode: normal line buffering is turned off and characters are available to be read one by one.
        curses.cbreak()
        # meta: if flag is True, allow 8-bit characters to be input. If flag is False, allow only 7-bit chars.
        curses.meta(True)
        
        self.parent.curses_pad.keypad(1)
        if self.parent.keypress_timeout:
            curses.halfdelay(self.parent.keypress_timeout)
            ch = self._get_ch()
            if ch == -1:
                return self.try_while_waiting()
        else:
            self.parent.curses_pad.timeout(-1)
            ch = self._get_ch()

        ch = self.filter_char(ch)
        if ch == False:     # Useless keys 
            return

        # handle escape-prefixed rubbish.
        if ch == curses.ascii.ESC:
            #self.parent.curses_pad.timeout(1)
            self.parent.curses_pad.nodelay(1)
            ch2 = self.parent.curses_pad.getch()
            if ch2 != -1: 
                ch = curses.ascii.alt(ch2)
            self.parent.curses_pad.timeout(-1) # back to blocking mode
            #curses.flushinp()

        self.handle_input(ch)
        if self.check_value_change:
            self.when_check_value_changed()
        if self.check_cursor_move:
            self.when_check_cursor_moved()
        
        self.try_adjust_widgets()

    def edit(self):
        self.editing = 1
        if self.cursor_position is False:
            self.cursor_position = len(self.value or '')
        self.parent.curses_pad.keypad(1)
        
        self.how_exited = False     # self.do_nothing = pass

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        #self.display() # don't uncomment: DetailField escape issue
        self.cursor_position = False
        return self.how_exited, self.value
   
    ###########################################################################################
    # Handlers and methods

    def set_up_handlers(self):
        super(npyscreen.MultiLineEdit, self).set_up_handlers()    
    
        # For OS X
        del_key = curses.ascii.alt('~')
        
        self.handlers.update({
                   curses.ascii.NL:    self.h_add_nl,
                   curses.ascii.CR:    self.h_add_nl,
                   curses.KEY_LEFT:    self.h_cursor_left,
                   curses.KEY_RIGHT:   self.h_cursor_right,
                   curses.KEY_UP:      self.h_line_up,
                   curses.KEY_DOWN:    self.h_line_down,
                   curses.KEY_DC:      self.h_delete_right,
                   curses.ascii.DEL:   self.h_delete_left,
                   curses.ascii.BS:    self.h_delete_left,
                   curses.KEY_BACKSPACE: self.h_delete_left,
                   "^R":           self.full_reformat,
                   curses.ascii.ESC:  self.h_escape_exit,
                   curses.KEY_HOME:   self.h_cursor_home,
                   curses.KEY_END:    self.h_cursor_end,
                   # mac os x curses reports DEL as escape oddly
                   # no solution yet                   
                   #"^K":          self.h_erase_right,
                   #"^U":          self.h_erase_left,
            })

        self.complex_handlers.extend((
                    (self.t_input_isprint, self.h_addch),
                    # (self.t_is_ck, self.h_erase_right),
                    # (self.t_is_cu, self.h_erase_left),
                        ))

    def t_input_isprint(self, inp):
        # DV: for Linux:
        if config.system == "Linux":
            if self._last_get_ch_was_unicode and inp not in '\n\t\r':
                return True
            if curses.ascii.isprint(inp) and \
            (chr(inp) not in '\n\t\r'): 
                return True
            else: 
                return False
        # DV: for Pyhton 3 under Windows:
        elif config.system == "Windows":
            if chr(inp).isprintable():
                return True
            else:
                return False   
                
    def h_cursor_home(self, input):
        self.cursor_position = 0
        
    def h_cursor_end(self, input):
        self.cursor_position = len(self.value)

    def h_escape_exit(self, ch):
        "Esc key was pressed"
        self.parent.textfield_exit()


class MyAutocomplete(textbox.Textfield):
    "From wgautocomplete.Autocomplete, adjusted for different keys."

    def display(self):
        """Do an update of the object AND refresh the screen"""
        if self.hidden:
            self.clear()
            self.parent.refresh()
        else:
            self.update()
            self.parent.refresh()

    def edit(self):
        self.editing = 1
        self.old_value = self.value      # DV: modified
        try:
            self.chooserType
        except AttributeError:  # doesn't exists, the chooser list is empty
            self.chooserType = "complex"            

        if self.cursor_position is False:
            self.cursor_position = 0    # DV: modified
        self.parent.curses_pad.keypad(1)

        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.display()
        self.cursor_position = False
        return self.how_exited, self.value

    def filter_char(self, char):
        "Filters some keys for the terminal"
        
        editable_field = False

        try:
            editable_field = self.parent.is_editable_field(widget=self)  # for book.py and bookListing.py
        except AttributeError:
            pass

        # A field for alphanumeric/decimal values, point, comma and space:
        match char:
            case ( 459 ):       # Numeric pad enter key
                char = curses.ascii.CR
            case ( 465 ):       # Numeric pad plus key
                char = 43
            case ( 464 ):       # Numeric pad minus key
                char = False
            case ( 463 ):       # Numeric pad asterisk key
                char = False
            case ( 458 ):       # Numeric pad slash key
                char = False
            case ( 330 | 462 ):     # Del/Supr key
                if editable_field:  pass    # Del/Supr is enabled
                else:   char = False        # Del/Supr is disabled
            case ( 331 ):       # Insert key
                char = False
            case ( 262 | 449 ):       # Home key
                if editable_field:  pass    # Home is enabled
                else:   char = False        # Home is disabled
            case ( 339 ):       # Page Up key
                char = False
            case ( 338 ):       # Page Down key
                char = False
            case ( 358 | 455 ):       # End key
                if editable_field:  pass    # End key is enabled
                else:   char = False        # End key is disabled
            case ( 360 ):       # End key for linux: doesn't work!
                if editable_field:
                    char = 358
                    pass    # Enabled
                else:   char = False        # Disabled
            case ( 260 | 452 ):     # Left Arrow
                if editable_field:  pass    # left arrow is enabled
                else:   char = False        # left arrow is disabled
            case ( 261 | 454 ):     # Right Arrow
                if editable_field:  pass    # right arrow is enabled
                else:   char = False        # right arrow is disabled
            case ( curses.ascii.TAB ):      # TAB
                pass
            case ( 258 | 456 ):         # Down Arrow
                pass
            case ( 259 | 450 ):         # Up Arrow
                pass
            case ( curses.ascii.BS | 263 ):   # Backspace 
                if self.cursor_position > 0:
                    self.value = self.value[:self.cursor_position - 1] + self.value[self.cursor_position:]
                    self.cursor_position -= 1
                char = False    # preemptively (Del key works)
            case ( curses.ascii.ESC ):  # Escape key
                # numeral/find field :
                if "DetailField" in repr(self):     # Detail field
                    pass    # go on
                elif "MyTextfield" in repr(self):   # "regular" text field
                    pass    # go on
                else:
                    char = False
        return char

    def convert_unicode_to_char(self, ch):
        "DV: for autocomplete fields and its searching of literals. Ready for Spanish+Catalan"
        rtn_ch = None
        match ch:
            case ( 192 ):
                rtn_ch = "À"
            case ( 193 ):
                rtn_ch = "Á"
            case ( 196 ):
                rtn_ch = "Ä"
            case ( 199 ):
                rtn_ch = "Ç"
            case ( 200 ):
                rtn_ch = "È"
            case ( 201 ):
                rtn_ch = "É"
            case ( 203 ):
                rtn_ch = "Ë"
            case ( 205 ):
                rtn_ch = "Í"
            case ( 207 ):
                rtn_ch = "Ï"
            case ( 209 ):
                rtn_ch = "Ñ"
            case ( 210 ):
                rtn_ch = "Ò"
            case ( 211 ):
                rtn_ch = "Ó"
            case ( 214 ):
                rtn_ch = "Ö"
            case ( 217 ):
                rtn_ch = "Ù"
            case ( 218 ):
                rtn_ch = "Ú"
            case ( 220 ):
                rtn_ch = "Ü"
            case ( 224 ):
                rtn_ch = "à"
            case ( 225 ):
                rtn_ch = "á"
            case ( 228 ):
                rtn_ch = "ä"
            case ( 231 ):
                rtn_ch = "ç"
            case ( 232 ):
                rtn_ch = "è"
            case ( 233 ):
                rtn_ch = "é"
            case ( 235 ):
                rtn_ch = "ë"
            case ( 236 ):
                rtn_ch = "ì"
            case ( 237 ):
                rtn_ch = "í"
            case ( 239 ):
                rtn_ch = "ï"
            case ( 241 ):
                rtn_ch = "ñ"
            case ( 242 ):
                rtn_ch = "ò"
            case ( 243 ):
                rtn_ch = "ó"
            case ( 246 ):
                rtn_ch = "ö"
            case ( 249 ):
                rtn_ch = "ù"
            case ( 250 ):
                rtn_ch = "ú"
            case ( 252 ):
                rtn_ch = "ü"
        if rtn_ch:
            self._last_get_ch_was_unicode = True
            return rtn_ch
        else:
            return ch

    def _get_ch(self):
        """
        >>>---> DV: Heavily modified to display non-ascii characters under Python 3.10
                    (See original in wgwidget.py)
        """
        #try:
        #    # Python3.3 and above - returns unicode
        #    ch = self.parent.curses_pad.get_wch()
        #    self._last_get_ch_was_unicode = True
        #except AttributeError:
            
        # For now, disable all attempt to use get_wch()
        # but everything that follows could be in the except clause above.
        
        # DV: For GNU/Linux:
        if config.system == "Linux":     
        
            # Try to read utf-8 if possible.
            _stored_bytes =[]
            self._last_get_ch_was_unicode = True
            global ALLOW_NEW_INPUT
            if ALLOW_NEW_INPUT == True and locale.getpreferredencoding() == 'UTF-8':
                ch = self.parent.curses_pad.getch()
                if ch <= 127:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                elif ch <= 193:
                    rtn_ch = ch
                    self._last_get_ch_was_unicode = False
                    return rtn_ch
                # if we are here, we need to read 1, 2 or 3 more bytes.
                # all of the subsequent bytes should be in the range 128 - 191, 
                # but we'll risk not checking...
                elif 194 <= ch <= 223: 
                        # 2 bytes
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif 224 <= ch <= 239: 
                        # 3 bytes 
                        _stored_bytes.append(ch)
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                elif 240 <= ch <= 244: 
                        # 4 bytes 
                        _stored_bytes.append(ch) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch()) 
                        _stored_bytes.append(self.parent.curses_pad.getch())
                elif ch >= 245:
                    # probably a control character
                    self._last_get_ch_was_unicode = False
                    return ch
                
                ch = bytes(_stored_bytes).decode('utf-8', errors='strict')
            else:
                ch = self.parent.curses_pad.getch()
                self._last_get_ch_was_unicode = False

            # This line should not be in the except clause.
            return ch
        
        # >>> DV: for Windows:
        elif config.system == "Windows":
            if ALLOW_NEW_INPUT == True:
                
                ch = self.parent.curses_pad.getch()
                rtn_ch = ch
                self._last_get_ch_was_unicode = False
                rtn_ch = self.convert_unicode_to_char(ch)      # for autocomplete fields and its search
                return rtn_ch

    def get_and_use_key_press(self):
        "Adapted from class Widget. Substitutes entirely the original function."

        # Enter raw mode. In raw mode, normal line buffering and processing of interrupt, quit, suspend, 
        #     and flow control keys are turned off; characters are presented to curses input functions one by one.
        curses.raw()
        # Enter cbreak mode: normal line buffering is turned off and characters are available to be read one by one.
        curses.cbreak()
        # meta: if flag is True, allow 8-bit characters to be input. If flag is False, allow only 7-bit chars.
        curses.meta(True)
        
        self.parent.curses_pad.keypad(1)
        if self.parent.keypress_timeout:
            curses.halfdelay(self.parent.keypress_timeout)
            ch = self._get_ch()
            if ch == -1:
                return self.try_while_waiting()
        else:
            self.parent.curses_pad.timeout(-1)
            ch = self._get_ch()
        ch = self.filter_char(ch)
        if ch == False:     # Useless keys 
            return

        # handle escape-prefixed rubbish.
        if ch == curses.ascii.ESC:
            #self.parent.curses_pad.timeout(1)
            self.parent.curses_pad.nodelay(1)
            ch2 = self.parent.curses_pad.getch()
            if ch2 != -1: 
                ch = curses.ascii.alt(ch2)
            self.parent.curses_pad.timeout(-1) # back to blocking mode
            #curses.flushinp()

        self.handle_input(ch)

        if self.check_value_change:
            self.when_check_value_changed()
        if self.check_cursor_move:
            self.when_check_cursor_moved()
        
        self.try_adjust_widgets()

    def set_up_handlers(self):
        super(MyAutocomplete, self).set_up_handlers()

        self.handlers.update({  465:                self.popup_chooser,     # numpad '+' key
                                43:                 self.popup_chooser,     # keyboard '+' key
                               "^U":                self.popup_chooser,     # '+' for VS Code
                                459:                self.h_exit_down,       # numpad intro key
                                curses.ascii.ESC:   self.h_escape_exit,     # go on       # Escape key
                                curses.KEY_UP:      self.h_exit_up,
                                curses.KEY_BTAB:    self.h_exit_up,
                                262:                self.h_home_key,        # Home key
                                449:                self.h_home_key,        # Home key
                                358:                self.h_end_key,         # End key  
                                455:                self.h_end_key,         # End key  
                            })

    def h_home_key(self, ch):
        "Home key was pressed"
        self.cursor_position = 0
    
    def h_end_key(self, ch):
        "End key was pressed"
        self.cursor_position = len(self.value)

    def h_escape_exit(self, ch):
        "Esc key was pressed"
        self.parent.textfield_exit()

    def h_exit_up(self, _input):
        if not self._test_safe_to_exit():
            return False
        """Called when the user leaves the widget to the previous widget"""
        self.editing = False
        self.how_exited = EXITED_UP

        try:
            self.parent.not_first_keypress(widget=self)  # for book.py
        except AttributeError:
            pass

    def h_exit_down(self, _input):
        """Called when user leaves the widget to the next widget"""
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_DOWN

    def h_cursor_left(self, input):
        if self.cursor_position > 0:
            self.cursor_position -= 1

    def h_cursor_right(self, input):
        self.cursor_position += 1

    def get_choice(self):
        "popup_chooser() asks for a list of values"
        # Pop-up window is displayed
        if self.popupType == "wide":
            tmp_window = MyPopupWide(self.parent, name=self.name, framed=True, show_atx=0, show_aty=0, columns=WIDTH, lines=15, shortcut_len=4)
        elif self.popupType == "narrow":
            try:
                tmp_window = self.parent.create_popup_window(widget=self)    # Hook for book.py and bookListing.py
            except AttributeError:
                pass

        selector = tmp_window.add_widget(MyMultiLine,
                values=self.values,
                value=self.value,
                return_exit=True, select_exit=True)
        tmp_window.display()

        # Search text field value in the popup list values

        field_val = self.value
        
        try:
            field_val = self.parent.more_than_one_item(widget=self, field_val=field_val)    # Hook for book.py
        except AttributeError:
            pass

        if field_val not in ["", None]:         # so there's a single item in the field
            if self.chooserType == "simple":    
                selector.value = self.values.index(self.value)

            elif self.chooserType == "complex":
                found = False
                for v in self.values:
                    # Here, v can be either:
                    #   2052       2052-Literal
                    #    01         01-Literal
                    #   Literal
                    try:
                        pos = v.index("-")  # can be variable length
                        # there's a hyphen
                        if v[:pos] == self.value[:pos]:
                            selector.value = self.values.index(v)
                            found = True    # it can be a multi-value field, then it simply finds the first
                            break
                    except ValueError:  # no hyphen
                        if v == self.value:
                            selector.value = self.values.index(v)
                            found = True
                            break
                if not found:
                    notify_OK("\n  Chooser: value '" + self.value + "' not found","Error")
                    return None      # not found
            self.cursor_position = 0
        else:
            selector.value = 0

        selector.cursor_line = selector.value
        selector.edit()
        if selector.how_exited == EXITED_ESCAPE:    # did not choose any one
            return None
        return selector.value
    
    def when_check_cursor_moved(self):
        "When key is pressed on the field."
        #print(inspect.stack()[0][3])
        
    def when_value_edited(self):
        "Input is completed on the field."
        pass

    def when_check_value_changed(self):
        "Manages initial-keypress(es) option."

        if self.value == "":    # for button mouse click
            return
        elif self.value == self.old_value:   # for escape on popup list: it's the same value than the original
            return
        elif self.value == self.current_value:   # it's the same value than the last selected one
            return

        if self.chooserType == "simple":
            if len(self.value) > 0:
                self.value = self.value[0]
                self.value = self.find_value_literal(self.value)
                if self.value == False:
                    self.value = self.old_value  # not found, so restore the initial value
                self.cursor_position=0
                self.update(clear=True)
                #self.parent.push_a_tab()    Beware the back-tab!
        elif self.chooserType == "complex":
            try:
                self.value = self.parent.scan_value_in_list(widget=self)    # Hook for book.py and bookListing.py
                self.current_value = self.value
            except AttributeError:
                if len(self.value) > self.maximum_string_length:
                    self.value = self.value[:self.maximum_string_length]
                    # No literal added here.
            self.update(clear=True)

    def find_value_literal(self, value):
        "Returns a literal from an initial code or from the first characters."
        try:
            pos = self.values[0].index("-")    # there's a hyphen (and a numeric value) So, first value can never sport a hyphen!
            for val in self.values:
                pos = val.index("-")
                if val[:pos] == value:
                    return val
            return False   # not found
        except ValueError:      # no hyphen, no numeric value
            for val in self.values:
                if val[:self.cursor_position].lower() == value[:self.cursor_position].lower():
                    return val
        except IndexError:      # values is empty
            return False

        return value


class Chooser(MyAutocomplete):
    "Autocomplete fixed-options field with simple or complex set up. Adapted from npyscreen.Filename."
    # Exclusive parameters:  values = [] or [(,),(,)]
    # Shortcut-codes before '-' can be of variable length. Don't use a "-" in chooser literal values.
    # There can't be a value = 0

    def __init__(self, screen, value='', values='', highlight_color='CURSOR', popupType=None, \
        highlight_whole_widget=False, invert_highlight_color=True, **keywords):
        
        super().__init__(screen, value, highlight_color, highlight_whole_widget, invert_highlight_color, **keywords)

        self.popupType = popupType

        self.load_values(values)    # Load the values into the chooser

        self.current_value = None

    def popup_chooser(self, input):
        "Displays a popup window to select a value."
        # expand ~

        self.old_value = self.value      # DV: modified
        chosen_value = self.get_choice()
        self.current_value = self.value  # backup value after selecting

        if chosen_value == None :   # not found or Esc-key pressed
            self.value = self.old_value  # restore initial value
            self.cursor_position = 0
            return

        try:
            self.value = self.parent.append_value_to_list(widget=self, chosen_value=chosen_value)
        except AttributeError:
            self.value = self.values[chosen_value]

    def load_values(self, values):
        "Load the values into the chooser."
        final_values = []
        try:
            if isinstance(values[0], str):    # it's a list of string values: will add a number before
                self.chooserType = "simple"
                if len(values) > 9:
                    notify_OK("\n Chooser 'simple' field doesn't accept more than 9 values","Error")
                    sys.exit()
                index = 1
                for v in values:
                    final_values.append(str(index) + "-" + v)
                    index += 1
            elif isinstance(values[0], tuple):  # it's a list of (ref,descr) or (descr) tuples: a table: no number will be added
                self.chooserType = "complex"
                for v in values:
                    if len(values[0]) == 1:     # for instance, authors, warehouses
                        ref = str(v[0])
                    else:
                        ref = v[1]              # for instance, publishers
                    final_values.append(ref)
            elif values == []:
                self.chooserType = "complex"

            self.values = final_values

        except IndexError:  # there are no values
            self.values = []
            return


class TitleChooser(MyTitleText):
    _entry_type = Chooser


class MyPopup(fmForm.Form):
    "A fmPopup.Popup form that captures a shortcut to the options."
    DEFAULT_LINES      = 12
    DEFAULT_COLUMNS    = 60
    SHOW_ATX           = 10
    SHOW_ATY           = 2

    def __init__(self, screen, name=None, parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None,\
        cycle_widgets=False, shortcut_len=None, *args, **keywords):
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets, *args, **keywords)

        self.shortcut_len = shortcut_len    # length of shortcut digits
        self.digit_num = 0  # digit counter
        
        self.parentField = None
        try:
            self.parentField = screen.get_parentField(widget=self)     # for book.py and bookListing.py
        except AttributeError:
            pass

    def create(self):
        "The standard constructor will call the method .create(), which you should override to create the Form widgets."
        self.framed = True
        #self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exitPopup   # Escape exit
        self.set_key_handlers()   # shortcuts
        self.shortcut = ""

    def set_key_handlers(self):
        "DV: adding key handlers for all types of autocomplete."
        # Numbers:
        for inc in range(10):
            self.add_handlers({ord('0') + inc: self.keyHandler})
        # Upper letters:
        for inc in range(26):
            self.add_handlers({ord('A') + inc: self.keyHandler})
        # Lower letters:
        for inc in range(26):
            self.add_handlers({ord('a') + inc: self.keyHandler})
        # Other letters (Spanish+Catalan):
        self.add_handlers({192: self.keyHandler})   # "À"
        self.add_handlers({193: self.keyHandler})   # "Á"
        self.add_handlers({199: self.keyHandler})   # "Ç"
        self.add_handlers({200: self.keyHandler})   # "È"
        self.add_handlers({201: self.keyHandler})   # "É"
        self.add_handlers({205: self.keyHandler})   # "Í"
        self.add_handlers({209: self.keyHandler})   # "Ñ"
        self.add_handlers({210: self.keyHandler})   # "Ò"
        self.add_handlers({211: self.keyHandler})   # "Ó"
        self.add_handlers({218: self.keyHandler})   # "Ú"
        self.add_handlers({224: self.keyHandler})   # "à"
        self.add_handlers({225: self.keyHandler})   # "á"
        self.add_handlers({231: self.keyHandler})   # "ç"
        self.add_handlers({232: self.keyHandler})   # "è"
        self.add_handlers({233: self.keyHandler})   # "é"
        self.add_handlers({237: self.keyHandler})   # "í"
        self.add_handlers({241: self.keyHandler})   # "ñ"
        self.add_handlers({242: self.keyHandler})   # "ò"
        self.add_handlers({243: self.keyHandler})   # "ó"
        self.add_handlers({250: self.keyHandler})   # "ú"
        self.add_handlers({129: self.keyHandler})   # "ü"
        self.add_handlers({154: self.keyHandler})   # "Ü"
        # Other chars:
        #self.add_handlers({" ": self.keyHandler})   # space, for un-numbered lists
        self.add_handlers({".": self.keyHandler})   # dot, for decimal numbered lists
        self.add_handlers({"-": self.keyHandler})   # this triggers end of a variable shortcut
        self.add_handlers({464: self.keyHandler})   # this triggers end of a variable shortcut - Numeric pad minus key
        self.add_handlers({curses.ascii.ESC: self.keyHandler})   # = Escape key

    def keyHandler(self, keyAscii):
        if chr(keyAscii) == "-" or keyAscii == 464:    # this triggers end of variable shortcut 
            self.select_option()
            self.digit_num = 0
            self.shortcut = ""
        else:   # normal
            if self.shortcut_len != None:
                if self.digit_num < self.shortcut_len:
                    self.shortcut += chr(keyAscii)
                    self.digit_num += 1
                if self.digit_num == self.shortcut_len:
                    self.select_option()
                    self.digit_num = 0
                    self.shortcut = ""
            else:   # it's a unnumbered list
                self.shortcut += chr(keyAscii)
                self.select_option()

    def select_option(self):
        "Simply points to the entered shortcut line."
        multiline = self._widgets__[0]
        try:
            pos = multiline.values[0].index("-")   # hyphen, so numbered list
            for v in multiline.values:
                pos = v.index("-")
                if v[:pos] == self.shortcut:
                    index = multiline.values.index(v)
                    multiline.cursor_line = index
                    break
        except ValueError:  # no hyphen, so non-numbered list
            found = False
            for v in multiline.values:
                if v[:len(self.shortcut)].lower() == self.shortcut.lower():
                    index = multiline.values.index(v)
                    multiline.cursor_line = index
                    found = True
                    break
            # not found: back to text field value
            if not found:
                try:
                    index = multiline.values.index(self.parentField.value)
                    multiline.cursor_line = index
                    self.shortcut = ""
                except ValueError:
                    index = 0


class MyPopupWide(MyPopup):
    DEFAULT_LINES      = 14
    DEFAULT_COLUMNS    = None
    SHOW_ATX           = 0
    SHOW_ATY           = 0


class MyMultiLine(multiline.MultiLine):
    "My version of npyscreen.MultiLine, to add Intro key handling to MyAutocomplete."
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False,\
        select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False,\
        allow_filtering=False, **keywords):

        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit, exit_left, exit_right,\
            widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def set_up_handlers(self):
        "Completely overrides multiline.MultiLine and wgwidget.InputHandler to get rid of handler shortcuts."

        """This function should be called somewhere during object initialisation (which all library-defined widgets do). 
        You might like to override this in your own definition, but in most cases the add_handers or add_complex_handlers methods are what you want."""

        #called in __init__
        self.handlers = {
                   curses.ascii.NL:     self.h_exit_down,
                   curses.ascii.CR:     self.h_exit_down,
                   curses.ascii.TAB:    self.h_exit_down,
                   curses.KEY_BTAB:     self.h_exit_up,
                   curses.KEY_DOWN:     self.h_exit_down,
                   curses.KEY_UP:       self.h_exit_up,
                   curses.KEY_LEFT:     self.h_exit_left,
                   curses.KEY_RIGHT:    self.h_exit_right,
                   #"^P":                self.h_exit_up,
                   #"^N":                self.h_exit_down,
                   curses.ascii.ESC:    self.h_exit_escape,
                   curses.KEY_MOUSE:    self.h_exit_mouse,
                   }

        self.handlers.update ( {
                    curses.KEY_UP:      self.h_cursor_line_up,
                    #ord('k'):          self.h_cursor_line_up,
                    curses.KEY_LEFT:    self.h_cursor_line_up,
                    curses.KEY_DOWN:    self.h_cursor_line_down,
                    #ord('j'):          self.h_cursor_line_down,
                    curses.KEY_RIGHT:   self.h_cursor_line_down,
                    curses.KEY_NPAGE:   self.h_cursor_page_down,
                    curses.KEY_PPAGE:   self.h_cursor_page_up,
                    curses.ascii.TAB:   self.h_exit_down,
                    curses.ascii.NL:    self.h_select_exit,
                    curses.KEY_HOME:    self.h_cursor_beginning,
                    curses.KEY_END:     self.h_cursor_end,
                    #ord('g'):          self.h_cursor_beginning,
                    #ord('G'):          self.h_cursor_end,
                    #ord('x'):          self.h_select,
                    # "^L":             self.h_set_filtered_to_selected,
                    curses.ascii.SP:    self.h_select,
                    curses.ascii.ESC:   self.h_exit_escape,
                    curses.ascii.CR:    self.h_select_exit,
                    459:                self.h_select_exit,     # DV: numpad Intro key
                } )
                
        if self.allow_filtering:
            self.handlers.update ( {
                ord('l'):       self.h_set_filter,
                ord('L'):       self.h_clear_filter,
                ord('n'):       self.move_next_filtered,
                ord('N'):       self.move_previous_filtered,
                ord('p'):       self.move_previous_filtered,
                # "^L":         self.h_set_filtered_to_selected,
            } )
            
                
        if self.exit_left:
            self.handlers.update({
                    curses.KEY_LEFT:    self.h_exit_left
            })
        
        if self.exit_right:
            self.handlers.update({
                    curses.KEY_RIGHT:   self.h_exit_right
            })

        self.complex_handlers = [
                    #(self.t_input_isprint, self.h_find_char)
                    ]


class MyMultiLineAction(MyMultiLine):
    "My version of npyscreen.MultiLineAction, to add Intro key handling to VerticalMenu."
    RAISE_ERROR_IF_EMPTY_ACTION = False
    def __init__(self, *args, **keywords):
        self.allow_multi_action = False  
        super(MyMultiLineAction, self).__init__(*args, **keywords)  
    
    def actionHighlighted(self, act_on_this, key_press):
        "Override this Method"
        pass
    
    def h_act_on_highlighted(self, ch):
        try:
            return self.actionHighlighted(self.values[self.cursor_line], ch)
        except IndexError:
            if self.RAISE_ERROR_IF_EMPTY_ACTION:
                raise
            else:
                pass
            
    def set_up_handlers(self):
        super(MyMultiLineAction, self).set_up_handlers()
        self.handlers.update ( {
                    curses.ascii.NL:    self.h_act_on_highlighted,
                    curses.ascii.CR:    self.h_act_on_highlighted,
                    ord('x'):           self.h_act_on_highlighted,
                    459:                self.h_act_on_highlighted,     # DV: numpad Intro key
                    } )                     


class MyMiniButtonPress(npyscreen.MiniButtonPress):
    "My version of MiniButtonPress with Escape and Intro keys."
    # NB.  The when_pressed_function functionality is potentially dangerous. It can set up
    # a circular reference that the garbage collector will never free. 
    # If this is a risk for your program, it is best to subclass this object and
    # override when_pressed_function instead.  Otherwise your program will leak memory.
    def __init__(self, screen, when_pressed_function=None, *args, **keywords):
        super(npyscreen.MiniButtonPress, self).__init__(screen, *args, **keywords)  # goes to class MiniButton
        self.when_pressed_function = when_pressed_function

        # to get to the different fields with .editw, when error occurs:
        self.how_exited = EXITED_DOWN   # self.find_next_editable
    
    def set_up_handlers(self):
        super(npyscreen.MiniButtonPress, self).set_up_handlers()    # goes to class _ToggleControl
        
        self.handlers.update({
                curses.ascii.NL:    self.h_toggle,
                curses.ascii.CR:    self.h_toggle,
                            459:    self.h_toggle,  # DV: numpad intro key
                curses.ascii.ESC:   self.h_escape,
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
    
    def h_escape(self, ch):     # Escape key on the buttons
        pass

    def whenPressed(self):
        pass


class MySelectOne(multiline.MultiLine):
    "My version of wgselectone.SelectOne, to include h_exit_down()"
    _contained_widgets = npyscreen.RoundCheckBox
    
    def update(self, clear=True):
        if self.hidden:
            self.clear()
            return False
        # Make sure that self.value is a list
        if not hasattr(self.value, "append"):
            if self.value is not None:
                self.value = [self.value, ]
            else:
                self.value = []
                
        super(MySelectOne, self).update(clear=clear)

    def h_select(self, ch):
        self.value = [self.cursor_line,]

    def h_exit_down(self, _input):
        """Called when user leaves the widget to the next widget"""
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_DOWN

        if "DeleteMultipleRecordsForm" in self.parent.name:     # for deleteMultipleRecords.py
            if self.value[0] == 0:  # "Empty the database"
                self.parent.rangeFromFld.editable = False
                self.parent.rangeToFld.editable = False
            else:
                self.parent.rangeFromFld.editable = True
                self.parent.rangeToFld.editable = True

    def _print_line(self, line, value_indexer):
        try:
            display_this = self.display_value(self.values[value_indexer])
            line.value = display_this
            line.hide = False
            if hasattr(line, 'selected'):
                if (value_indexer in self.value and (self.value is not None)):
                    line.selected = True
                else:
                    line.selected = False
            # Most classes in the standard library use this
            else:
                if (value_indexer in self.value and (self.value is not None)):
                    line.show_bold = True
                    line.name = display_this
                    line.value = True
                else:
                    line.show_bold = False
                    line.name = display_this
                    line.value = False
                    
            if value_indexer in self._filtered_values_cache:
                line.important = True
            else:
                line.important = False
            
        except IndexError:
            line.name = None
            line.hide = True

        line.highlight= False


class MyTitleSelectOne(multiline.TitleMultiLine):
    "My version of TitleSelectOne."
    _entry_type = MySelectOne
