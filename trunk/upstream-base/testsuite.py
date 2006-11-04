from logmoduleloader import *
from submitmoduleloader import *
lml = LogModuleLoader(["log-modules"], True, 1)
print "Printing modules"
lml.join()
for m in lml:
	print m
print lml.getCategories()
for c in lml.getCategories():
	print lml.getModulesInCategory(c)
print "***********************************************"
sml = SubmitModuleLoader(["submit-modules"], True, 0)
sml.join()
for m in sml:
	print m
