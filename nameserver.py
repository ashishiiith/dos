import sys
import commands
import os
status, output=commands.getstatusoutput("hostname")
HOST=output

os.system("python -m Pyro4.naming -n "+HOST)

