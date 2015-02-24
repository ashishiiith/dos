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
scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
rwl = Lock()

global database
requestHandling = 0 #find the load of server1
leaderNum = -1
offset = 0.0  #used in Berkley algorithm
idNum = 1     #id of the server
tstamp = 1    #
requestQ = [] #queue to store the requests coming from the client
requestCount = 0 #keeps track of count of the request from client
isLeader = False #tell whether the current server is leader or not
class serverPush(object):

    def __init__(self):

	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
	self.medalType = ['gold', 'silver', 'bronze']  #types of medals


    '''routes the update server request to database
    ''' 
    def setScores(self, event, score):
	
	try:
	    database.setScores(event, score)
	    return
	except:
	    print 'My exception occurred, value'
	    return
  
    '''routes the update server request to database
    ''' 
    def incrementMedalTally(self, teamName, medalType):

	global medals
	try:
	    database.incrementMedalTally(teamName, medalType)
	    return
	except:
	    print 'My exception occurred, value'
	    return

class scoreRead(object):

    def getLoad(self):
        return requestHandling

    def ping(self):
	return True

    def notify(self, leaderId):
	#setting the newly elected leader into system
	global leaderNum 
        leaderNum = leaderId

    def getID(self):

	#send the id for node
    	return idNum 

    def isLeader(self):

	return leaderNum

    def getTime(self):
	
        #send the time for clock synchronization
	return time.time() + offset

    def updateOffset(self, delta):

	global offset
	offset = delta
	return

    '''This function selects the leader based on the highest id of the server in the network
    '''
    def startLeaderElection(self):
        global leaderNum
        id1 = []
        try:
            print "Leader Election Running.."
            for i in xrange(0, 3):
                try:#checks the presence of other server in network
                    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
                    server.ping()
                    id1.append(server.getID())
                except:
                    continue

            id1.append(idNum)
            leaderNum = max(id1)

            print "Server1 Elected as Leader with NodeId: " + str(leaderNum)
            for i in xrange(0, 3):
                try:
                    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
                    server.notify(leaderNum)
                except:
                    continue
        except:
            print 'My exception occurred, value'


    '''This function returns the already selected leader or start leader election in case leader failed.
    '''
    def getLeader(self):
        global leaderNum
        leader_found = False
	print "Checking if Leader already exist..."
        for i in xrange(0,3):
            try:
                server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
                ans = server.isLeader()
                if ans !=-1 and ans==i:
                   leader_found = True
                   leaderNum = i
                   break;
            except:
                continue
        print leader_found, leaderNum
        if leader_found == False:
	    print "Leader not found. Run Leader Election.."
            self.startLeaderElection()

    ''' Berkley clock is ran every 15 seconds for synchronizing the time between two interface servers and database server.
    '''                                
    def berkleyClock(self):

	while True:
            if leaderNum == idNum:#this condition executes when this server is leader
                try:
                    global offset
                    print "Berkley Clock Synchronization Running..."
                    count = 0
                    tme = [None] * 3
                    tm = 0.0
                    for i in xrange(0,3):
                        try:
                            server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
                            tme[i] = server.getTime()
                            tm += tme[i]
                            count+=1
                        except:
                            continue
                    print "count " + str(count)
                    avg_time = float(tm/count)
                    print "Synchronize"
                    for i in xrange(0, 3):
                        try:
                            server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
                            server.updateOffset(tme[i]-avg_time)
                        except:
                            continue
                    print "Clock's Synchronized"
                except:
                    print 'My exception occurred, value'
            else: #this condition will execute when some other server is leader
                try:
                    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(leaderNum))
                    server.ping()
                    print "pinging nameserver: " +str(leaderNum)
                except:
                    #in case someother server is leader, start leader election again
                    print leaderNum
                    print 'Time server is down is down...Start Leader Election'
                    self.getLeader()
            time.sleep(10)

    '''route the client pull request to database to fetch the score
    '''
    def getScore(self, eventType):
	
	try:
            l = []
            l = database.getScore(eventType)
	    return l
 
	except: 
 	    print 'My exception occurred, value'
    	    return

    '''route the client pull request to database to fetch the medal tally
    '''	
    def getMedalTally(self, teamName):

	try:
	    total = []
	    total = database.getMedalTally(teamName)
            return total

	except:	
	    print 'My exception occurred, value'
            return

    '''updates the request Queue based on acknowledgment received from other servers in the network.
    '''
    def updateQueue(self, timestamp, requestId):

	global requestQ
	global requestCount
	try:
            #acquires write lock before updating the request Queue
	    rwl.acquire_write()
	    for l in requestQ:
		if l[0] == requestId:
		    l[-2] = timestamp
		    l[-1] = 'd'
		    break
  	    print "Updating request Queue in Server1" 
	    #sorting the Queue to process the first sent request
	    requestQ.sort(key=operator.itemgetter(-2))
	    request = requestQ[0]
	    score = ""
	    if request[-1] == 'd':
	    	requestCount += 1
		print "Processed total number of requests = " + str(requestCount)
		if requestCount%20 == 0:
                    print "received 20th request. Entering into raffle..." 
                    print request
		    token = request[0].split()
		    clientnum = token[0].split(":")[1]
		    print "Raffle is won by Client Number:" + clientnum
	        requestQ.pop(0)
		if int(request[1]) == idNum:
		    requiredUpdate = request[3]
                    print requiredUpdate
		    if requiredUpdate[0] == 'e':
			score = self.getScore(requiredUpdate.split(":")[1])
		    else:
			score = self.getMedalTally(requiredUpdate.split(":")[1])
	    rwl.release()
	    return score	
	    	
	except:
	    rwl.release()
            print 'My exception occurred, value'
            return

    '''receives the client pull request from client and sends back the acknowledgment
    '''
    def receiveRequest(self, request):
	
	global requestQ
        global requestHandling
	try:
	    rwl.acquire_write()
            requestHandling += 1
	    global tstamp 
	    timestamp = str(tstamp) + "." + str(idNum)
	    tstamp += 1
	    request.append(timestamp)
	    request.append('u')
	    requestQ.append(request)
	    rwl.release()
	    return request	
	except:
	    rwl.release()
	    print 'My exception occurred, value'
            return

def main():

    global database
    #getting database object
    database = Pyro4.core.Proxy("PYRONAME:example2.server0")

    ## registering server objects on nameserver

    server = serverPush()  #all modify functions are here 
    server_read = scoreRead()  #all client read functions are here
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output #set the hostname 

    threading.Timer(3, server_read.getLeader).start() 
    threading.Timer(6, server_read.berkleyClock).start()

    print "Server1 Ready..."

    #binding the server object onto nameserver for client to access.
    Pyro4.Daemon.serveSimple(
            {
                server: "example1.server1", server_read: "example2.server1"
            },
            ns = True)

if __name__ == "__main__":
    main() 
