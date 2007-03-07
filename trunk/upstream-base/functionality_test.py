#!/usr/bin/python
# Personal testsuite

import sys, ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('../conf/upstream.conf'))


import pluginloader, uconf, logsynchronizer

confdir = config.get("paths","confdir")
osync = logsynchronizer.LogSynchronizer(sys.stdout)
config = uconf.PluginConfigReader(uconf.SUBMIT, confdir)
modules = pluginloader.PluginLoader(config, osync )

modules.start()

while not modules.validation_is_complete():
	sys.stdout.write('\r')
	modules.wait_progress_change()
	import_c = modules.get_import_count()
	valid_c = modules.get_validation_count()
	valid =  modules.get_valid_plugin_count()
	if import_c == 0:
		import_c = 1
	percent = ((valid_c + 0.0)/import_c) * 100
	sys.stdout.write('[')
	for x in range(0, 100, 10):
		if x < percent:
			sys.stdout.write('-')
		else:
			sys.stdout.write(' ')
	sys.stdout.write(']')
	sys.stdout.write("    ")
	sys.stdout.write("%s %s %s\n" % (import_c, valid_c, valid))
print "\nDone"
modules.wait_validation_complete()