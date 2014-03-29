import time
import threading
import Pyro4
import commands
from dicts import DefaultDict
from lock import Lock

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer for data transmission
Pyro4.config.SERVERTYPE="thread" #prespawned pool of thread server
Pyro4.config.THREADPOOL_SIZE=100 #number of threads spawned.

clients = DefaultDict(DefaultDict(0))   #clients[clientID][event] #dictionary to store registered clients.
scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
rwl = Lock()

global database
offset = 0.0  #used in Berkley algorithm
idNum = 1     #id of the server
class serverPush(object):

    def __init__(self):

	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
	self.medalType = ['gold', 'silver', 'bronze']  #types of medals


    def setScores(self, event, score):
	
	try:
	    database.setScores(event, score)
	    return
	except:
	    print 'My exception occurred, value'
	    return
   
    def incrementMedalTally(self, teamName, medalType):

	global medals
	try:
	    database.incrementMedalTally(teamName, medalType)
	    return
	except:
	    print 'My exception occurred, value'
	    return

class scoreRead(object):

    '''
    def startLeaderElection(self, time, idNum):
        
	offset = time - time.time()
	return  offset
    '''
	 
    def getID(self):

	#send the id for node
    	return idNum 

    def getTime(self):
	
        #send the time for clock synchronization
	return time.time()

    def updateOffset(self, delta)

	global offset
	offset = delta
	return

    def getScore(self, eventType):
	
	try:
            l = []
	    print "Entered get score"
            l = database.getScore(eventType)
	    print "out of get score"
	    return l
 
	except: 
 	    print 'My exception occurred, value'
    	    return
	
    def getMedalTally(self, teamName):

	try:
	    total = [] 
	    total = database.getMedalTally(teamName)
            return total

	except:	
	    print 'My exception occurred, value'
            return

def main():

    global database
    #getting database object
    database = Pyro4.core.Proxy("PYRONAME:database.server")

    ## registering server objects on nameserver

    server = serverPush()  #all modify functions are here 
    server_read = scoreRead()  #all client read functions are here
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output #set the hostname 
    #binding the server object onto nameserver for client to access. 
    Pyro4.Daemon.serveSimple(
            {
                server: "example1.server", server_read: "example2.server"
            },
            ns = True)
    print "Server Ready"
    daemon.requestLoop()

if __name__ == "__main__":
    main() 
