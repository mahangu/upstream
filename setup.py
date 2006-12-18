#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
# Lodge build system for versions 0.3+
#
# Copyright (C) 2006  Mahangu Weerasinghe <mahangu@gmail.com>
# Jason Ribeiro <jason.ribeiro@gmail.com> et al.
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
import glob, os, sys
import ConfigParser, shutil

UPSTREAM_SETUP_CONFIG = 'setup.cfg'

config = ConfigParser.ConfigParser()
config.readfp(open(UPSTREAM_SETUP_CONFIG))
prefix = config.get("install", "prefix")

# Constants
genpaths = config.get("paths", "generate_paths")
if genpaths == "yes":
	rootdir = config.get("paths", "rootdir")
	confdir = config.get("paths", "confdir")
	datadir = config.get("paths", "datadir")
	imagedir = config.get("paths", "imagedir")
	gladedir = config.get("paths", "gladedir")
	localedir = config.get("paths", "localedir")
	docdir = config.get("paths", "docdir")


def setup_upstream():
	global lang_data
	other_data = [(imagedir, ['extras/upstream.png']),
		(gladedir, ['extras/canoe.glade']),
		(confdir, ['conf/upstream.conf']),
		(confdir + "/log-plugins.d/", ['conf/log-plugins.d/log-plugins.conf']),
		(confdir + "/submit-plugins.d/", ['conf/submit-plugins.d/submit-plugins.conf'])]

	complete_data = other_data + get_trans() + get_docs()
	
	setup(
		name='Upstream',
		version="0.3-alpha",
		author="Mahangu Weerasighe",
		packages=['upstream', 'upstream.log-modules', 'upstream.submit-modules'],
		package_dir={'upstream' : 'upstream-base'},
		package_data={'upstream': ['extras/*']},

		data_files= complete_data,
		scripts=['canoe/canoe', 'kayak/kayak', 'upstream-base/upstream'])

	
def get_trans():
	lang_data = []
	for root, dirs, files in os.walk('po/'):
		for name in files:
			ext = name.split(".")
			lang = root.split("/")[1]
			if len(ext) == 2:
				if ext[1] == "mo":
					lang_file = root + "/" +  name
					print name
					print lang
					print lang_file				
					lang_data.append((localedir + "/%s/LC_MESSAGES/"%(lang), ["%s"%(lang_file)]))
	return lang_data

		
def get_docs():
	import re
	doc_data = []
	for root, dirs, files in os.walk('docs/'):
		for name in files:
			print root
			if re.search(".svn", root):
				print "Subversion file found, skipping."
			else:	
				doc_file = root + "/" + name
				doc_data.append((docdir, ["%s"%(doc_file)]))
	return doc_data

def get_constants():
	confdir_full = "/" + confdir
	datadir_full = os.path.join(rootdir,datadir)
	imagedir_full = os.path.join(rootdir,imagedir)
	localedir_full = os.path.join(rootdir,rootdir)
	gladedir_full = os.path.join(rootdir,gladedir)
	docdir_full = os.path.join(rootdir,docdir)
	
	# TODO: move this to constants.py.in
	f = open("conf/upstream.conf.in","r")
	 
	conf_template = f.read()
	
	print conf_template
	 
	conf_template_modified = conf_template%(confdir_full, datadir_full,imagedir_full,gladedir_full,localedir_full,docdir_full)
		
	print conf_template_modified
	
	shutil.copyfile('conf/upstream.conf', './upstream.conf.bk') #backup upstream.conf to wherever we're running setup from
	
	f = open("conf/upstream.conf","w") #open the real upstream.conf which will be packaged
	f.writelines(conf_template_modified) #write to file

if __name__ == "__main__":
	
	if genpaths == "yes":
		get_constants()
	
	setup_upstream()
