#!/usr/bin/python
# Personal testsuite

import sys, ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('../conf/upstream.conf'))


import pluginloader, uconf

confdir = config.get("paths","confdir")

l_config = uconf.PluginConfigReader(uconf.LOG, confdir)
log_modules = pluginloader.PluginLoader(l_config, sys.stdout)
log_modules.start()
log_modules.join()
log_modules.wait()
log_modules.dump_log()