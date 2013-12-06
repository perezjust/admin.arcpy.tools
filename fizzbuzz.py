#this better work...zen mode inside github
import os, string, sys, traceback
from os.path import join

x = 0
for i in range(0,100):
    x += 1.0
    y = str(x / 3.0)
    z = str(x / 5.0)
    if y.split(".")[1] == "0" and z.split(".")[1] == "0":
        print "fizzbuzz"
    elif y.split(".")[1] == "0" and z.split(".")[1] != "0":
        print "fizz"
    elif y.split(".")[1] != "0" and z.split(".")[1] == "0":
        print "buzz"
    else:
        print x, y, z
