# For anyone reading this, Please don't change/move/delete this, unless you know what this does, and more importantly Why this is here, and what problem this fixes.
# This fixes an error with the test 'test_unit.py' where it couldn't load a module from outside it's folder.
# Why this happens, because when you run ^ from it's folder, python only looks for modules in the folder (path) of the running python program.
# To fix this I have this run this program outside, which being next two both 'test' and 'panzee' Python will find that 'panzee' is a module, and then I have to run 'test_unit.py', with the same 'settings/path/privliges' for a lack of a better word
import time
import sys
try:
	execfile("test/test_unit.py") # This executes 'test_unit.py' with the same 'settings/path/privliges', for again a lack of a better work
except Exception,error: # A note: This DOESN'T always work espesilly when it comes to pytest's 'assert' trackback/assertion errors msg feedback
	print("Done testing unit... Errors Reported")
	print(str(error))
else: 
	print("Done testing unit... No Errors Reported")
time.sleep(5)