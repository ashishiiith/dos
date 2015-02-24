#Written by: Ashish Jain (ashishjain@cs.umass.edu)
#This assignment runs on Pyro4 python library.

-	Run nameserver: python nameserver.py (Note: In case this command throws error, move to next step because nameserver is already
	running.)
-	Run database server: python databaseserver.py
-	Run server 1: python server1.py (dicts.py and lock.py should be in same folder as this script file)
-	Run server 2: python server2.py
	Note: These two are two front-end server which you start in any order.
-	Run clients: python client.py <id> (Any number of client can be run with client ids assigned. Ids can vary from 3-10. Run it on
	different terminals and you can see the input. Example: python client.py 3).
-	Run Updateserver: It will read input from input.txt: python updateserver.py

NOTE: We are doing raffle entry for 20th request so as to see output early rather than waiting for every 100th request.
