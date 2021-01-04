'''
Script to copy data from the VS View tool and store it in our database
Author Siggi Bjarnason Copyright 2021

Following packages need to be installed as administrator
pip install requests
pip install jason

'''
# Import libraries
import sys
import os
import time
import requests
import platform
import json

# End imports

ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
strF5URL = "https://t2securityselfhelp.eng.t-mobile.com/f5Output.json"

#avoid insecure warning
requests.urllib3.disable_warnings()

def FetchTextFile (strURL):
  try:
    WebRequest = requests.get(strURL, headers={}, verify=False)
  except Exception as err:
    LogEntry ("Issue with API call. {}".format(err))
    return None

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry ("response is unknown type")
    return None
  
  return WebRequest.text

def LogEntry(strMsg):
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
	print(strMsg)

def CleanExit(strCause):
  LogEntry("{} is exiting abnormally on {} {}".format(strScriptName,strScriptHost, strCause))
  objLogOut.close()
  sys.exit(9)

def main ():
  global objLogOut
  global strScriptName
  global strScriptHost

  strBaseDir = os.path.dirname(sys.argv[0])
  strBaseDir = strBaseDir.replace("\\", "/")
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\","/")
  strScriptName = os.path.basename(sys.argv[0])
  iLoc = sys.argv[0].rfind(".")
  # strConf_File = sys.argv[0][:iLoc] + ".ini"

  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
    strLogDir  = strBaseDir + "Logs/"
  if strLogDir[-1:] != "/":
    strLogDir += "/"

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print ("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  objLogOut = open(strLogFile, "w", 1)

  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])
  strScriptHost = platform.node().upper()

  print ("This is a script to fetch data in the VS View Tool and cache it in our DB. This is running under Python Version {}".format(strVersion))
  print ("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print ("The time now is {}".format(dtNow))
  print ("Logs saved to {}".format(strLogFile))

  strF5File = FetchTextFile(strF5URL)
  lstF5json = strF5File.splitlines()

  for strF5json in lstF5json:
    dictF5VS = json.loads(strF5json)
    LogEntry ("Node: {} VS: {} VIP: {} SNAT: {} Pool: {}".format(dictF5VS["Node"],dictF5VS["VS"],
      dictF5VS["IP"],dictF5VS["SNAT"],dictF5VS["Pool"]))



if __name__ == '__main__':
  main()
