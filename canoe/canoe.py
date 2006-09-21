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
import sys, time, threading, string, ConfigParser

import functions



def query():
	email_addr = get_email_addr()
	if email_addr:
		support_msg = get_support_msg()
		if support_msg:
			support_type = get_support_type()
			if support_type:
				return RequestHandler(email_addr, support_msg, support_type)	
	# If the user cancelled at any point return false
	return None

	
	
def submit(request):
		
	global window
	window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	window.set_default_size(400, 80)
	global label
	label = gtk.Label("Your request is being submitted, please be patient")
	global vbox
	vbox = gtk.VBox(True)
	global hbuttonbox
	hbuttonbox = gtk.HBox(True)
		
	window.add(vbox)
	vbox.pack_start(label, True, False, 0)
	vbox.pack_start(hbuttonbox, True, False, 0)
		
	#obs = SubmitObserver(request, on_submit_complete)
	window.connect("delete_event", window_delete_event, request)
	window.connect("destroy", window_destroy)
	
	window.show_all()
	print "Finished GUI setup"
	
		
	
	#obs.start()
	request.set_complete_handler(on_submit_complete, None)
	request.start()
	gtk.main()
	
def window_delete_event(widget, event, obs=None):
	# Data should be a reference to observer
	if request.isStarted() and not request.isAlive():
		print "Delete event accepted"
		return False
	else:
		print "Submission not complete!"
		return True
		
def window_destroy(widget, data=None):
	gtk.main_quit()
		
def get_email_addr():
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
	
def get_support_msg():
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
	
def get_support_type():
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


# A class to handle running of requests
class RequestHandler(threading.Thread):
	def __init__(self, email, support, support_type):
		threading.Thread.__init__(self)
		self.email = email
		self.support = support
		self.support_type = support_type
		# These store useful variables for the class
		self.is_started = False
		self.result = None
		self.func_handler = None
		self.func_handler_data = None
	
	def set_complete_handler(self, func_handler, func_handler_data=None):
		self.func_handler = func_handler
		self.func_handler_data = func_handler_data
	
	# Determine if the thread has started yet
	def isStarted(self):
		return self.is_started
	
	# Get the result returned by whatever the current submit method is
	def get_result(self):
		return self.result
		
	def run(self):
		# First thing, we must start the thread
		self.is_started = True
		print "Submitting %s\n%s" % (self.email, self.support)
		print self.support_type
		config = ConfigParser.ConfigParser()
		config.readfp(open('conf/list.conf'))
		for section in self.support_type:
			command = config.get(section, "command")
			dump = functions.get_dump(command)
			response = functions.add_final(dump)
		user_logs = functions.get_final()
		self.result = functions.send_curl(user_logs, self.support, self.email)
		if self.func_handler:
			self.func_handler(self.result, self.func_handler_data)
		
# Class to observe 
#class SubmitObserver(threading.Thread):
	# Initialize, we grab a reference to the RequestHandler thread
	# so that we can spit out proper data
	# This handles connecting the appropriate signals from the
	# close button once the request thread terminates
	# func_handler should be of the form func_handler(request_result, user_data)
#	def __init__(self, request, func_handler, func_handler_data=None):
#		threading.Thread.__init__(self)
#		self.request = request
#		self.func_handler = func_handler
#		self.func_handler_data = func_handler_data
#	def run(self):
#		# Sleep until the request is done
#		while not request.isStarted() or request.isAlive():
#			time.sleep(0.01)
#		result_res = request.get_result()
#		self.func_handler(result_res, self.func_handler_data)
#		
#		
		
#	def isRun(self):
#		return self.request.isStarted() and not self.request.isAlive()

def on_submit_complete(request_result, user_data=None):
	# Once here, the request should be done
	print request_result
	global label
	global window
	global hbuttonbox
	global button
	gtk.threads_enter()	
	label.set_text("The submission is complete")
	button = gtk.Button("Close", gtk.STOCK_CLOSE);		
	hbuttonbox.pack_end(button, False, False, 0)
	button.connect_object("clicked", gtk.Widget.destroy, window)
	button.show()
	gtk.threads_leave()

# Only execute if this was called directly
if __name__ == "__main__":
	# Actual code
	# Initialize threading		
	gtk.threads_init()	
	request = query()
	if request:
		submit(request)