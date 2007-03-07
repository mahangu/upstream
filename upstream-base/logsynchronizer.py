#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import threading

class LogSynchronizerError(Exception):
	pass
		
class LogSynchronizer:
	"""A class for synchronizing threaded output to an arbitrary file-like
	object. The purpose of this is to prevent unreadable output from multiple
	threads running at the same time, as well as to allow redirection to files"""
	__internal = threading.Lock()
	__store = dict()
	delimiter_string = "----------------------------------------"
	def __init__(self, output_stream = None):
		"""Create a new MessageStreamSyncer that will write to the file-like
		object output_stream when flush() is called. An exception will be thrown
		if output_stream is not a file-like object."""
		if not isinstance(output_stream, file):
			raise LogSynchronizerError, "Output stream was not a file-like object"
		self.__output_stream = output_stream
		self.__out_id = 0
		
	def new_stream(self, title):
		"""Create a new "stream" to write to. Note, this isn't a real stream, just
		an internal buffer to delimit from other calls. The returned stream should be
		referenced by the unique ID that is returned.
		Returns an ID for use with writing to a stream"""
		
		self.__internal.acquire()
		using_id = self.__out_id
		self.__out_id = self.__out_id + 1
		self.__store[using_id] = (title, threading.RLock(), [])
		self.__internal.release()
		return using_id
		
	def write(self, stream_id, msg):
		if self.__output_stream:
			try:
				self.__internal.acquire()
				dict_elem = self.__store[stream_id]
				self.__internal.release()
				s_lock = dict_elem[1]
				s_list = dict_elem[2]				
				# Acquire a lock so multiple thread can write to one stream
				s_lock.acquire()
				s_list.append(msg)
				s_lock.release()
			except KeyError, e:
				raise LogSynchronizerError, "Bad stream ID"
			
	def get_output_stream(self):
		return self.__output_stream
	
	def set_output_stream(self, ostream):
		if not isinstance(output_stream, file):
			raise LogSynchronizerError, "Output stream was not a file-like object"
		self.__output_stream = ostream
		
	def dump(self):
		"""Write all accumulated data to the given output stream. If clear is true
		all previous data is deleted"""
		if self.__output_stream:
			self.__write_all_to_stream()
				
	def __write_all_to_stream(self, reset = True):
		for d_elem_id in self.__store:
				self.__internal.acquire()
				d_elem = self.__store[d_elem_id]
				self.__internal.release()
				self.__write_element(d_elem)
		if reset:
			self.__reset()
				
	def __write_element(self, d_elem):
		d_title = d_elem[0]
		d_lock = d_elem[1]
		d_list = d_elem[2]
		self.__output_stream.write('[' + str(d_title)+ ']\n')
		self.__output_stream.write(self.delimiter_string+'\n')
		d_lock.acquire()
		for d_list_elem in d_list:
			self.__output_stream.write("%s" % str(d_list_elem))
		d_lock.release()
		self.__output_stream.write(self.delimiter_string+'\n')
		
	def __reset(self):
		for d_elem_id in self.__store:
			self.__internal.acquire()
			d_elem = self.__store[d_elem_id]
			self.__internal.release()
			self.__reset_elem(d_elem)
	
	def __reset_elem(self, d_elem):
		d_lock = d_elem[1]
		d_lock.acquire()
		d_elem = (d_elem[0], d_elem[1], [])
		d_lock.release()