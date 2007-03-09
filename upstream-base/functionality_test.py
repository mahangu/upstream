#!/usr/bin/python
# Personal testsuite

import sys, ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('../conf/upstream.conf'))


import inputpluginloader, pluginloader, outputpluginloader, uconf, logsynchronizer

confdir = config.get("paths","confdir")
fp = open("./dump.txt", "w+")
logsync = logsynchronizer.LogSynchronizer(fp)
l_config = uconf.PluginConfigReader(uconf.INPUT, confdir)
log_modules = inputpluginloader.InputPluginLoader(l_config, logsync)

s_config = uconf.PluginConfigReader(uconf.OUTPUT, confdir)
submit_modules = outputpluginloader.OutputPluginLoader(s_config, logsync)
log_modules.start()
submit_modules.start()
log_modules.join()
submit_modules.join()

logsync.dump()
fp.close()	