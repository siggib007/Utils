'''
Link testing script
Author Siggi Bjarnason Copyright 2025
Website http://supergeek.us

Description:
This is script crawls a URL to parse links out and check if they are valid.

Following packages need to be installed as administrator
pip install requests
pip install jason
pip install bs4

'''

# Import libraries
import os
import time
import urllib.parse as urlparse
import subprocess
import platform
import sys
import subprocess
import argparse
try:
  from bs4 import BeautifulSoup
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'bs4'])
finally:
    from bs4 import BeautifulSoup
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

def FetchEnv (strEnvName):
  if os.getenv(strEnvName) != "" and os.getenv(strEnvName) is not None:
    return os.getenv(strEnvName)
  else:
    return None

def SendNotification (strMsg):
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global strNotifyEnabled
  global bNotifyEnabled

  if not bNotifyEnabled:
    return "notifications not enabled"
  iTimeOut = 20  # Connection timeout in seconds
  iMaxMSGlen = 19999  # Truncate the slack message to this length

  strNotifyURL = strNotifyURL
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = "Bearer " + strNotifyToken

  dictPayload = {}
  dictPayload["channel"] = strNotifyChannel
  dictPayload["text"] = strMsg[:iMaxMSGlen]

  bStatus = False
  WebRequest = None
  try:
    WebRequest = requests.post(
      strNotifyURL, timeout=iTimeOut, json=dictPayload, headers=dictHeader)
  except Exception as err:
    return "FAIL. Issue with sending notifications. {}".format(err)
  if WebRequest is not None:
    if isinstance(WebRequest,requests.models.Response)==False:
      LogEntry ("response is unknown type")
    else:
      dictResponse = json.loads(WebRequest.text)
      if isinstance(dictResponse,dict):
        if "ok" in dictResponse:
          bStatus = dictResponse["ok"]
          if bStatus:
            LogEntry ("Successfully sent slack notification\n{} ".format(strMsg))
          else:
            LogEntry ("Failed to send slack notification")
        else:
          LogEntry ("Slack notification response: {}".format(dictResponse))
      else:
        LogEntry ("response is not a dictionary, here is what came back: {}".format(dictResponse))
      if not bStatus or WebRequest.status_code != 200:
        LogEntry ("Problem: Status Code:{} API Response OK={}".format(WebRequest.status_code,bStatus))
        LogEntry (WebRequest.text)
  else:
    LogEntry("WebRequest not defined")

def LogEntry(strMsg,bAbort=False):

  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  if not bQuiet:
    print (strMsg)
  if bAbort:
    SendNotification("{} on {} aborting: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    objLogOut.close()
    sys.exit(9)

def GetURL(strURL,dictHeader):
  WebRequest = None

  if iVerbose > 0:
    LogEntry ("Doing a get to URL:{}".format(strURL))
  try:
    WebRequest = requests.get(strURL, timeout=iTimeOut, headers=dictHeader)
    if iVerbose > 1:
      LogEntry ("get executed")
  except Exception as err:
    LogEntry ("Issue with get call,. {}".format(err))
    return None

  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry ("response is unknown type")
    return None
  if iVerbose > 1:
    LogEntry ("call resulted in status code {}".format(WebRequest.status_code))
  if WebRequest.status_code != 200:
    LogEntry("Web response status is not OK")
  else:
    if iVerbose > 2:
      LogEntry("All is OK")
  return WebRequest

def processConf():
  global strSaveFolder
  global strGetURL
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global strNotifyEnabled
  global strBlockedURLs

  strNotifyURL = None
  strNotifyToken = None
  strNotifyChannel = None
  strSaveFolder = ""
  strGetURL = None

  if os.path.isfile(strConf_File):
    LogEntry ("Configuration File {} exists".format(strConf_File))
  else:
    LogEntry ("Can't find configuration file {}".format(strConf_File))
    return

  strLine = "  "
  LogEntry ("Reading in configuration")
  objINIFile = open(strConf_File,"r")
  strLines = objINIFile.readlines()
  objINIFile.close()

  for strLine in strLines:
    strLine = strLine.strip()
    iCommentLoc = strLine.find("#")
    if iCommentLoc > -1:
      strLine = strLine[:iCommentLoc].strip()
    else:
      strLine = strLine.strip()
    if "=" in strLine:
      strConfParts = strLine.split("=")
      strVarName = strConfParts[0].strip()
      strValue = strConfParts[1].strip()
      if strVarName == "NotificationURL":
        strNotifyURL = strValue
      if strVarName == "NotifyChannel":
        strNotifyChannel = strValue
      if strVarName == "NotifyToken":
        strNotifyToken = strValue
      if strVarName == "NotifyEnable":
        strNotifyEnabled = strValue
      if strVarName == "SaveFolder":
        strSaveFolder = strValue
      if strVarName == "URL":
        strGetURL = strValue
      if strVarName == "Block":
        strBlockedURLs = strValue

  LogEntry ("Done processing configuration, moving on")
