#How to run it? python client.py
#Functionality: It will register itsef randomly to any of the LIVE server in the system. It periodically pulls scores and medal tally from the servers.
#Messages will be displayed containing score and medal tally on the standard output.

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
import random
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle') #pickle serializer is used for data transmission between client and server

global serverId
global server1
global server2

class Client(object):
    def __init__self(self):

	self.eventType = ['skating', 'curling', 'snowboard']
        self.teams = ['Gauls', 'Romans']
        self.medals = ['gold', 'silver', 'bronze'] 
    
    def viewScores(self, eventType,scores):
	#send getScore request to server periodically and receive updateed scores of an event for all the teams. 
	print "******************************************************"
	print "Score received from Server: " + str(serverId)
	print "Score: " + eventType + " - Gauls:" + str(scores[0])+ " Romans:"+str(scores[1])
	print "******************************************************"

    def viewMedal(self, team, medal):	    
	#send getMedalTally request to server periodically and receive total medal count for a team.
	print "******************************************************"
	print "Medal Tally received from Server: " + str(serverId)
	print "Medal: " + team + " gold:" + str(medal[0]) + " silver:"+str(medal[1]) + " bronze:" + str(medal[2])
	print "******************************************************"

    def notify(self, sID):
	#changing the active serverId
	global serverId
	serverId = sID
	print "Client is notified: serverID: " + str(serverId)

    def setServerId(self, ID):
	global serverId
	serverId = ID

    def sendRequest(self, request):
	#send the request to assigned servers
	ID=serverId
	answer=['empty']
	try:
	    #based on the assigned server, route the requests.
	    if ID == 1: 
	        answer=server1.receiveRequest(request)
	    elif ID == 2:
		answer=server2.receiveRequest(request)
	    if request[0]=='e':
	        self.viewScores(request.split(":")[1], answer)
	    else:
	    	self.viewMedal(request.split(":")[1], answer)
	except:
	    print "WARNING: Server crashed..."
	    print "MSG: Sending pull request to alternate server..." 
	    s = Pyro4.core.Proxy("PYRONAME:example2.server"+str(3-ID))
	    try:
   	        answer=s.receiveRequest(request)
		if request[0]=='e':
	    	    self.viewScores(request.split(":")[1], answer)
		else:
	    	    self.viewMedal(request.split(":")[1], answer)
	    except:
		print "WARNING: Server is down.."
		print "MSG: Request getting routed to alternate Server.."


    def pullRequest(self):
	#each event is called sequentially to pull update in every five seconds 
        while True:
		print "Server sending the score is Server:" + str(serverId)
                self.sendRequest('event:skating')
                self.sendRequest('event:curling')
                self.sendRequest('event:snowboard')
                self.sendRequest('medal:Gauls')
                self.sendRequest('medal:Romans')
                time.sleep(5)


def main():
    
    global server1
    global server2
    global serverId
 
    client = Client()
    
    status, output=commands.getstatusoutput("hostname")
    Pyro4.config.HOST=output
    pyrodaemon = Pyro4.Daemon(host=output)
    uri = pyrodaemon.register(client)
    ns=Pyro4.locateNS()
    ns.register("client", uri)	
    

    #get server object for pulling updates 
    server1 = Pyro4.core.Proxy("PYRONAME:example2.server1")
    server2 = Pyro4.core.Proxy("PYRONAME:example2.server2")

    #generate random client id 
    serverId = random.randint(1, 2)
    print "Registered with Server: " +  str(serverId)
 
    #register clients in server directory

    '''
	register to alternate server in case the chosen server is unavailable
    '''
    try:
        server1.registerClient(client, serverId)
    except:
	print "WARNING: Server 1 is down..."
	if serverId==1:
	    serverId=2
	    print "MSG: Registering to SERVER 2"

    try:
        server2.registerClient(client, serverId) 
    except:
	print "WARNING: Server 2 is down..."
	if serverId==2:
	    serverId=1
	    print "MSG: Registering to SERVER 1"

    threading.Timer(0.25, client.pullRequest).start()

    pyrodaemon.requestLoop() 

if __name__ == "__main__":
    main()
