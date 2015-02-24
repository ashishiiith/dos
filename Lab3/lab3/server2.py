#How to run this script:"python server2.py <argument>". Argument is either 1(push) or 2(pull).
#Funtionality: This code handles the front-end server with ID=2. It also has a cache implemented in it.
#This server exchange heartbeat messages with other servers in the system to detect failure and keeping system fault tolerant.

import sys
import time
import threading
import Pyro4
import commands
from dicts import DefaultDict
from lock import Lock
import operator

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer for data transmission
Pyro4.config.SERVERTYPE="thread" #prespawned pool of thread server
Pyro4.config.THREADPOOL_SIZE=10 #number of threads spawned.

clients = DefaultDict(DefaultDict(0))   #clients[clientID][event] #dictionary to store registered clients.
cache_scores = DefaultDict(DefaultDict(-1))    #score[team][event] #dictionary to store scores for a given event.
cache_medals = DefaultDict(DefaultDict(-1))    #medals[team][medalTypes] #dictionary to store medal count for a team.

rwl = Lock()

global database #database server object
idNum = 2     #id of the server
clientRegistry = {} #store the registered clients
global cacophonix

push = 0 #decide whether to use pull or push based cache
pull = 0  

class serverPush(object):

    def __init__(self):

	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
	self.medalType = ['gold', 'silver', 'bronze']  #types of medals

    '''Store the cacophonix object to notify it about server failure '''
    def registerCacophonix(self, object_caco):

	global cacophonix 
	cacophonix=object_caco

    '''on receiving update invalidate the cache'''
    def invalidateCache(self, argument, flag):
            
        print "MSG: Invalidating the cache..."
        global cache_scores
        global cache_medals
        if flag=='e':
            for team in self.teams:
                if cache_scores.has_key(team):
                    cache_scores[team][argument] = -1
        else:     
            for medal in self.medalType:
                if cache_medals.has_key(argument):
                    cache_medals[argument][medal] = -1

    '''routes the update server request to database
    ''' 
    def setScores(self, event, score):
	
	try:
	    print "Set the score for database"
	    database.setScores(event, score)
	    print "the score is set"
	    if push==1:
		self.invalidateCache(event, 'e')
		try:
		    server=Pyro4.core.Proxy("PYRONAME:example1.server1")
		    server.invalidateCache(event, 'e')
		except:
		    print "Server " + str(3-idNum) +" is not up"
	    return
	except:
	    print 'My exception occurred, value'
	    return
  
    '''routes the update server request to database
    ''' 
    def incrementMedalTally(self, teamName, medalType):

	try:
	    database.incrementMedalTally(teamName, medalType)
	    if push==1:
		self.invalidateCache(teamName, 'm')
		try:
                    server=Pyro4.core.Proxy("PYRONAME:example1.server1")
                    server.invalidateCache(teamName, 'm')
                except:
                    print "Server " + str(3-idNum) +" is not up"
	    return
	except:
	    print 'My exception occurred, value'
	    return

class scoreRead(object):


    def __init__(self):

        self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
        self.medalType = ['gold', 'silver', 'bronze']  #types of medals

    '''store the reference of registered clients to notify them about server failuires '''
    def registerClient(self, client, serverId):

	global clientRegistry
	clientRegistry[client] = serverId

    '''When server comes up, populate its client registry '''
    def updateClientRegistry(self, client, ID):
	
	print "MSG: Updating Client Registry.."
	global clientRegistry
	clientRegistry[client] = ID

    def ping(self):

	return True

    def getID(self):

	#send the id for node
    	return idNum 

    def heartBeat(self):

	print "NOTE: Starting heart beat message exchange.."
	failed_server=3-idNum
	server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(failed_server))
	fail = 0
	while True:
	    try:
	        server.ping()
		if fail == 1:
		    print "Server coming up. Wait..."
                    #print "Enter the fail condition"
		    for client in clientRegistry:
			try:
                            if clientRegistry[client]==failed_server:
				print "Notify the client.."
                                client.notify(failed_server) #resetting the client to original server
			    #when server comes up, update its registered clients
			    server.updateClientRegistry(client, clientRegistry[client])
			except:
			    print "Client doesn't exist anymore"	
		
		    #server.updateClientRegistry(clientRegistry) #when server comes up, send it the latest client dictionary
		    try:	 #resetting the cacophonix server 
			cacophonix.notify(failed_server)
		    except:
			print "Condition1: Cacophonix server is not up..."
		    fail=0 #resetting server to original state
		    print "Serve came up..."
		print "Server "+str(3-idNum)+ " is alive.."

	    except:
		fail = 1
		print "WARNING: Server " + str(3-idNum) + " is not reachable.."
		
		try:
		    cacophonix.notify(idNum) #notifying Cacophonix to send update to this server
		except:
		    print "WARNING: Condition2: Cacophonix server is not up.."

		for client in clientRegistry:
		    try:
		        if clientRegistry[client]!=idNum:
		            client.notify(idNum) #notifying the clients to use alternate servers
		    except:
			print "Client id not up.."
	    time.sleep(3) 

    def removeDataCache(self, argument, flag, total):

        global cache_medals
        global cache_scores
        try:
            if flag=='m':
                temp_medals=self.medalType
                for i in xrange(0, len(temp_medals)):
                    if cache_medals[argument][temp_medals[i]] != total[i] and cache_medals[argument][temp_medals[i]] != -1:
                        print "MSG: Removing stale data from medal cache"
                        cache_medals[argument][temp_medals[i]] = -1
		    #else:
		    #	print 
            else:
                temp_teams=self.teams
                for i in xrange(0, len(temp_teams)):
                    if cache_scores[temp_teams[i]][argument] != total[i] and cache_scores[temp_teams[i]][argument] != -1:
                        print "MSG: Removing stale data from score cache"
                        cache_scores[temp_teams[i]][argument] = -1
		    #else:
		    #	print
	except:
	    print "stale data removed from cache.."

    ''' periodically checks the cache consistency'''
    def cachePullConsistency(self, database):

        #checking the cache consistency
        print "Pull based caching: Removing stale data from cache.."    
        while True:
            try:
                #update cache_medals
                for team in self.teams:
                    medal = database.getMedalTally(team) 
                    self.removeDataCache(team,'m', medal) 
                #update cache_scores
                for event in self.events:
                    score = database.getScore(event)
                    self.removeDataCache(event, 'e', score)
            except:
                print "WARNING: database server is not up..."
            time.sleep(5)

    '''This function will check whether request score/medal count is present in cache or not '''
    def  checkCache(self, argument, flag):

        global cache_scores
        global cache_medals
        l = []
        f = 1

        try:
            if flag=='e':
		print "***********************************"
                print "MSG: Checking scores in cache.."
                for team in self.teams:
                    #print cache_scores[team][argument]
                    if cache_scores[team][argument] != -1:
                        l.append(cache_scores[team][argument])
                    else:
                        f = 0
                        l = []
                        break
            elif flag=='m':
		print "***********************************"
                print "MSG: Checking medals in cache.."
                for medal in self.medalType:
                    #print cache_medals[argument][medal]
                    if cache_medals[argument][medal] != -1:
                        l.append(cache_medals[argument][medal])
                    else:
                        f = 0
                        l = []
                        break
            if f==1:
                print "found in cache"
		print "***********************************"
            return l
        except:
            print "Entry doesn't exist in cache"
            l = []
            return l

    def updateCache(self, argument, flag, total):

        global cache_medals
        global cache_scores
        try:
            if flag=='m':
                print "MSG: Updating medal_cache.."
                temp_medals=self.medalType
                for i in xrange(0, len(temp_medals)):
                    cache_medals[argument][temp_medals[i]] = total[i]
                print total
            elif flag=='e':
                print "MSG: Updating score_cache.."
                temp_teams=self.teams
                for i in xrange(0, len(temp_teams)):
                    cache_scores[temp_teams[i]][argument] = total[i]
                print total
        except:
            print "My exception occurred, updateCache"

    '''route the client pull request to database to fetch the score
    '''
    def getScore(self, eventType):
	
	try:
            l = []
	    l = self.checkCache(eventType, 'e') #check the cache first
            if len(l) == 0:
                print "NOTE: Cache missed.."
		print "***********************************"
            	l = database.getScore(eventType)
                self.updateCache(eventType,'e',l)
	    return l
 
	except: 
 	    print 'My exception occurred, value'
    	    return

    '''route the client pull request to database to fetch the medal tally
    '''	
    def getMedalTally(self, teamName):

	try:
	    total = []
	    total = self.checkCache(teamName, 'm')
            if len(total) == 0:
                print "NOTE: Cache missed.."
		print "***********************************"
	    	total = database.getMedalTally(teamName)
                self.updateCache(teamName, 'm', total)
	    return total

	except:	
	    print 'My exception occurred, value'
            return

    def receiveRequest(self, request):
	
	try:
	    if request[0] == 'e':
		score = self.getScore(request.split(":")[1])	    
	    elif request[0] == 'm':
		score = self.getMedalTally(request.split(":")[1])	    
	    return score	
	except:
	    print 'My exception occurred, receiveRequest'
            return

def main():

    global database
    global push
    global pull

    #getting database object
    database = Pyro4.core.Proxy("PYRONAME:example2.server0")

    ## registering server objects on nameserver

    server = serverPush()  #all modify functions are here 
    server_read = scoreRead()  #all client read functions are here
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output #set the hostname 
   
    if len(sys.argv) <2:
	print "Error: Insufficient argument"
	print "Enter either 1 or 2 as argument for push/pull based mechanism"
	exit()
    elif sys.argv[1]=='2':
        print "MSG: Pull cache is on.."
        pull = 1
	threading.Timer(0.25, server_read.cachePullConsistency, args=(database,)).start()
    elif sys.argv[1]=='1':
        print "MSG: Push cache is on.."
        push = 1

    print "Server2 Ready..."
    #starting heart beat message exchange..
    threading.Timer(0.25, server_read.heartBeat).start()
	 
    #binding the server object onto nameserver for client to access.
    Pyro4.Daemon.serveSimple(
            {
                server: "example1.server2", server_read: "example2.server2"
            },
            ns = True)

if __name__ == "__main__":
    main() 
