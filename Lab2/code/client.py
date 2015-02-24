
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
global server1
global server2
global client

requestId = 1
global clientid

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

    def sendRequest(self, client, serverId, requiredUpdate):
		
                global requestId
		print "Processing Request Number: " +  str(requestId)
		while True:
		    rid = "c:"+str(clientid) + " "+str(requestId)
	            request = [rid, serverId, client, requiredUpdate]
		    ack1 = server1.receiveRequest(request)
		    ack2 = server2.receiveRequest(request)
		    timestamp = max(float(ack1[-2]), float(ack2[-2]))
		    print "Maximum Timestamp: " + str(timestamp)
		    score1 = ""	
  		    score2 = ""
    		    score1 = server1.updateQueue(str(timestamp), rid)
	            score2 = server2.updateQueue(str(timestamp), rid)
		    tok = requiredUpdate.split(":")[1]
		    if score1!= "" and requiredUpdate[0]=='e':
                        print "Scores of team for event: " + tok
			for l in xrange(0, len(score1)):
			    if score1[l] == 0:
			        print "No update received yet .."
				break
				
			    token = score1[l].split("-")
			    if l==0:
			        tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			        print "Score Gauls: " + token[0] + " updated at time " + str(tm)
			    elif l==1:
			        tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			        print "Score Romans: " + token[0] + " updated at time " + str(tm)
			print "***********************************************************"
			print
 
		    elif score1!="" and requiredUpdate[0]=='m':
                        print "Medals count of team: " + tok
			try:
			    for l in xrange(0, len(score1)):
			        token = score1[l].split("-")
			    	if len(token) <2:
			            print "No update received yet .."
				    break
			    	if (l == 0):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Gold: " + token[0] + " updated at time " + str(tm)
			    	elif (l == 1):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Silver: " + token[0] + " updated at time " + str(tm)
			    	elif (l == 2):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Bronze: " + token[0] + " updated at time " + str(tm)
			except:
				print "No update received yet .."
			
			print "***********************************************************"
			print
 
		    elif score2!="" and requiredUpdate[0]=='m':
                        print "Medals count of team: " + tok
			try:
			    for l in xrange(0, len(score2)):
			        token = score2[l].split("-")
			        if len(token) <2:
			            print "No update received yet .."
				    break
			        if (l == 0):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Gold: " + token[0] + " updated at time " + str(tm)
			    	elif (l == 1):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Silver: " + token[0] + " updated at time " + str(tm)
			    	elif (l == 2):
			            tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			            print "Bronze: " + token[0] + " updated at time " + str(tm)
			except:
			        print "No update received yet .."	
			print "***********************************************************"
			print 

		    elif score2!="" and requiredUpdate[0]=='e':
                        #printing time in standard format
                        print "Scores of team for event: " + tok
			for l in xrange(0, len(score2)):
			    if score2[l] == 0:
			        print "No update received yet .."
				break
			    token = score2[l].split("-")
			    if l==0:
			        tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			        print "Score Gauls: " + token[0] + " updated at time " + str(tm)
			    elif l==1:
			        tm = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(token[1])))
			        print "Score Romans: " + token[0] + " updated at time " + str(tm)
			print "***********************************************************"
			print

		    requestId += 1
		    break

    
    def pullRequest(self, serverId):
        #each event is called sequentially to pull update in every five seconds 
        while True:
                self.sendRequest(client, serverId, 'event:skating')
                self.sendRequest(client, serverId, 'event:curling')
                self.sendRequest(client, serverId, 'event:snowbord')
                self.sendRequest(client, serverId, 'medal:Gauls')
                self.sendRequest(client, serverId, 'medal:Romans')
                time.sleep(5)

def main():
    
    global server1
    global server2
    global client   
    global clientid

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
    
    serverId = random.randint(1, 2) #give server id to which score is to be requested
    clientid = sys.argv[1] #assign an id to client from 3-10
    threading.Timer(0.25, client.pullRequest, args=(str(serverId))).start()
    #threading.Timer(0.25, client.sendRequest, args=(client, serverId, 'event:curling')).start()
    #threading.Timer(0.25, client.sendRequest, args=(client, serverId, 'event:snowboard')).start()
    #threading.Timer(0.25, client.sendRequest, args=(client, serverId, 'medal:Gauls')).start()
    #threading.Timer(0.25, client.sendRequest, args=(client, serverId, 'medal:Romans')).start()
    
    pyrodaemon.requestLoop() 

if __name__ == "__main__":
    main()
