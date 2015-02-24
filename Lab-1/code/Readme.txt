#Written by: Ashish Jain (ashishjain@cs.umass.edu)
#This assignment runs on Pyro4 python library.


Instructions:

1. Run the nameserver file: python nameserver.py (Caution: In case nameserver is running, this will thrown an error. Go to step-2, you are not required to run nameserver.)
2. Run server: python server.py (Note: dicts.py should be in same directory as server.py)
3. Run client: We have six different directories: client-1, client-2, client-3 ... client-6. Go inside each directory and execute "python client.py <arg>"(Note: arg will be
"1" if you want to register that client for curling event or "0" if you don't want to register.) 
4. Run updateserver: python updateserver.py (Note: input.txt should be in the same folder as updateserver.py. It contains predefined medal and score input for the events)

Update server should always start after client.py and server.py started.
