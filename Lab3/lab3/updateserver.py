#cacophonix server. It sends update to servers, which is redirected to database and stored there.
#In case the master server crashes, it will send update to alternate available servers.


import threading
import Pyro4
from dicts import DefaultDict
import time
import commands

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
serverId = 1

class Cacofonix(object):

    '''This function will receive ID of new server to which to send the score, in case previous one crashes.'''
    def notify(self, sID):
        global serverId
        serverId = sID
	print "NOTE: Cacofonix is notified with LIVE SERVER ID: " + str(serverId) 

    def sendUpdates(self, cacophonix):

        server1 = Pyro4.Proxy("PYRONAME:example1.server1") #identifying the server object on nameserver to send updates
        server2 = Pyro4.Proxy("PYRONAME:example1.server2") #identifying the server object on nameserver to send updates
        lines = open("input.txt", "r").readlines() #read the input from input.txt
	
	server1.registerCacophonix(cacophonix)
	server2.registerCacophonix(cacophonix)
	num_lines = len(lines)
	count = 0
	print "NOTE: Cacophonix registered.."	
        for line in lines:
	    ID = serverId
   	    '''MSG: Sending scores and medal tally to front-end server. ''' 
	    try:
	    	tokens = line.split()
	    	if tokens[0] == '1': #this will update scores
	       	    if ID == 1:
	           	server1.setScores(tokens[1], tokens[2].strip("\n"))
	       	    elif ID == 2:
	           	server2.setScores(tokens[1], tokens[2].strip("\n"))
 	    	elif tokens[0] == '2': #this will update medal tally
	       	    if ID == 1:
	           	server1.incrementMedalTally(tokens[1], tokens[2].strip("\n"))
	       	    elif ID == 2:
	           	server2.incrementMedalTally(tokens[1], tokens[2].strip("\n"))
	    except:
		print "WARNING: Server failed.."
		print "MSG: Sending update to alternate server.."
		server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(3-ID))
	   	if tokens[0]=='1':
		    server.setScores(tokens[1], tokens[2].strip("\n"))
		elif tokens[0]=='2':
	            server.incrementMedalTally(tokens[1], tokens[2].strip("\n"))
	    count+=1
	    if count == num_lines:
		break
	    time.sleep(3) #read next update after 3 seconds
	    print

def main():

    cacophonix = Cacofonix()

    #register the cacophonix is name server
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output
    pyrodaemon = Pyro4.Daemon(host=output)
    uri = pyrodaemon.register(cacophonix)
    ns=Pyro4.locateNS()
    ns.register("cacophonix", uri)

    #send score and medal updates to server
    threading.Timer(0.25, cacophonix.sendUpdates, args=(cacophonix, )).start()
    pyrodaemon.requestLoop()

if __name__ == "__main__":
    main()
