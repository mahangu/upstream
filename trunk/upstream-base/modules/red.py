#!/usr/bin/python
#
# Upstream paste.redkrieg.com  module.
# Copyright (C) 2006  Mahangu Weerasinghe (mahangu@gmail.com)
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

import webbrowser,os
	
logs = logs.replace("\"","")
	
url= "http://pastebin.redkrieg.com?page=submit"
referer= "http://pastebin.redkrieg.com"
# misc= "&channel=none&colorize=none"

# Prepare Curl object
import pycurl
from urllib import urlencode
from StringIO import StringIO
c = pycurl.Curl()
c.setopt(pycurl.URL, url)
c.setopt(pycurl.POST, 1)
post_data = { 'subject': "Upstream<%s>"%email, 'title': "title", 'code': message + logs }
c.setopt(pycurl.POSTFIELDS, urlencode(post_data))
c.setopt(pycurl.REFERER, referer)
clog = StringIO()
c.setopt(pycurl.WRITEFUNCTION, clog.write)
c.perform()

file = open ( 'red.html', 'w' )

foo = clog.getvalue()

file.write ( "%s"%(foo) )

file.close() 

# print clog.getvalue()

webbrowser.open_new("red.html")
