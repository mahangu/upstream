#!/usr/bin/python
#
# Upstream pastebin.ca  module.
# Copyright (C) 2006  Ryan Zeigler <zeiglerr@gmail.com>
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
import  time

module_name = "none"
module_description = "Module to use in the event we want to test that the base works but don't want to spam a pastebin site."
module_submit_url = "http://nothing/here/now/move/along.html"


def execute(submit_name, submit_message, log_tuple):
	time.sleep(10)
	return (True, "http://nothing/here/now/move/along.html")
