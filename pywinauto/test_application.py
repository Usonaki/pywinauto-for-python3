# GUI Application automation and testing library
# Copyright (C) 2006 Mark Mc Mahon
#
# This library is free software; you can redistribute it and/or 
# modify it under the terms of the GNU Lesser General Public License 
# as published by the Free Software Foundation; either version 2.1 
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public 
# License along with this library; if not, write to the 
#    Free Software Foundation, Inc.,
#    59 Temple Place,
#    Suite 330, 
#    Boston, MA 02111-1307 USA 

import os

import application


def TestExceptions():
	# test that trying to _connect to a non existent app fails
	try:
		app = application.Application()
		app._connect(path = ur"No process with this please")
		assert 0
	except application.ProcessNotFoundError:
		pass

	# test that trying to _connect to a non existent app fails
	try:
		app = application.Application()
		app._start(cmd_line = ur"No process with this please")
		assert 0
	except application.AppStartError:
		pass

	# try when it isn't connected
	try:
		app = application.Application()
		#app._start(ur"c:\windows\system32\notepad.exe")
		app.Notepad.Click()
		assert 0
	except application.AppNotConnected:
		pass


def TestNotepad():
	
	app = application.Application()

#	# for distribution we don't want to connect to anybodies application
#   # because we may mess up something they are working on!
#	try:
#		app._connect(path = ur"c:\windows\system32\notepad.exe")
#	except application.ProcessNotFoundError:	
#		app._start(ur"c:\windows\system32\notepad.exe")
	app._start(ur"c:\windows\system32\notepad.exe")
	
	app.Notepad.MenuSelect("File->PageSetup")

	app.PageSetupDlg.ComboBox1.Select(4)

	app.PageSetupDlg.Printer.Click()		

	TestingCheckBox = 1
	if TestingCheckBox:
		# Open the Connect to printer dialog so we can 
		# try out checking/unchecking a checkbox
		app.PageSetupDlg.Network.Click()

		app.ConnectToPrinter.ExpandByDefault.Check()

		app.ConnectToPrinter.ExpandByDefault.UnCheck()

		# try doing the same by using click
		app.ConnectToPrinter.ExpandByDefault.Click()

		app.ConnectToPrinter.ExpandByDefault.Click()

		# close the dialog
		app.ConnectToPrinter.Cancel.Click()

	app.PageSetupDlg2.Properties.Click()

	docProps = app._window(title_re = ".*Document Properties")

	TestingTabSelect = 1
	if TestingTabSelect:
		docProps.TabCtrl.Select(0)
		docProps.TabCtrl.Select(1)
		docProps.TabCtrl.Select(2)

		docProps.TabCtrl.Select("PaperQuality")
		docProps.TabCtrl.Select("JobRetention")
		docProps.TabCtrl.Select("Layout")


	TestingRadioButton = 1
	if TestingRadioButton:
		docProps.RotatedLandscape.Click()
		docProps.BackToFront.Click()
		docProps.FlipOnShortEdge.Click()

		docProps.Portrait.Click()
		docProps._None.Click()
		docProps.FrontToBack.Click()

	#print docProps._ctrl
	advbutton = docProps.Advanced
	advbutton.Click()

	# close the 4 windows
	app._window(title_re = ".* Advanced Options").Ok.Click()
	docProps.Cancel.Click()
	app.PageSetupDlg2.OK.Click()
	app.PageSetupDlg.Ok.Click()

	# type some text
	app.Notepad.Edit.SetText("I am typing some text to Notepad\r\n\r\nAnd then I am going to quit")

	# exit notepad
	app.Notepad.MenuSelect("File->Exit")
	app.Notepad.No.Click()



def TestPaint():

	app = application.Application()

#	# for distribution we don't want to connect to anybodies application
#   # because we may mess up something they are working on!
#	try:
#		app._connect(path = ur"c:\windows\system32\mspaint.exe")
#	except application.ProcessNotFoundError:	
#		app._start(ur"c:\windows\system32\mspaint.exe")

	app._start(ur"c:\windows\system32\mspaint.exe")

	pwin = app._window(title_re = ".* - Paint")

	# get the reference to the Canvas window
	canvas = pwin.Afx100000008

	# make sure the pencil tool is selected
	pwin.Tools2.Click(coords = (91, 16))

	size = 15
	num_slants = 20

	# draw the axes
	canvas.PressMouse(coords = (size, size * num_slants)) 
	canvas.MoveMouse(coords = (size*num_slants, size*num_slants)) # x and y axes
	canvas.MoveMouse(coords = (size * num_slants, size))
	canvas.ReleaseMouse()

	# now draw the lines
	print "*** if you move your mouse over Paint as it is drawing ***"
	print "*** these lines then it will mess up the drawing!      ***\n"
	for i in range(1, num_slants):
		canvas.PressMouse(coords = (size * num_slants, i * size)) # start

		canvas.MoveMouse(coords = (size * (num_slants - i), size * num_slants)) # x and y axes

		canvas.ReleaseMouse()

	print "Saved image as: Application_Paint_test.png"
	canvas._.CaptureAsImage().save(r"Application_Paint_test.png")
	
	# close Paint
	pwin.MenuSelect("File->Exit")
	
	# Click the no button on teh message box asking if we want to save
	app.Paint.No.Click()
	
def Main():
	TestExceptions()
	TestNotepad()
	TestPaint()

if __name__ == "__main__":
	Main()