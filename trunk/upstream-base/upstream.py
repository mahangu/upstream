#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
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

import sys, optparse, os, ConfigParser
import logmoduleloader, submitmoduleloader

import config
# Deprecated?
#functions.set_modules_dir("submit-modules/")

# Hoorah! for ridiculous namespacings :-)
log_modules = logmoduleloader.LogModuleLoader(config.log_module_path, False, logmoduleloader.moduleloader.DEBUG_ALL)

submit_modules = submitmoduleloader.SubmitModuleLoader(config.submit_module_path, True, submitmoduleloader.moduleloader.DEBUG_ALL)

parser = optparse.OptionParser("%prog yourname@yourdomain.org \"Your support message\" [options]")

for log_module in log_modules:
		lflag = "--%s"%(log_module.module_name)
		print lflag

		parser.add_option("", lflag, action="store_true", help=log_module.module_description, default=False)

parser.add_option("", "--pastebin", dest="pastebin", help="Specify a pastebin module to use.", default=False)

(options, args) = parser.parse_args()


if options.pastebin:
	submit_module = submit_modules[options.pastebin]
	
else:
	submit_module = submit_modules[config.log_module_default]
	
	
log_dict = {}
for x in options.__dict__.iteritems():
	log_module = x[0]
	on = x[1]

	# Is there a nicer way to do this?
	if on and log_module != "pastebin":
		module = log_modules[log_module]
		(name, contents) = module.execute()
		log_dict[name] = contents	
		
		# Deprecated with new log module loader
		# Do we need to do anything relating to "help" below?
		#log_path = functions.get_conf_item("list", section, "file")
		#help = functions.get_conf_item("list", section, "help")
		#log_dict = functions.append_log(log_dict, log_path, section)
		##dump = functions.get_log(log_path)
		##response = functions.add_final(dump)


# Check to see if all mandatory arguments have been filled.


if len(args) != 2:
	print "Please specify the required options. See help (-h) for more information."
	sys.exit(1)


#  Populating final variables.

user_email = args[0]
user_message = args[1]

print user_message
print user_email

#user_logs = functions.get_final()

submit_module.execute(user_email, user_message, log_dict)

