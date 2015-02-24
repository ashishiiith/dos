import threading
import Pyro4
import commands
from dicts import DefaultDict
from lock import Lock
import time
import pickle

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer for data transmission
Pyro4.config.SERVERTYPE="thread" #prespawned pool of thread server
Pyro4.config.THREADPOOL_SIZE=100 #number of threads spawned.


clients = DefaultDict(DefaultDict(0))   #clients[clientID][event] #dictionary to store registered clients.
scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
medalTime = DefaultDict(0)              #time stamp corresponding to medal tally

leaderNum = -1
global offset
rwl = Lock()
offset = 0.0
idNum = 0
isLeader = False

databaseFile = None
class dataUpdate(object):


    def __init__(self):
    
	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
        self.medalType = ['gold', 'silver', 'bronze']  #types of medals
    
    def getID(self):
        #return the assigned id for server
	return idNum

    def ping(self):
	#to ascertain the presence of server
	return True

    '''returns the current leader of the system
    ''' 
    def isLeader(self):
	return leaderNum
 	
    def notify(self, leaderId):
	global leaderNum 
	leaderNum = leaderId

    def updateOffset(self, delta):

        global offset
        offset = delta
        return

    def getTime(self):

        #send the time for clock synchronization
        return (time.time() + offset)

    '''sets the medal count based on input from update server
    '''
    def setScores(self, event, score):
 	global scores
        try:
	    
            tokens = score.split(":")
            rwl.acquire_write()
            print "Set score for Gauls and Romans for "+event+ " event"
            #scores for all the teams in a given event is updated
	    tm  = time.time()+offset
	    tme = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tm))
	    print "Scores for event "+event +" updated at: " + str(tme)
	    print "***********************************************************"
	    print
            for i in xrange(0, len(tokens)):
                scores[self.teams[i]][event] = tokens[i] + "-" + str(tm)
            rwl.release() #lock will be there till updates are not pushed on to registered client
            return
        except:
            rwl.release()
            #print 'My exception occurred, value'
            return

    '''increments the medal count based on input from update server
    '''
    def incrementMedalTally(self, teamName, medalType):

	global medals
        try:
            rwl.acquire_write()
            print "Increment "+medalType+" medal count for "+teamName
            #medal tally is incremented based on team and type of medal
            medals[teamName][medalType] = medals[teamName][medalType] + 1
	    medalTime[teamName] = time.time() + offset
	    tme = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(medalTime[teamName]))
	    print "Medals for team " + teamName+ " updated at: " + str(tme)
	    print "***********************************************************"
            print
            rwl.release()
            return
        except:
            rwl.release()
            print 'My exception occurred, value'
            return

    '''sends back the score count for all the teams stored in the datastructure
    '''
    def getScore(self, eventType):

        try:
            rwl.acquire_read()
            #return scores of all teams for a given event        
            l = []
            print "Get scores of all team for "+eventType
            for team in self.teams:
                l.append(scores[team][eventType])
            rwl.release()
            return l

        except:
            rwl.release()
            print 'My exception occurred, value'
            return
   

    '''sends back the medal tally count for all the teams stored in the datastructure
    '''
    def getMedalTally(self, teamName):

        try:
            #returns the total medal count for a given team
            rwl.acquire_read()
            #return medal tally of all medalType for a given team
            print "Get total medal count of "+teamName
            total = []
            for medal in self.medalType:
                total.append(str(medals[teamName][medal])+"-"+str(medalTime[teamName]))
            rwl.release()
            return total

        except:
            rwl.release()
            print 'My exception occurred, value'
            return

    '''This function selects the leader based on the highest id of the server in the network
    '''
    def startLeaderElection(self):
	
        global leaderNum
	id1 = []
        try:
	    print
	    print "Leader Election Running.."
	    for i in xrange(0, 3):
	    	try: #checks the presence of other server in network
		    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
		    server.ping()
	            id1.append(server.getID())
	    	except:
		    continue

	    id1.append(idNum)
	    leaderNum = max(id1)

	    print "Database server Elected as Leader with NodeId: " + str(leaderNum)
	    print
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
	print "Checking if leader exists..."
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
  	if leader_found == False:
	    print "Leader not responding, start leader election"
	    self.startLeaderElection()

    ''' Berkley clock is ran every 15 seconds for synchronizing the time between two interface servers and database server.
    '''	     
    def berkleyClock(self):
	
	while True:
	    if leaderNum == idNum: #this condition executes when this server is leader
                try:
	            global offset
		    print
	       	    print "Berkley Clock Synchronization Running..."
		    count = 0
		    tme = [None] * 3
		    tm = 0.0
		    for i in xrange(0,3):
	    	        try: #stores the current server time of all the running server
	        	    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
	        	    tme[i] = server.getTime()
			    tm += tme[i]
			    count+=1
	    	        except:
			    continue
		    avg_time = float(tm/count)
	            print "Synchronize"
		    for i in xrange(0, 3):
		        try:#offset is computed here for each of the server to adjust their clock 
		            server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(i))
		            server.updateOffset(tme[i]-avg_time)
		        except:
			    continue
	            print "Clock's Synchronized"
		    print
	        except:
	  	    print 'My exception occurred, value' 
	    else: #this condition will execute when some other server is leader
	        try:
		    server = Pyro4.core.Proxy("PYRONAME:example2.server"+str(leaderNum))
		    print "Probing Time/Master server.."
		    server.ping()
		    print "Time/Master is working fine.."
		    print
	        except:
                     #in case someother server is leader, start leader election again
		    print 'Time server is down is down...Start Leader Election'
		    self.getLeader()
	    time.sleep(10)

    def createDB(self, files, scores, medals):

	try:
	    rwl.acquire_write()
	    pickle.dump(scores,files)
	    pickle.dump(medals,files)
	    rwl.release()
	except:    
	    print 'Exception occurred while writing data into file'
    	    rwl.release()

    def writeFile(self):
	
	global databaseFile
	while True:
		
	  	try:
	   	  databaseFile = open('db.p','wb')	
		  self.createDB(databaseFile, scores, medals)
		  databaseFile.close()	
		except:  	 
       		  print 'Error in File'
		  databaseFile.close()

		time.sleep(5)
def main():

    global leaderNum
    database = dataUpdate()
    status, output=commands.getstatusoutput("hostname")

    threading.Timer(2, database.getLeader).start()  #database initiates leader ELECTION.
    threading.Timer(5, database.berkleyClock).start() #berkley algorithm is ran in separate thread.
    threading.Timer(0, database.writeFile).start()
    #binding the server object onto nameserver for client to access. 
    #starts the database instance and registers in nameserver.
    
    Pyro4.Daemon.serveSimple(
            {
                database: "example2.server0"
            },
            ns = True)
    

    print "database Ready"

if __name__ == "__main__":
    main()
