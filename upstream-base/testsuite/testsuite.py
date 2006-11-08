from logmoduleloader import *
from submitmoduleloader import *
from moduleloader import *


def check_log():	
	rmod = __import__(sys.argv[2])
	print dir(rmod)
	lval = LogValidator(None, True, len(sys.argv) > 3 and sys.argv[3] == "verbose")
	if lval.validate_module(rmod):
		print "Module validates"
	else:
		print "Module does not validate\nPossible Reasons:\n"
		
		if not lval.validate_fields(rmod):
			print "Module does not have the correct fields"
		if not lval.validate_execution_hook(rmod, "execute", 0):
			print "Module does not have an execute method that takes 0 arguments"
		if not lval.validate_category_contains_str(rmod):
			print "Module category list contains non-string types"
		
				
def check_submit():
	rmod = __import__(sys.argv[2])
	print rmod
	sval = SubmitValidator(None, True, len(sys.argv) > 3  and sys.argv[3] == "verbose")
	if sval.validate_module(rmod):
		print "Module validates"
	else:
		print "Module does not validate\nPossible Reasons:"		
		if not sval.validate_fields(rmod):
			print "Module does not have the correct fields"
		if not sval.validate_execution_hook(rmod, "execute", 3):
			print "Module does not have an execute method that takes 3 arguments"
			sys.exc_info()[1]
				

if __name__ == "__main__":
	if len(sys.argv) < 3 or sys.argv[1] == "help":
		print "Developer tools for validating modules"
		print "Usage:"
		print "testsuite.py <module type> <module name> [verbose]"
		
	else:
		try:
			if sys.argv[1] == "log":
				check_log()
			elif sys.argv[1] == "submit":
				check_submit()
			else:
				pass
				#check_generic()
			
		except:
			print "\n\nValidation caused exception: "
			print sys.exc_info()[0]
			print sys.exc_info()[1]	
		if len(sys.argv) < 3:
			print "\n\nRerun with verbose as the last argument to get more info"
			
		
		
	

