#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     config.py - Parameters, magic numbers and buffered "global" variables.
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import json
import os
import platform
import subprocess
import sys

SCREENWIDTH = 80        # Intended/enforced screen width
AUTHENTICATE = True    # Ask for user identification at program startup.  
CONFIRMEXIT = True
PROFILING = False
TRACEMALLOC = False

system = platform.system()
system_release = platform.release()     # e.g. '10', '8.1', '5.15.76-1-MANJARO'  
if system == "Windows":
    dataPath = os.getcwd().replace("\\", "/") + "/Data/"    # or a remote resource like "J:/Data/"
    #dataPath = "J:/PyProjects/bookstore/Data/"
    textViewer = "notepad"
elif system == "Linux":
    dataPath = os.getcwd() + "/Data/"
    textViewer = "mousepad" # for Manjaro Xfce

pname = "bookstore"     # program name
dbname = pname + ".db"

# Program version: from git cmd or previously created json file
try:
    program_version = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], \
        capture_output=True, text=True).stdout.strip('\n')[:4]
except FileNotFoundError:
    program_version = ""

filename = dataPath + "program.json"
if program_version != "":   # it's a git repository
    data = {'program': [ {'version' : program_version} ] }
    json_string = json.dumps( data )
    try:
        with open(filename, 'w') as outfile:
            outfile.write(json_string)  # we'll write the json now
    except Exception as e:
        print("\n" + pname + ": " + str(e) ,"Error")
        sys.exit()                
else:   # it's not a git repository, so we read from the json file   
    try:
        with open(filename) as json_file:
            data = json.load(json_file)
            program_version = data['program'][0]['version']
    except FileNotFoundError:
        print("\n " + pname + ": " + filename + " was not found.\n")
        sys.exit()                

parentApp = None        # It's the npyscreen.NPSAppManaged in memory
conn = None             # DB Connection
fileRows = None         # DB record-row list, includes id
fileRow = None          # Current record-row, includes id; same structure as fileRows
currentRow = 0          # Currently selected record-row Numeral field
screenRow = None        # Selected row number/index in the grid

dateFormat = "dd/mm/yy"             # currently accepted format (accepted formats below)
dateTimeFormat = "dd-mm-yy hh:MM"   # currently accepted format
timeFormat = "hh:MM:ss"             # currently accepted format

dateAcceptedFormats = ["dd-mm-yy", "dd/mm/yy", "dd-mm-yyyy", "dd/mm/yyyy", 
                        "mm-dd-yy", "mm/dd/yy", "mm-dd-yyyy", "mm/dd/yyyy"]
datetimeAcceptedFormats = ["dd-mm-yy hh:MM", "dd/mm/yy hh:MM", "dd-mm-yyyy hh:MM", "dd/mm/yyyy hh:MM", 
                        "mm-dd-yy hh:MM", "mm/dd/yy hh:MM", "mm-dd-yyyy hh:MM", "mm/dd/yyyy hh:MM"]
timeAcceptedFormats = ["hh:MM:ss"]

last_table = None       # to read table when entering from main menu
last_operation = None

decimal_symbol = "."    # can be "." or ","
ndecimals = 2   # price mantissa
currency_symbol = "€"
genreList = ["Narrative","Theatre","Poetry","Short story","Essay"]
coverTypeList = ["Softcover with one-sided board",\
            "Silk softcover",\
            "Printed paper case hardcover",\
            "Cloth hardcover",\
            "Hardcover with dust jacket"]

REMEMBER_SUBSET = True  # remember the last found subset
REMEMBER_FILTERS = False  # remember the last listing filter subset

gender_neutral_pronoun = "(S)he"   # (S)he , She/he, He/She , They, Ze, Zir

normal_exit_message = "Program exited normally."

SAVE_REPORTS = False     # if False, automatically deletes the reports after created
#-----------------------------------------------------------------------------------