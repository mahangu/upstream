from logmoduleloader import *
from submitmoduleloader import *
from moduleloader import *


def check_log():
	

if __name__ == "__main__":
	if len(sys.argv) < 3 or sys.argv[1] == "help":
		print "Developer tools for validating modules"
		print "Usage:"
		print "testsuite.py <module type> <package name> <module name>"
		
	else:
		if sys.argv[1] == "log":
			check_log()
		else if sys.arv[1] == "submit":
			check_submit()
		else:
			check_generic()
			
			
		
		
	

