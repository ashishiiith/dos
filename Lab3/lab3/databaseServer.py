#Stores the data update sent by the Cacophonix server.
#generates db.p database file. This is the pickle file.

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


scores = DefaultDict(DefaultDict(0))    #score[team][event] #dictionary to store scores for a given event.
medals = DefaultDict(DefaultDict(0))    #medals[team][medalTypes] #dictionary to store medal count for a team.
medalTime = DefaultDict(0)              #time stamp corresponding to medal tally

rwl = Lock()
idNum = 0

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

    '''sets the medal count based on input from update server
    '''
    def setScores(self, event, score):
 	global scores
        try:
	    
            tokens = score.split(":")
            rwl.acquire_write()
	    print
	    print "***********************************************************"
            print "Set score for Gauls and Romans for "+event+ " event"
            #scores for all the teams in a given event is updated
	    tm  = time.time()
	    tme = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tm))
	    print "Scores for event "+event +" updated at: " + str(tme)
	    print "***********************************************************"
	    print
            for i in xrange(0, len(tokens)):
                scores[self.teams[i]][event] = tokens[i]
            rwl.release() #lock will be there till updates are not pushed on to registered client
            return
        except:
            rwl.release()
            print 'My exception occurred, setScores'
            return

    '''increments the medal count based on input from update server
    '''
    def incrementMedalTally(self, teamName, medalType):

	global medals
        try:
            rwl.acquire_write()
	    print
	    print "***********************************************************"
            print "Increment "+medalType+" medal count for "+teamName
            #medal tally is incremented based on team and type of medal
            medals[teamName][medalType] = medals[teamName][medalType] + 1
	    medalTime[teamName] = time.time()
	    tme = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(medalTime[teamName]))
	    print "Medals for team " + teamName+ " updated at: " + str(tme)
	    print "***********************************************************"
            print
            rwl.release()
            return
        except:
            rwl.release()
            print 'My exception occurred, incrementMedalTally'
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
            print 'My exception occurred, getScore'
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
                #total.append(str(medals[teamName][medal])+"-"+str(medalTime[teamName]))
                total.append(str(medals[teamName][medal]))
            rwl.release()
            return total

        except:
            rwl.release()
            print 'My exception occurred, getMedalTally'
            return

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
    Pyro4.config.HOST=output

    #threading.Timer(0, database.writeFile).start()
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
