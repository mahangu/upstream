#!/usr/bin/python
#
# Kayak frontend for the upstream log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Ryan Zeigler (zeiglerr@gmail.com) (Canoe)
# Copyright (C) 2006  Michael Pyne (michael.pyne@kdemail.net)
#
# Ported to PyQt by Michael Pyne, using code borrowed from kdesvn-pywizard
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.\

from qt import *
import sys, time, threading, string, ConfigParser, re

import functions, asyncsubmit, submitmoduleloader, logmoduleloader

class BoldLabel(QLabel):
	def __init__(self, label, parent):
		QLabel.__init__(self, "<center><h3><b>" + label + "</b></h3></center>", parent)

# Standard class to use for all the pages in the wizard
class WizardPage(QWidget):
	def __init__(self, wizard, title):
		QWidget.__init__(self, wizard)

		# QVBoxLayout used instead of QVBox so we can add stretchies
		self.layout = QVBoxLayout(self, 0, 10) # margin, then spacing

		self.wizard = wizard
		self.title = title
		self.label = BoldLabel(title, self)

		self.child = QVBox(self) # use this to add new widgets into
		self.child.setMargin(0)
		self.child.setSpacing(10)

		self.layout.addWidget(self.label)
		self.layout.addStretch()
		self.layout.addWidget(self.child)
		self.layout.addStretch()

		wizard.addPage(self, title)

		self.connect(wizard, SIGNAL("selected(const QString &)"), self.pageSelected)

	# This may be called even when this page isn't selected, so check against
	# the title to be sure.
	def pageSelected(self, title):
		if str(title) == self.title:
			self.preparePage()

	def preparePage(self):
		pass

class IntroPage(WizardPage):
	def __init__(self, wizard):
		WizardPage.__init__(self, wizard, "Kayak Introduction")

		self.body = QLabel("""<qt><center>This program will assist you in
		sending troubleshooting data to aid support personnel in diagnosing
		problems on your system.</center></qt>""", self.child)

class EmailPage(WizardPage):
	def __init__(self, wizard):
		WizardPage.__init__(self, wizard, "E-mail")

		formBox = QVBox(self.child)
		formBox.setSpacing(12)

		self.label = QLabel("Please enter your e-mail address", formBox)
		self.emailText = QLineEdit(formBox)

		self.connect(self.emailText, SIGNAL("textChanged(const QString&)"), wizard.setEmail)

class SupportPage(WizardPage):
	def __init__(self, wizard):
		WizardPage.__init__(self, wizard, "Problem Description")

		self.group = QVGroupBox("Please select categories this problem affects", self.child)
		self.types = { }

		if log_loader.threaded:
			log_loader.join()
		for x in log_loader:
			typeBox = QCheckBox(x.module_name, self.group)
			self.connect(typeBox, SIGNAL("toggled(bool)"), self.typeChecked)

		self.label = QLabel("Please enter a description of the problem as well", self.child)
		self.msg = QTextEdit(self.child)
		self.connect(self.msg, SIGNAL("textChanged()"), self.msgChanged)

	def msgChanged(self):
		message = str(self.msg.text())
		self.wizard.setMessage(message)

	def typeChecked(self, activated):
		button = self.sender() # Scary that this works. :)
		type = str(button.text())
		if type == None:
			return

		self.types[type] = activated

		activatedCategories = [ ]
		for type in self.types.iterkeys():
			if self.types[type]:
				activatedCategories.append(type)

		self.wizard.setCategories(activatedCategories)

class SubmitPage(WizardPage):
	def __init__(self, wizard):
		WizardPage.__init__(self, wizard, "Submit")

		self.label = QLabel("Please select the server to submit troubleshooting data to.", self.child)
		self.serverBox = QComboBox(False, self.child)
		if submit_loader.threaded:
			submit_loader.join()
		self.servers = [mod for mod in submit_loader]
		for server in self.servers:
			self.serverBox.insertItem(server.module_name)

		self.connect(self.serverBox, SIGNAL("activated(int)"), self.serverChanged)
		self.name = QLabel('a', self.child)
		self.description = QLabel('b', self.child)

		# Make this multi-line.  But, this breaks layouting. :(
		self.description.setTextFormat(Qt.RichText)
		self.url = QLabel('c', self.child)
		self.serverChanged(0)

		self.wizard.setFinishEnabled(self, True)

	def serverChanged(self, index):
		self.name.setText(self.servers[index].module_name)
		description = re.sub('\s+', ' ', self.servers[index].module_description)
		self.description.setText(description)
		self.url.setText(self.servers[index].module_submit_url)

		module = submit_loader[self.servers[index].module_name]
		self.wizard.setModule(module)
	
def threadCompleteHandler(result, userData = None):
	global wizardDialog
	wizardDialog.result = result
	QTimer.singleShot(0, wizardDialog.submitDone)

class UpstreamWizard(QWizard):
	def __init__(self, parent=None):
		QWizard.__init__(self, parent)

		self.email = ''
		self.module = None
		self.categories = [ ]

	def showPage(self, page):
		QWizard.showPage(self, page)

        # No help yet
		self.setHelpEnabled(page, 0)

	def setEmail(self, email):
		self.email = str(email)

	def setModule(self, module):
		self.module = module

	def setMessage(self, message):
		self.message = str(message)

	def setCategories(self, categories):
		self.categories = categories

	def categoryLogs(self):
		logs = None
		for x in self.categories:
			name, contents = log_loader[x].execute()
			if not logs:
				logs = { name: contents }
			else:
				logs[name] = contents
		return logs
			
	def submitDone(self):
		if self.result and self.result.bool_success:
			QMessageBox.information(self, "Kayak", "Submission completed successfull and is located at <br />" + self.result.result_url)
		else:
			QMessageBox.information(self, "Kayak", "Submission failed :-(")
		self.done(0)

	def makeRequest(self):
		print "EMail: " + self.email
		print "Message: " + self.message

		request = asyncsubmit.ThreadSubmit(
			self.module,
			self.email,
			self.message,
			self.categoryLogs(),
			threadCompleteHandler,
			None)
		return request

	def accept(self):
		# Submit the stuff
		self.finishButton().setEnabled(False)
		global wizardDialog

		wizardDialog = self
		self.setCaption("Kayak - Submitting Report")
		self.setEnabled(False)

		request = self.makeRequest()

		if request:
			request.start()
		else:
			QMessageBox.critical(self, "Kayak",
			    "Unable to submit report (unable to create the request)")
			QWizard.accept(self)

def main(args):
	app = QApplication(args)
	wizard = UpstreamWizard()

	# Bold looks better. :-)
	font = wizard.titleFont()
	font.setBold(True)
	wizard.setTitleFont(font)

	page1 = IntroPage(wizard)
	page2 = EmailPage(wizard)
	page3 = SupportPage(wizard)
	page4 = SubmitPage(wizard)

	wizard.exec_loop()

# Only execute if this was called directly
if __name__ == "__main__":
	# Actual code
	# Initialize threading
	
	log_loader = logmoduleloader.LogModuleLoader(["../upstream-base/log-modules"], True, 1)

	submit_loader = submitmoduleloader.SubmitModuleLoader(["../upstream-base/submit-modules"], True, 1)
	
	main(sys.argv)

# vim: set noet sw=4 ts=4 tw=0:

