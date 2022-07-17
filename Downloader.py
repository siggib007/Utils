'''
API testing Script
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script you can put in your specific API details and the script will save the raw response to a text file.
Since some API reponses can be rather large it will process the response one line at a time.

Following packages need to be installed as administrator
pip install requests
pip install jason

'''

# Import libraries

import os
import time
import urllib.parse as urlparse
import platform
import sys
import subprocess
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
        LogEntry ("Problme: Status Code:[] API Response OK={}")
        LogEntry (WebRequest.text)
      else:
        pass
        # LogEntry ("WebRequest status: {}, bStatus: {}".format(WebRequest.status_code,bStatus))
  else:
    LogEntry("WebRequest not defined")

def CleanExit(strCause):
  SendNotification("{} is exiting abnormally on {} {}".format(strScriptName,strScriptHost, strCause))

  objLogOut.close()
  sys.exit(9)

def LogEntry(strMsg,bAbort=False):

  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print (strMsg)
  if bAbort:
    SendNotification("{} on {}: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    CleanExit("")

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
      " make sure you specified it correctly or\n"
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

  if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None:
    bNotifyEnabled = False
    LogEntry("Missing configuration items for Slack notifications, turning slack notifications off")
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

  lstSysArg = sys.argv
  iSysArgLen = len(lstSysArg)
  iTimeOut = 120
  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

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

  strScriptHost = platform.node().upper()
  print ("This script downloads results from a specified URL, and writes to file."
    "\nThis is running under Python Version {}".format(strVersion))
  print ("Running from: {}".format(strRealPath))
  now = time.asctime()
  print ("The time now is {}".format(now))
  print ("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)

  if iSysArgLen > 1:
    strConf_File = lstSysArg[1]
    LogEntry("Argument provided, setting conf file to: {}".format(strConf_File))
  else:
    iLoc = lstSysArg[0].rfind(".")
    strConf_File = lstSysArg[0][:iLoc] + ".ini"
    LogEntry("No Argument found, setting conf file to: {}".format(strConf_File))

  processConf()

  if strSaveFile is None:
    CleanExit("No file name provided, can't continue")
  if strGetURL is None:
    CleanExit("No URL, can't continue")

  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  if strAuth is not None:
    dictHeader["Authorization"] = "Bearer " + strAuth

  LogEntry ("Doing a get to URL:\n{}\n".format(strGetURL))
  try:
    if strUserName != "" and strPWD != "":
      LogEntry("I have none blank credentials so I'm doing basic auth")
      WebRequest = requests.get(strGetURL, timeout=iTimeOut, headers=dictHeader, auth=(strUserName, strPWD), stream=True)
    else:
      LogEntry("I do not have none blank credentials so no basic auth")
      WebRequest = requests.get(strGetURL, timeout=iTimeOut, headers=dictHeader, stream=True)
    LogEntry ("get executed")
  except Exception as err:
    CleanExit ("Issue with get call. {}".format(err))

  if isinstance(WebRequest,requests.models.Response)==False:
    CleanExit ("response is unknown type")

  LogEntry ("call resulted in status code {}".format(WebRequest.status_code))
  if WebRequest.status_code != 200:
    CleanExit("Web response status is not OK, here is the response:\n{}".format(WebRequest.text))
  if strType.lower() == "binary":
    LogEntry("processing binary file")
    objFileOut = open(strSaveFile,"wb")
    iLineNum = 1
    for chunk in WebRequest.iter_content(chunk_size=8192):
      if chunk:
        try:
          print ("Downloaded {} chunks.".format(iLineNum),end="\r")
          iLineNum += 1
          objFileOut.write (chunk)
        except Exception as err:
          CleanExit ("Unexpected issue: {}".format(err))
  else:
    LogEntry("processing non binary file, type {}".format(strType))
    objFileOut = open(strSaveFile,"w")
    iLineNum = 1
    for strLine in WebRequest.iter_lines():
      if strLine:
        try:
          strLine = strLine.decode("ascii","ignore")
          print ("Downloaded {} lines.".format(iLineNum),end="\r")
          iLineNum += 1
          objFileOut.write ("{}\n".format(strLine))
        except Exception as err:
          CleanExit ("Unexpected issue: {}".format(err))

  objFileOut.close()
  LogEntry ("{} results written to file {}".format(strType, strSaveFile))


if __name__ == '__main__':
  main()
