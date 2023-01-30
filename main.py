#!/usr/bin/python
# encoding: utf-8
##############################################################################
#     main.py - Startup module
#
##############################################################################
# Copyright (c) 2022, 2023 David Villena
# All rights reserved.
# Licensed under the New BSD License
# (http://www.freebsd.org/copyright/freebsd-license.html)
##############################################################################

import config

if config.TRACEMALLOC:
    import tracemalloc
    tracemalloc.start()

import sys

# Python version control
if sys.version_info[0] == 3 and sys.version_info[1] >= 10 :
    pass
else:
    print("\n>>> " + config.pname + ": I'm sorry, program only runs on Python 3.10 or later. <<<\n")
    sys.exit()

import cProfile
import os
import pstats
import mainMenu

import colored_traceback
import npyscreen

colored_traceback.add_hook(always=True) # error Traceback in colors
npyscreen.disableColor()                # application color

PROFILING = config.PROFILING

def set_profiling():
    logfile = "cProfile.log"
    cProfile.run('App.run()', logfile)
    stats = pstats.Stats(logfile)
    #s.strip_dirs().sort_stats(-1).print_stats()
    stats.strip_dirs().print_stats()

if __name__ == "__main__":
    if config.system == "Linux":
        os.environ.setdefault('ESCDELAY', '25')     # To shorten Esc key delay
    App = mainMenu.bookstoreApp()
    if PROFILING:
        set_profiling()
    else:
        App.run()
