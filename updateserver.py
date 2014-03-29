import threading
import Pyro4
from dicts import DefaultDict
import time

Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')

def main():

    server = Pyro4.Proxy("PYRONAME:example1.server") #identifying the server object on nameserver to send updates
    lines = open("input.txt", "r").readlines() #read the input from input.txt
    for line in lines:
	tokens = line.split()
	if tokens[0] == '1': #this will update scores
	   server.setScores(tokens[1], tokens[2].strip("\n"))
 	elif tokens[0] == '2': #this will update medal tally
	   server.incrementMedalTally(tokens[1], tokens[2].strip("\n"))
	time.sleep(3) #read next update after 3 seconds
	print

if __name__ == "__main__":
    main()
