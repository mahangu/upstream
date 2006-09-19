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
import functions

STANDARD_MASK = 1 << 0
VIDEO_MASK = 1 << 1
NETWORK_MASK = 1 << 2

class Canoe:
	# Initialize the class
	def __init__(self):
		self.request_object = 0
		self.continue_input = 1
		
	def query(self):
		email_addr = self.email_addr()
		if email_addr:
			support_msg = self.support_msg()
			if support_msg:
				suport_mask = support_mask()
				request_object = RequestObject(email_addr, support_msg, support_mask)				
				return True
		# If the user cancelled at any point return false
		return False
	
		
		
	def submit(self):
		pass	
		
	def email_addr(self):
		# Create the dialog
		dialog = gtk.Dialog("E-Mail Address", None, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		# Pack instruction and text-entry into the dialog
		label = gtk.Label("Enter your e-mail address: ")
		dialog.vbox.pack_start(label, True, False, 5);
		text_entry = gtk.Entry()
		dialog.vbox.pack_start(text_entry, True, True, 5);
		# Show the elements
		label.show()
		text_entry.show()
		if dialog.run() == gtk.RESPONSE_ACCEPT:
			print "Debug MSG: Got email addr: %s" % text_entry.get_text()
			return text_entry.get_text()
		else:
			print "Debug MSG: Aborted on email addr:"
			return None
		
	def support_msg(self):
		pass
		
	def support_mask(self):
		pass
		
class RequestObject:
	def __init__(self, email_addr, support_msg, support_mask):
		self.email_addr = email_addr
		self.support_msg = support_msg
		self.support_mask = support_mask
		
	def set_email_addr(self, addr):
		self.email_addr = addr
	
	def set_support_msg(self, msg):
		self.support_msg = msg
		
	def set_support_mask(self, mask):
		self.support_type_mask = self.support_type_mask | mask
		
	def dump_info(self):
		print "%s\n%s\n%b" % (self.email_addr, self.support_msg, self.support_type_mask)
		
if __name__ == "__main__":
	print "Executing Canoe PyGTK frontend"	
	canoe_obj = Canoe();
	canoe_obj.query()
