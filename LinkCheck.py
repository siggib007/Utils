'''
Link testing script
Author Siggi Bjarnason Copyright 2025
Website http://supergeek.us

Description:
This is script to parse links out of a URL and check if they are valid.

Following packages need to be installed as administrator
pip install requests
pip install jason

'''

# Import libraries
import os
import time
import urllib.parse as urlparse
import subprocess as proc
import platform
import sys
import subprocess
import argparse
try:
  import requests
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
finally:
    import requests
try:
  import json
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'json'])
finally:
    import json
# End imports

def SendNotification (strMsg):
  if not bNotifyEnabled:
    return "notifications not enabled"
  dictNotify = {}
  dictNotify["token"] = strNotifyToken
  dictNotify["channel"] = strNotifyChannel
  dictNotify["text"]=strMsg[:199]
  strNotifyParams = urlparse.urlencode(dictNotify)
  strURL = strNotifyURL + "?" + strNotifyParams
  bStatus = False
  WebRequest = None
  try:
    WebRequest = requests.get(strURL,timeout=iTimeOut)
  except Exception as err:
    LogEntry ("Issue with sending notifications. {}".format(err))
  if WebRequest is not None:
    if isinstance(WebRequest,requests.models.Response)==False:
      LogEntry ("response is unknown type")
    else:
      dictResponse = json.loads(WebRequest.text)
      if isinstance(dictResponse,dict):
        if "ok" in dictResponse:
          bStatus = dictResponse["ok"]
          LogEntry ("Successfully sent slack notification\n{} ".format(strMsg))
        else:
          LogEntry ("Slack notification response: {}".format(dictResponse))
      else:
        LogEntry ("response is not a dictionary, here is what came back: {}".format(dictResponse))
      if not bStatus or WebRequest.status_code != 200:
        LogEntry ("Problem: Status Code:[] API Response OK={}")
        LogEntry (WebRequest.text)
      else:
        pass
        # LogEntry ("WebRequest status: {}, bStatus: {}".format(WebRequest.status_code,bStatus))
  else:
    LogEntry("WebRequest not defined")

def LogEntry(strMsg,bAbort=False):

  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print (strMsg)
  if bAbort:
    SendNotification("{} on {}: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    objLogOut.close()
    sys.exit(9)

def processConf():
  global strSaveFile
  global strGetURL
  global strAuth
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global bNotifyEnabled
  global strType
  global strUserName
  global strPWD


  strNotifyURL = None
  strNotifyToken = None
  strNotifyChannel = None
  bNotifyEnabled = False
  strSaveFile = None
  strGetURL = None
  strAuth = None
  strType = "text"
  strUserName = ""
  strPWD = ""

  if os.path.isfile(strConf_File):
    LogEntry ("Configuration File {} exists".format(strConf_File))
  else:
    LogEntry ("Can't find configuration file {},"
      " make sure you specified it correctly or"
      " it is named after this script and in the same"
      " directory as this script".format(strConf_File),True)

  strLine = "  "
  LogEntry ("Reading in configuration")
  objINIFile = open(strConf_File,"r")
  strLines = objINIFile.readlines()
  objINIFile.close()

  for strLine in strLines:
    strLine = strLine.strip()
    strFullLine = strLine
    iCommentLoc = strLine.find("#")
    if iCommentLoc > -1:
      strLine = strLine[:iCommentLoc].strip()
    else:
      strLine = strLine.strip()
    if "=" in strLine:
      strConfParts = strLine.split("=")
      strLineParts = strFullLine.split("=")
      strVarName = strConfParts[0].strip()
      strValue = strConfParts[1].strip()
      strFullValue = strLineParts[1].strip()
      if strVarName == "NotificationURL":
        strNotifyURL = strValue
      if strVarName == "NotifyChannel":
        strNotifyChannel = strValue
      if strVarName == "NotifyToken":
        strNotifyToken = strValue
      if strVarName == "NotifyEnable":
        strNotifyEnabled = strValue
      if strVarName == "Save":
        strSaveFile = strValue
      if strVarName == "URL":
        strGetURL = strValue
      if strVarName == "Auth":
        strAuth = strValue
      if strVarName == "UserName":
        strUserName = strValue
      if strVarName == "Password":
        strPWD = strFullValue
      if strVarName == "Mode":
        strType = strValue

  if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None or strNotifyEnabled.lower() != "true":
    bNotifyEnabled = False
    LogEntry("Notify turned off or Missing configuration items for notifications, turning notifications off")
  else:
    bNotifyEnabled = True

  LogEntry ("Done processing configuration, moving on")

def main():
  global strConf_File
  global objLogOut
  global strScriptName
  global strScriptHost
  global strSaveFile
  global strGetURL
  global strAuth
  global strType
  global strUserName
  global strPWD
  global iTimeOut

  iTimeOut = 120
  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

  lstSysArg = sys.argv

  strRealPath = os.path.realpath(lstSysArg[0])
  strBaseDir = os.path.dirname(lstSysArg[0])
  if strBaseDir != "":
    if strBaseDir[-1:] != "/":
      strBaseDir += "/"
  strLogDir  = strBaseDir + "Logs"
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print ("\nPath '{0}' for log file didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(lstSysArg[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + "/" + strScriptName[:iLoc] + ISO + ".log"
  iLoc = lstSysArg[0].rfind(".")
  strDefConf = lstSysArg[0][:iLoc] + ".ini"

  strScriptHost = platform.node().upper()
  print ("This script downloads results from a specified URL, and writes to file."
    "\nThis is running under Python Version {}".format(strVersion))
  print ("Running from: {}".format(strRealPath))
  now = time.asctime()
  print ("The time now is {}".format(now))
  print ("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)

  objParser = argparse.ArgumentParser(description="Link checker script")
  objParser = argparse.ArgumentParser()
  objParser.add_argument("--config", "-c", type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("--URL", "-u", type=str, help="Base URL to check")
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Not implemented")
  args = objParser.parse_args()

  strConf_File = args.config
  LogEntry("conf file set to: {}".format(strConf_File))
  processConf()

  if args.URL is not None:
    strGetURL = args.URL

  if strGetURL is None:
    LogEntry("No URL, can't continue",True)

  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"

  LogEntry ("Doing a get to URL:\n{}\n".format(strGetURL))
  try:
    WebRequest = requests.get(strGetURL, timeout=iTimeOut, headers=dictHeader)
    LogEntry ("get executed")
  except Exception as err:
    LogEntry ("Issue with get call. {}".format(err),True)

  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry ("response is unknown type",True)

  LogEntry ("call resulted in status code {}".format(WebRequest.status_code))
  if WebRequest.status_code != 200:
    LogEntry("Web response status is not OK",True)
  else:
    LogEntry("All is OK")
  LogEntry("Done!!")


if __name__ == '__main__':
  main()
