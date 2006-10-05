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

import functions, asyncsubmit, submitmoduleloader




def query():
	email_addr = get_email_addr()
	if email_addr:
		support_msg = get_support_msg()
		if support_msg:
			support_logs = get_support_type()
			if support_logs:				
				module = get_submit_module()
				if module:
					return asyncsubmit.ThreadSubmit(module, email_addr, support_msg, support_logs, on_submit_complete, None)	
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
	window.connect("delete_event", window_delete_event, request)
	window.connect("destroy", window_destroy)	
	window.set_title("Completing...")
	window.show_all()		
	request.start()
	gtk.main()
	
def window_delete_event(widget, event, obs=None):
	# Data should be a reference to observer
	if request.isStarted() and not request.isAlive():
		return False
	else:
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
	# We scan the configuration so that everything works
	
	sections_dict = dict([(x, gtk.CheckButton(x, False)) for x in functions.get_conf_sections("list")])

			
	#network_check = gtk.CheckButton("Network", False)
	#video_check = gtk.CheckButton("Video", False)
	# Pack the check buttons into the vbox
	#dialog.vbox.pack_start(network_check, False, False, 5)
	#dialog.vbox.pack_start(video_check, False, False, 5)
	for x in sections_dict:
		dialog.vbox.pack_start(sections_dict[x])
	
	dialog.set_default_size(400, dialog.get_property("default-height"))
	dialog.show_all()
	
	log_dict = None
	if dialog.run() == gtk.RESPONSE_ACCEPT:
		#support_list.append("standard")
		#if network_check.get_active():
		#	support_list.append("network")
		#if video_check.get_active():
		#	support_list.append("video")
		for x in sections_dict:
			if sections_dict[x].get_active():
				log_path = functions.get_conf_item("list", x, "file")
				log_dict = functions.append_log(log_dict, log_path, x)
	# Mask is initialized to 0, so we can safely return it
	# if the user didn't enter anything, since we will get false
	dialog.destroy()
	return log_dict

def get_submit_module():
	dialog = gtk.Dialog("Upload Server", None, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
	label = gtk.Label("Select a server to upload your data to")
	dialog.vbox.pack_start(label, False, False, 5)
	
	combobox = gtk.combo_box_new_text()
	server_list = [module for module in module_loader]
	for mod in server_list:
		combobox.append_text(mod.module_name)
	dialog.vbox.pack_start(combobox, False, False, 5)		
	if server_list:
		text_list = [gtk.Label(server_list[0].module_name), gtk.Label(server_list[0].module_description), gtk.Label(server_list[0].module_submit_url)] 
	else:
		text_list = [gtk.Label(""), gtk.Label(""), gtk.Label("")]
		
	for x in text_list:
		dialog.vbox.pack_start(x, False, False, 10)
		
	combobox.connect("changed", submit_select_changed, text_list)
	
	dialog.show_all()
	if dialog.run() == gtk.RESPONSE_ACCEPT:
		module = module_loader.module(combobox.get_active_text())
		dialog.destroy()
		return module
	else:
		return None
		
	
	

def submit_select_changed(widget, text_list):
	mod_name = widget.get_active_text()
	module = module_loader.module(mod_name)
	text_list[0].set_text(module.module_name)
	text_list[1].set_text(module.module_description)
	text_list[2].set_text(module.module_submit_url)
		
def on_submit_complete(request_result, user_data=None):
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
	window.set_title("Finished")
	gtk.threads_leave()

# Only execute if this was called directly
if __name__ == "__main__":
	# Actual code
	# Initialize threading
	functions.set_conf_dir("../upstream-base/conf/")
	module_loader = submitmoduleloader.SubmitModuleLoader(["../upstream-base/submit-modules"], False, submitmoduleloader.moduleloader.DEBUG_ALL)
	gtk.threads_init()	
	request = query()
	if request:
		submit(request)
