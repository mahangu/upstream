#!/usr/bin/python
#
# Canoe - gtk frontend using glade for Upstream
# log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Jason Ribeiro <jason.ribeiro@gmail.com>
# Based on canoe.py by Ryan Zeigler <zeiglerr@gmail.com>
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

# TODO: Fix spacing between widgets
# TODO: use defaults in conf file

import sys
# Deprecated
#import config
import logmoduleloader, submitmoduleloader
from getpass import getuser

try:
	import pygtk
	pygtk.require("2.0")
except:
	pass
try:
	import gtk
	import gtk.glade
except:
	sys.exit(1)

class CanoeGTK:
	"""This is the canoe frontend for Upstream"""

	def __init__(self, log_modules, submit_modules):
		self.log_modules = log_modules
		self.submit_modules = submit_modules

		# Set the Glade file
		self.gladefile = "canoe.glade"  
		self.wTree = gtk.glade.XML(self.gladefile) 

		self.cat_dict = self.__gui_add_logs()
		self.submits_combobox = self.__gui_add_submits()

		# Set the username as the default nickname
		self.wTree.get_widget("entry_email").set_text(getuser())

		# Create our dictionay and connect it
		dic = { "on_btnNext_clicked" : self.btnNext_clicked,
				"on_btnBack_clicked" : self.btnBack_clicked,
				"on_btnCancel_clicked" : self.destroy,
				"on_MainWindow_destroy" : self.destroy }
		self.wTree.signal_autoconnect(dic)


	def __gui_add_logs(self):
		"""Create the checkboxes for selecting logs"""

		vbox = self.wTree.get_widget("vbox_problems")
		if self.log_modules.threaded:
			self.log_modules.join()
		categories = self.log_modules.getCategories()
		cat_dict = dict([(cat, gtk.CheckButton(cat, False)) for cat in categories])
		for cat in cat_dict:
			vbox.pack_start(cat_dict[cat])
		vbox.show_all()
		return cat_dict

	def __gui_add_submits(self):
		"""Create the combobox for the pastebin modules"""

		vbox = self.wTree.get_widget("vbox_modules")
		combobox = gtk.combo_box_new_text()
		vbox.pack_start(combobox)
		# Join the thread since we are using threading
		if self.submit_modules.threaded:
			self.submit_modules.join()
			
		for module in self.submit_modules:
			combobox.append_text(module.module_name)
		vbox.reorder_child(combobox, 1)

		# Set default value
		# TODO: Read the conf file and use it to select the default
	
		combobox.connect("changed", self.submit_select_changed)
		combobox.set_active(0)
		#self.submit_select_changed(combobox)
		vbox.show_all()
		return combobox


	# Callbacks
	def submit_select_changed(self, widget):
		label_name = self.wTree.get_widget("label_submit_name")
		label_description = self.wTree.get_widget("label_submit_description")
		label_url = self.wTree.get_widget("label_submit_url")

		name = widget.get_active_text()
		module = self.submit_modules[name]

		label_name.set_text(module.module_name)
		label_description.set_text(module.module_description)
		label_url.set_text(module.module_submit_url)

	def btnBack_clicked(self, widget):
		nb = self.wTree.get_widget("MainNotebook")
		back = self.wTree.get_widget("btnBack")
		next = self.wTree.get_widget("btnNext")
		
		# Make the "back" button inactive if we are coming from the second page
		if nb.get_current_page() is 1:
			back.set_sensitive(False)

		# Change the "finish" button to a "next" button if we are coming from the last page
		if nb.get_current_page() is nb.get_n_pages()-1:
			next.set_label("gtk-go-forward")

		nb.prev_page()

	def btnNext_clicked(self, widget):
		nb = self.wTree.get_widget("MainNotebook")
		back = self.wTree.get_widget("btnBack")
		next = self.wTree.get_widget("btnNext")

		# Run the submit code if we are on the last page
		if nb.get_current_page() is nb.get_n_pages()-1:
			email = self.get_email()
			support_logs = self.get_support_logs()
			support_msg = self.get_support_msg()
			module = self.get_module()
			#print email, support_logs, support_msg, module  # debug print 
			# TODO: We need to update this to use threading and asyncsubmit like canoe.py
			module.execute(email, support_msg, support_logs)
			# TODO: We are exiting for now but we should give the user some confirmation beforehand
			sys.exit(0)

		# Go to the next page if we aren't on the last page
		else:
			# Make the "back" button active if we are coming from the first page
			if nb.get_current_page() is 0:
				back.set_sensitive(True)

			# Change the "next" button to a "finish" button if we are going to the last page
			if nb.get_current_page() is nb.get_n_pages()-2:
				next.set_label("gtk-ok")

			nb.next_page()


	# Helper functions
	def get_email(self):
		return self.wTree.get_widget("entry_email").get_text()

	def get_support_logs(self):
		log_dict = {}
		for cat in self.cat_dict:
			if self.cat_dict[cat].get_active():
				for mod in self.log_modules.getModulesInCategory(cat):
					module = log_modules[mod.module_name]
					(name, contents) = module.execute()
					log_dict[name] = contents 
		return log_dict 

	def get_support_msg(self):
		text_view = self.wTree.get_widget("textview_description")
		m_buffer = text_view.get_buffer()
		m_buffer_s_iter = m_buffer.get_start_iter()
		m_buffer_e_iter = m_buffer.get_end_iter()
		message = m_buffer.get_text(m_buffer_s_iter, m_buffer_e_iter)
		return message

	def get_module(self):
		module = self.submit_modules[self.submits_combobox.get_active_text()]
		return module


	def main(self):
		gtk.main()
	def destroy(self, widget):
		gtk.main_quit()

if __name__ == "__main__":
	# Initialize
	log_modules = logmoduleloader.LogModuleLoader(["log-modules"], False, submitmoduleloader.moduleloader.DEBUG_ALL, True)
	submit_modules = submitmoduleloader.SubmitModuleLoader(["submit-modules"], False, logmoduleloader.moduleloader.DEBUG_ALL, True)

	# Load the GUI
	canoe = CanoeGTK(log_modules, submit_modules)
	canoe.main()
