# The *bookstore* Project

*"bookstore" is a multi-screen database maintenance program developed on npyscreen, a character terminal user interface.*

This is my attempt at building a fully npyscreen-based application, while learning a decent amount of Python at the same time. It's kind of a demo of the solutions I've implemented using Nicholas P. S. Cole's excellent 'npyscreen' Terminal User Interface library. My focus has been on the final user interaction and usability. Although the program is a fully-fledged book manager on a SQL database, it's more like a demo. Please feel free to share your criticism (and knowledge), I'm using this project as a workbench to learn the right pythonic approach to this implementation.

The application is limited to be a home librarian, not a commercial book store software. The pretense has been to include as many of my own adapted widgets (different types of input fields) as possible. It includes table record grids with different column sizes, quick one-keypress option fields, popup lists of values associated to auto-complete text fields, money input fields, etc. I've followed quite pristinely the old CRUD database paradigm (Create, Read, Update, Delete) and I've added a useful "Find" option based on the LIKE sentence from the SQL language. 

It does not run on Python 2, I'm sorry, it is developed from scratch on Python 3.10, on Windows 10. State-of-the-Art under the hood. The sample SQLite database is version 3.35.5. The program runs on the Command Prompt on Win10, and it is by default limited to a monochrome classical size of 80 x 25 characters, in part, to enforce resource frugality and, in part, by sheer PC-era nostalgia. Note that you can write texts of 80 columns on the screen, but the "editable" widgets can only use 79. The npyscreen library I used is the last available version 4.10.5, and the original widgets have been inherited/overridden onto my own ones to allow for the new functionalities and also for localization purposes (latin and accented characters).

The program also works fine on my Manjaro 22.0 Xfce linux. In fact, python runs much faster on Linux than on Windows when generating 100,000's of test records.

For the book listings, the program builds text files and displays them using a simple GUI text editor, but it can easily be downgraded again to a pure character program for non-GUI linuxes, using a terminal-based text editor like Vim.

For every screen in the program there's a F1-activated help form with a commentary about operational considerations and the widgets used. I've included an Entity-Relationship diagram for better understanding of the database table structure.

*Dependencies:*
The only Python dependencies are: NumPy, PyICU and, of course, npyscreen. The curses library I installed on Windows is "windows-curses". I like to import colored_traceback to better read the errors but it should be commented out.


To run the *bookstore*, simply:
==============================
                            
1) Place all the files of the release into a folder respecting the folder tree.
2) Open a Windows/Linux Terminal window of 81 x 25 characters (there's an extra position on the right). It will work fine on a maximized terminal window as well, but the       actual used space will remain at 80 x 25. 
3) Change directory ("cd") to the folder where the bookstore python modules are located.
4) Run "python3 main.py". Or change "python3" for your own python 3 executable synonym.
---------------------------------------------------------------------------------------------------------------


<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-01.jpg">
</p>
<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-02.jpg">
</p>
<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-03.jpg">
</p>
<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-04.jpg">
</p>
<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-05.jpg">
</p>
<p align="center">
  <img src="https://github.com/dvdvillena/bookstore/blob/master/Docs/Images/Screens-06.jpg">
</p>
