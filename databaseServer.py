import threading
import Pyro4
import commands
from dicts import DefaultDict
from lock import Lock
import time

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer for data transmission
Pyro4.config.SERVERTYPE="thread" #prespawned pool of thread server
Pyro4.config.THREADPOOL_SIZE=100 #number of threads spawned.


clients = DefaultDict(DefaultDict(0))   #clients[clientID][event] #dictionary to store registered clients.
scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
medalTime = DefaultDict(0)              #time stamp corresponding to medal tally
rwl = Lock()
offset = 0.0
idNum = 3
class dataUpdate(object):


    def __init__(self):
    
	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
        self.medalType = ['gold', 'silver', 'bronze']  #types of medals

    def setScores(self, event, score):

 	global scores
        try:
	    
            tokens = score.split(":")
            rwl.acquire_write()
            print "Set score for Gauls and Romans for "+event+ " event"
            #scores for all the teams in a given event is updated
            for i in xrange(0, len(tokens)):
                scores[self.teams[i]][event] = tokens[i] + "-" + str(time.time()+offset)
            rwl.release() #lock will be there till updates are not pushed on to registered client
            return
        except:
            rwl.release()
            #print 'My exception occurred, value'
            return

    def incrementMedalTally(self, teamName, medalType):

	global medals
        try:
            rwl.acquire_write()
            print "Increment "+medalType+" medal count for "+teamName
            #medal tally is incremented based on team and type of medal
            medals[teamName][medalType] = medals[teamName][medalType] + 1
	    medalTime[teamName] = time.time() + offset
            rwl.release()
            return
        except:
            rwl.release()
            print 'My exception occurred, value'
            return

    def getScore(self, eventType):

        try:
	    print "Entered get score"
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

    def getID(self):

	return idNum

    def getMedalTally(self, teamName):

        try:
            #returns the total medal count for a given team
	    print "Entered get medal"
            rwl.acquire_read()
            #return medal tally of all medalType for a given team
            print "Get total medal count of "+teamName
            total = []
            for medal in self.medalType:
                total.append(str(medals[teamName][medal])+"."+str(medalTime[teamName]))
            rwl.release()
            return total

        except:
            rwl.release()
            print 'My exception occurred, value'
            return

    def startLeaderElection(self, server1, server2):

        try:
	    print "Leader Election Running.."
	    rwl.acquire_read()
	    id1 = server1.getID() 
	    id2 = server2.getID()
	    num = max(id1, id2,idNum)
	    rwl.release()
	    print "Leader Elected"
	    return num
	except:
	    rwl.release()
	    print 'My exception occurred, value'
	    
    def berkleyClock(self, server1, server2):

        try:
	   global offset
	   while True:
	       "Berkley Clock Synchronization Running..."
	       rwl.acquire_write()
	       time1 = server1.getTime()
	       time2 = server2.getTime()
	       offset1 = time1 - time.time()
	       offset2 = time2 - time.time()
	       offset = (offset1 + offset2)/2 
	       server1.updateOffset(offset)
	       server2.updateOffset(offset)
	       rwl.release()
	       "Clock's Synchronized"
	       time.sleep(20)
	except:
	   rwl.release()
	   print 'My exception occurred, value' 

def main():

    database = dataUpdate()
    server1 = Pyro4.core.Proxy("PYRONAME:example1.server")
    #server2 = Pyro4.core.Proxy("PYRONAME:example1.server")
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output #set the hostname 

    #binding the server object onto nameserver for client to access. 
    Pyro4.Daemon.serveSimple(
            {
                database: "database.server"
            },
            ns = True)
    print "database Ready"

    number = database.startLeaderEelection(server1, server2)  #database initiates leader ELECTION
    print number
    #if number == 3: #based on the id number of leader, berkley clock syncrhonization begin
    #    threading.Timer(0.0, database.berkleyClock, args=(server1, server2)).start()
    daemon.requestLoop()

if __name__ == "__main__":
    main()
