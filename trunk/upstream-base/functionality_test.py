#!/usr/bin/python
# Personal testsuite

import sys, ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('../conf/upstream.conf'))


import pluginloader, uconf

confdir = config.get("paths","confdir")
osync = pluginloader.OutputSynchronizer(sys.stdout)
l_config = uconf.PluginConfigReader(uconf.LOG, confdir)
log_modules = pluginloader.PluginLoader(l_config, osync )
s_config = uconf.PluginConfigReader(uconf.SUBMIT, confdir)
submit_modules = pluginloader.PluginLoader(s_config, osync)
log_modules.start()
submit_modules.start()
log_modules.join()
submit_modules.join()
osync.dump()