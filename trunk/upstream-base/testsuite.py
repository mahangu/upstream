from logmoduleloader import *
from submitmoduleloader import *
lml = LogModuleLoader(["log-modules"], True, 1)
lml.join()
print lml.getCategories()

sml = SubmitModuleLoader(["submit-modules"], True, 1)
sml.join()
for m in sml:
	print m
