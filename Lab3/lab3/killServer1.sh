#!/bin/bash
ps -ef | grep 'python server1.py' | awk '{print $2}' | xargs kill -9

