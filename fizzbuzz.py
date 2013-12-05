import arcpy
import os, string, sys, traceback
from os.path import join

x = 0
for i in range(0,100):
    x += 1.0
    y = str(x / 3.0)
    if y.split(".")[1] == "0" and str(x).split(".")[0].endswith("5") or str(x).split(".")[0].endswith("0"):
        print "fizzbuzz - " + str(x)
    elif y.split(".")[1] == "0":
        print "fizz"
    elif str(x).split(".")[0].endswith("5") or str(x).split(".")[0].endswith("0"):
        print "buzz - " + str(x).split(".")[0]
    else:
        print x
