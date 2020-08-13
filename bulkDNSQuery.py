'''
Script that does a DNS query on hostnames from a file
Author Siggi Bjarnason Copyright 2019
Website http://www.supergeek.us

'''
# strFilein = "C:/temp/cmdb_ci_server.csv"
# strOutFile = "C:/temp/cmdb_ci_server-fixed.csv"

import sys
import os
import socket
import time
try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print ("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

strRealPath = os.path.realpath(sys.argv[0])
strVersion = "{0}.{1}.{2}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2])
print("This script reads in a text file of host names and attempts to do DNS resolution on each line.")
print("Each Line is expected to be nothing but a single hostname")
print("This is running under Python Version {}".format(strVersion))
print("Running from: {}".format(strRealPath))
now = time.asctime()
print("The time now is {}".format(now))

strFilein = ""

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
  strFilein = sa[1]

if strFilein == "":
  if btKinterOK:
    print ("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
    root = tk.Tk()
    root.withdraw()
    strFilein = filedialog.askopenfilename(title = "Select file",filetypes = (("CSV files","*.csv"),("Text files","*.txt"),("all files","*.*")))
  else:
    strFilein = input("Please provide full path and filename for the file to be processed: ")

if strFilein == "":
  print ("No filename provided unable to continue")
  sys.exit()

if os.path.isfile(strFilein):
  print ("OK found {}".format(strFilein))
else:
  print ("Can't find {}".format(strFilein))
  sys.exit(4)


iLoc = strFilein.rfind(".")
strOutFile = strFilein[:iLoc] + "-DNS.csv"

objFileIn  = open(strFilein,"r")
strLine = "start"

objFileOut = open(strOutFile,"w")
objFileOut.write ("Hostname,IPAddr\n")

while strLine:
  strLine = objFileIn.readline()
  strLine = strLine.strip()
  strLineParts = strLine.split(".")
  if strLine != "":
    if len(strLineParts) > 0:
      strHostName = strLineParts[0]
      try:
        strIPAddr = socket.gethostbyname(strHostName)
        print ("{0} resolves to {1}".format(strHostName,strIPAddr))
      except OSError as err:
        print ("Socket Exception for {1}: {0}".format(err,strHostName))
        strIPAddr  = "Socket Exception: {0}".format(err)
      except Exception as err:
        print ("Generic Exception for {1}: {0}".format(err,strHostName))
        strIPAddr  = "Generic Exception: {0}".format(err)
      objFileOut.write ("{},{}\n".format(strLine,strIPAddr))

print ("All Done, results in {}".format(strOutFile))