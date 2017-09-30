import os
import stat

f = open("testing_testing", "w")

f.write("line 1")

f.close()

os.chmod("testing_testing", stat.S_IREAD)

os.chmod("testing_testing", stat.S_IWRITE)

f = open("testing_testing", "w")

f.write("line 2")

f.close()

os.chmod("testing_testing", stat.S_IREAD)
