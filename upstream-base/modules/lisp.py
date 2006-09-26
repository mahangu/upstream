#!/usr/bin/python
#
# Upstream paste.lisp.org module.
# Copyright (C) 2006  Joel Pan (toastyou@gmail.com)
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
	
logs = logs.replace("\"","")
	
url= "http://paste.lisp.org/submit"
referer= "http://paste.lisp.org"
misc= "&channel=none&colorize=none"

# Prepare Curl object
import pycurl
from urllib import urlencode
from StringIO import StringIO
c = pycurl.Curl()
c.setopt(pycurl.URL, url)
c.setopt(pycurl.POST, 1)
post_data = { 'username': "Upstream<%s>"%email, 'title': message, 'text': logs }
c.setopt(pycurl.POSTFIELDS, urlencode(post_data)+misc)
c.setopt(pycurl.REFERER, referer)
clog = StringIO()
c.setopt(pycurl.WRITEFUNCTION, clog.write)
c.perform()

print clog.getvalue()