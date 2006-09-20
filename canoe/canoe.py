#!/usr/bin/python
#
# Canoe - gtk frontend for the upstream
# log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Ryan Zeigler (zeiglerr@gmail.com)
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

import pygtk
pygtk.require('2.0')
import gtk
import sys
import time
import threading


import functions



class Canoe:
	# Initialize the class
	def __init__(self):
		self.request_object = None
	def query(self):
		email_addr = self.email_addr()
		if email_addr:
			support_msg = self.support_msg()
			if support_msg:
				support_type = self.support_type()
				self.request_object = RequestObject(email_addr, support_msg, support_type)				
				return True
		# If the user cancelled at any point return false
		return False
	
		
		
	def submit(self):
		print "Executing submit"
		if self.request_object:
			self.request_object.dump_info()		
			obs_thread = ObserverThread(self.request_object)
			# After launching threads go into the main loop
			obs_thread.start()
			gtk.main()
			print "Main has quit"
	
		
	def email_addr(self):
		# Create the dialog
		dialog = gtk.Dialog("E-Mail Address", None, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		# Pack instruction and text-entry into the dialog
		label = gtk.Label("Enter your e-mail address: ")
		dialog.vbox.pack_start(label, False, False, 5);
		text_entry = gtk.Entry()
		dialog.vbox.pack_start(text_entry, True, True, 5);
		# Show the elements
		
		dialog.set_default_size(400, dialog.get_property("default-height"))
		dialog.show_all()
		
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			dialog.destroy()
			return text_entry.get_text()
		else:
			dialog.destroy()
			return None
		
	def support_msg(self):
		dialog = gtk.Dialog("Problem Description", None, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		# Pack instruction and text-entry into the dialog
		label = gtk.Label("Enter a message describing your problem: ")
		dialog.vbox.pack_start(label, False, False, 5);
		text_view = gtk.TextView()
		text_view.set_wrap_mode(gtk.WRAP_WORD)
		dialog.vbox.pack_start(text_view, True, True, 5);
		# Show the elements		
		dialog.set_default_size(400, 250)
		dialog.show_all()
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			# Extract text from the text view
			m_buffer = text_view.get_buffer()
			m_buffer_s_iter = m_buffer.get_start_iter()
			m_buffer_e_iter = m_buffer.get_end_iter()
			message = m_buffer.get_text(m_buffer_s_iter, m_buffer_e_iter)
			dialog.destroy()
			return message
		else:
			dialog.destroy()
			return None
		
	def support_type(self):
		dialog = gtk.Dialog("Problem Category", None, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		# Pack instruction and text-entry into the dialog
		label = gtk.Label("Select all boxes relevant to your problem: ")
		dialog.vbox.pack_start(label, False, False, 5)
		# Create some check buttons
		network_check = gtk.CheckButton("Network", False)
		video_check = gtk.CheckButton("Video", False)
		# Pack the check buttons into the vbox
		dialog.vbox.pack_start(network_check, False, False, 5)
		dialog.vbox.pack_start(video_check, False, False, 5)
		
		dialog.set_default_size(400, dialog.get_property("default-height"))
		dialog.show_all()
		
		support_list = []
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			support_list.append("standard")
			if network_check.get_active():
				support_list.append("network")
			if video_check.get_active():
				support_list.append("video")
		# Mask is initialized to 0, so we can safely return it
		# if the user didn't enter anything, since we will get false
		dialog.destroy()
		return support_list

# This class is a thread that sits above a request object and
# watches it for changes.  It also runs in its own thread so gtk_main doesn't block
# it is responsible for all window modifications
class ObserverThread(threading.Thread):
	def __init__(self, request_obj):
		threading.Thread.__init__(self)
		self.request = request_obj
		self.request_started = False
	
		# Set up all the variables like the need to be used later
		self.gtkWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.gtkBox = gtk.VBox(False, 5)
		self.gtkLabel = gtk.Label("Your request is being submitted, please be patient, this may take sometime")
		self.gtkButtonBox = gtk.HButtonBox()
		self.gtkButton = gtk.Button("Close", gtk.STOCK_CLOSE)
		
		self.gtkWin.add(self.gtkBox);
		self.gtkBox.pack_start(self.gtkLabel, True, False, 0)
		self.gtkBox.pack_start(self.gtkButtonBox, False, False, 0)
		self.gtkButtonBox.pack_end(self.gtkButton, False, False, 0)
		print "Initialized observer thread"		
			 
	def destroy_callback(self, widget, data=None):
		print "Destroying"
		gtk.main_quit()
	
	def delete_event_callback(self, widget, event, data=None):
		print "Delete event"
		if self.request.isAlive() or not self.request_started:
			return True
		else:
			return False
		
	def run(self):
		print "Running ObserverThread object"
		self.gtkWin.show_all()
		self.gtkWin.connect("delete_event", self.delete_event_callback)
		
		self.request.start()
		self.request_started = True
		
		while self.request.isAlive():
			# Idle until the thread is done
			time.sleep(0.01)
		
		result = self.request.get_response()
		print result
		
		# At the end of the run method, we should attach a callback to the gtk.Button
		# that enables the user to close the window		
		self.gtkButton.connect("clicked", gtk.Widget.destroy, self.gtkWin);
		
class RequestObject(threading.Thread):
	response = None
	# Note: support_type should be a list
	def __init__(self, email_addr, support_msg, support_type):
		threading.Thread.__init__(self)
		self._email_addr = email_addr
		self._support_msg = support_msg
		self._support_type = support_type
		print "Initialized support object"		
	
	def run(self):
		print "Running RequestObject thread"
		# Execute all of the dumps
		for section in self._support_type:
			print "Using section: %s" % section
			command = functions.config.get(section, "command")
			dump = functions.get_dump(command)
			functions.add_final(dump)
		user_logs = functions.get_final()
		self.response = functions.send_curl(user_logs, self._support_msg, self._email_addr)
		
	def get_response(self):
		return self.response
		
	def dump_info(self):
		print (self._email_addr, self._support_msg, self._support_type)
		
if __name__ == "__main__":
	print "Executing Canoe PyGTK frontend"	
	canoe_obj = Canoe();
	if canoe_obj.query():
		canoe_obj.submit()
