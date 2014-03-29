
''' 
Our Client is multithreaded to receive scores and medal tally for each event and team periodcally. 
Hence for each client (processs), we will be having multiple threads running.
'''

import sys
import Pyro4
import threading
import time
from multiprocessing import Process
import commands

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer is used for data transmission between client and server
global server
class Client(object):
    def __init__self(self):

	self.eventType = ['skating', 'curling', 'snowboard']
        self.teams = ['Gauls', 'Romans']
        self.medals = ['gold', 'silver', 'bronze'] 
    
    def viewScores(self, eventType):
	#send getScore request to server periodically and receive updateed scores of an event for all the teams. 
	 while True:
	     scores = server.getScore(eventType)
	     print "Score: " + eventType + " - Gauls:" + str(scores[0])+ " Romans:"+str(scores[1])
	     time.sleep(3)

    def viewMedal(self, team):	    
	#send getMedalTally request to server periodically and receive total medal count for a team.
	 while True:
	     medal = server.getMedalTally(team)
	     print "Medal: " + team + " gold:" + str(medal[0]) + " silver:"+str(medal[1]) + " bronze:" + str(medal[2])
	     time.sleep(3)

def main():
    
    global server
   
    client = Client()
    '''
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output
    pyrodaemon = Pyro4.Daemon(host=output)
    uri = pyrodaemon.register(client)
    ns=Pyro4.locateNS()
    ns.register("client", uri)
    ''' 
    #get server object for pulling updates 
    server = Pyro4.core.Proxy("PYRONAME:example2.server")
    
    threading.Timer(0.25, client.viewScores, args=('skating', )).start()
    threading.Timer(0.25, client.viewScores, args=('curling', )).start()
    threading.Timer(0.25, client.viewScores, args=('snowboard', )).start()
    threading.Timer(0.25, client.viewMedal, args=('Gauls', )).start()
    threading.Timer(0.25, client.viewMedal, args=('Romans', )).start()
    #pyrodaemon.requestLoop() 

if __name__ == "__main__":
    main()
