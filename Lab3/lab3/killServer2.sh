#!/bin/bash
ps -ef | grep 'python server2.py' | awk '{print $2}' | xargs kill -9

