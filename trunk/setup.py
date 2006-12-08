#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
# Build System for versions 0.3+
#
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
from distutils.core import setup
import glob, os

def setup_f():
	global lang_data
	other_data = [('share/pixmaps', ['extras/upstream.png']),
		('share/upstream', ['extras/canoe.glade']),
		('etc/upstream', ['conf/upstream.conf']),]

	complete_data = other_data + lang_data
	print other_data
	print complete_data


	setup(
		name='Upstream',
		version="0.3-alpha",
		author="Mahangu Weerasighe",
		packages=['upstream', 'upstream.log-modules', 'upstream.submit-modules'],
		package_dir={'upstream' : 'upstream-base'},
		package_data={'upstream': ['extras/*']},

		data_files= complete_data,
		scripts=['canoe/canoe', 'kayak/kayak', 'upstream-base/upstream'])

	
	

lang_data = []
for po in glob.glob('po/*.po'):
	lang = os.path.splitext(os.path.basename(po))[0]
	lang_file = os.path.basename(po)
        lang_data.append(("locale/%s/LC_MESSAGES/%s"%(lang,lang_file), ["%s"%(po)]))
	print po
setup_f()



