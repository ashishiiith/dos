import threading
import Pyro4
import commands
from dicts import DefaultDict

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer for data transmission
Pyro4.config.SERVERTYPE="thread" #prespawned pool of thread server
Pyro4.config.THREADPOOL_SIZE=100 #number of threads spawned.

class Lock:
  """
A simple reader-writer lock Several readers can hold the lock
simultaneously. Write locks have priority over reads to
prevent write starvation.
"""
  def __init__(self):
    self.rwlock = 0
    self.writers_waiting = 0
    self.monitor = threading.Lock()
    self.readers_ok = threading.Condition(self.monitor)
    self.writers_ok = threading.Condition(self.monitor)
  def acquire_read(self):
    """Acquire a read lock. Several threads can hold this typeof lock.
It is exclusive with write locks."""
    self.monitor.acquire()
    while self.rwlock < 0 or self.writers_waiting:
      self.readers_ok.wait()
    self.rwlock += 1
    self.monitor.release()
  def acquire_write(self):
    """Acquire a write lock. Only one thread can hold this lock, and
only when no read locks are also held."""
    self.monitor.acquire()
    while self.rwlock != 0:
      self.writers_waiting += 1
      self.writers_ok.wait()
      self.writers_waiting -= 1
    self.rwlock = -1
    self.monitor.release()
  def release(self):
    """Release a lock, whether read or write."""
    self.monitor.acquire()
    if self.rwlock < 0:
      self.rwlock = 0
    else:
      self.rwlock -= 1
    wake_writers = self.writers_waiting and self.rwlock == 0
    wake_readers = self.writers_waiting == 0
    self.monitor.release()
    if wake_writers:
      self.writers_ok.acquire()
      self.writers_ok.notify()
      self.writers_ok.release()
    elif wake_readers:
      self.readers_ok.acquire()
      self.readers_ok.notifyAll()
      self.readers_ok.release()

clients = DefaultDict(DefaultDict(0))   #clients[clientID][event] #dictionary to store registered clients.
scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
rwl = Lock()

class serverPush(object):

    def __init__(self):

	self.events = ['skating', 'curling', 'snowboard'] #events list
        self.teams = ['Gauls', 'Romans']  #teams list
	self.medalType = ['gold', 'silver', 'bronze']  #types of medals

    def pushUpdate(self, eventType, score):

	#pass the scores to registered clients
	for client in clients:
	    for events in clients[client]:
	        if events == eventType:
		    print "SERVER Push UPDATE"
	            client.pushedScores(eventType, score)#score is pushed to client from here 
   	            print "Done Update"

    def setScores(self, event, score):
	
	global scores
	try:
	    tokens = score.split(":")
	    rwl.acquire_write()
	    print "Set score for Gauls and Romans for "+event+ " event"
	    #scores for all the teams in a given event is updated
	    for i in xrange(0, len(tokens)):
	        scores[self.teams[i]][event] = tokens[i]
	    self.pushUpdate(event, score)
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
	    rwl.release()
	    return
	except:
	    rwl.release()
	    print 'My exception occurred, value'
	    return

class scoreRead(object):
	 
    def getScore(self, eventType):

        obj=serverPush()
	try:
            rwl.acquire_read()
	    #return scores of all teams for a given event        
            l = []
	    print "Get scores of all team for "+eventType
	    for team in obj.teams:
                l.append(scores[team][eventType])
            rwl.release()
	    return l
 
	except: 
	    rwl.release()
 	    print 'My exception occurred, value'
    	    return
	
    def getMedalTally(self, teamName):

	obj=serverPush()
	try:
	    #returns the total medal count for a given team
	    rwl.acquire_read()
	    total = 0
	    #return medal tally of all medalType for a given team
	    print "Get total medal count of "+teamName
	    total = []
	    for medal in obj.medalType:
	        total.append(int(medals[teamName][medal]))
	    rwl.release()
            return total

	except:	
	    rwl.release()
	    print 'My exception occurred, value'
            return
	
    def registerClient(self, clientID, eventType):

	global clients	
	#registers the clients for pushing updates
	try:
	    rwl.acquire_write()
            clients[clientID][eventType] = 1 #clientID is the reference of client object. Using it we can push server update onto specific client.
	    rwl.release()

	except:
	    rwl.release()
	    print 'My exception occurred, value'
  	return 

def main():

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
