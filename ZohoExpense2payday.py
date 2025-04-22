'''
Script Transfers expenses from Zoho Expense to payday

Author Siggi Bjarnason 21 april 2025
Nanitor Copyright 2025.

Following packages need to be installed
pip install requests
pip install jason

'''
# Import libraries
import os
import time
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

try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

if sys.version_info[0] > 2:
  import urllib.parse as urlparse
  # The following line surpresses a warning that we aren't validating the HTTPS certificate
  requests.urllib3.disable_warnings()
else:
  import urllib as urlparse
  # The following line surpresses a warning that we aren't validating the HTTPS certificate
  import urllib3
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# End imports

# Few globals
tLastCall = 0
iTotalSleep = 0

# Define few Defaults
iLogLevel = 4  # How much logging should be done. Level 10 is debug level, 0 is none
iTimeOut = 180  # Max time in seconds to wait for network response
iMinQuiet = 2  # Minimum time in seconds between API calls

# sub defs


def CleanExit(strCause):
  """
  Handles cleaning things up before unexpected exit in case of an error.
  Things such as closing down open file handles, open database connections, etc.
  Logs any cause given, closes everything down then terminates the script.
  Parameters:
    Cause: simple string indicating cause of the termination, can be blank
  Returns:
    nothing as it terminates the script
  """
  LogEntry("{} is exiting abnormally on {}: {}".format(
    strScriptName, strScriptHost, strCause), 0)

  objLogOut.close()
  print("objLogOut closed")

  sys.exit(9)

def LogEntry(strMsg, iMsgLevel, bAbort=False):
  """
  This handles writing all event logs into the appropriate log facilities
  This could be a simple text log file, a database connection, etc.
  Needs to be customized as needed
  Parameters:
    Message: Simple string with the event to be logged
    iMsgLevel: How detailed is this message, debug level or general. Will be matched against Loglevel
    Abort: Optional, defaults to false. A boolean to indicate if CleanExit should be called.
  Returns:
    Nothing
  """
  if iLogLevel > iMsgLevel:
    strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
    objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
    print(strMsg)
  else:
    if bAbort:
      strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
      objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))

  if bAbort:
    CleanExit("")

def isInt(CheckValue):
  """
  function to safely check if a value can be interpreded as an int
  Parameter:
    Value: A object to be evaluated
  Returns:
    Boolean indicating if the object is an integer or not.
  """
  if isinstance(CheckValue, (float, int, str)):
    try:
      fTemp = int(CheckValue)
    except ValueError:
      fTemp = "NULL"
  else:
    fTemp = "NULL"
  return fTemp != "NULL"

def MakeAPICall(strURL, dictHeader, strMethod, dictPayload="", strUser="", strPWD=""):
  """
  Handles the actual communication with the API, has a backoff mechanism
  MinQuiet defines how many seconds must elapse between each API call.
  Sets a global variable iStatusCode, with the HTTP code returned by the API (200, 404, etc)
  Parameters:
    strURL: Simple String. API EndPoint to call
    dictHeader: Simple string with the header to pass along with the call
    strMethod: Simple string. Call method such as GET, PUT, POST, etc
    Payload: Optional. Any payload to send along in the appropriate structure and format
    User: Optional. Simple string. Username to use in basic Auth
    Password: Simple string. Password to use in basic auth
  Return:
    Returns a tupple of single element dictionary with key of Success,
    plus a list with either error messages or list with either error messages
    or result of the query, list of dictionaries..
    ({"Success":True/False}, [dictReturn])
  """
  global tLastCall
  global iTotalSleep
  global iStatusCode

  fTemp = time.time()
  fDelta = fTemp - tLastCall
  LogEntry("It's been {} seconds since last API call".format(fDelta), 7)
  if fDelta > iMinQuiet:
    tLastCall = time.time()
  else:
    iDelta = int(fDelta)
    iAddWait = iMinQuiet - iDelta
    LogEntry("It has been less than {} seconds since last API call, "
              "waiting {} seconds".format(iMinQuiet, iAddWait), 7)
    iTotalSleep += iAddWait
    time.sleep(iAddWait)

  strErrCode = ""
  strErrText = ""
  dictReturn = {}

  LogEntry("Doing a {} to URL: {}".format(strMethod, strURL), 7)
  try:
    if strMethod.lower() == "get":
      if strUser != "":
        LogEntry(
            "I have none blank credentials so I'm doing basic auth", 7)
        WebRequest = requests.get(strURL, timeout=iTimeOut, headers=dictHeader,
                                  auth=(strUser, strPWD), verify=False, proxies=dictProxies)
      else:
        LogEntry("credentials are blank, proceeding without auth", 7)
        WebRequest = requests.get(
            strURL, timeout=iTimeOut, headers=dictHeader, verify=False, proxies=dictProxies)
      LogEntry("get executed", 7)
    if strMethod.lower() == "post":
      if dictPayload:
        dictTmp = dictPayload.copy()
        if "password" in dictTmp:
            dictTmp["password"] = dictTmp["password"][:2]+"*********"
        LogEntry("with payload of: {}".format(dictTmp), 7)
        WebRequest = requests.post(strURL, json=dictPayload, timeout=iTimeOut,
                                    headers=dictHeader, auth=(strUser, strPWD), verify=False, proxies=dictProxies)
      else:
        WebRequest = requests.post(
            strURL, headers=dictHeader, verify=False, proxies=dictProxies)
      LogEntry("post executed", 7)
  except Exception as err:
    dictReturn["condition"] = "Issue with API call"
    dictReturn["errormsg"] = err
    return ({"Success": False}, [dictReturn])

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry("response is unknown type", 1)
    strErrCode = "ResponseErr"
    strErrText = "response is unknown type"

  LogEntry("call resulted in status code {}".format(
    WebRequest.status_code), 7)
  iStatusCode = int(WebRequest.status_code)

  if iStatusCode != 200:
    strErrCode += str(iStatusCode)
    strErrText += "HTTP Error"
  if strErrCode != "":
    dictReturn["condition"] = "problem with your request"
    dictReturn["errcode"] = strErrCode
    dictReturn["errormsg"] = strErrText
    return ({"Success": False}, [dictReturn])
  else:
    if "<html>" in WebRequest.text[:99]:
      return ({"Success": True}, WebRequest.text)
    try:
      return ({"Success": True}, WebRequest.json())
    except Exception as err:
      dictReturn["condition"] = "failure converting response to jason"
      dictReturn["errormsg"] = err
      dictReturn["errorDetail"] = "Here are the first 199 character of the response: {}".format(
          WebRequest.text[:199])
      return ({"Success": False}, [dictReturn])

def chkdir(strDir):
  if not os.path.exists(strDir):
    try:
      os.makedirs(strDir)
      LogEntry(
          "\nPath '{0}' for ouput files didn't exists, so I create it!\n".format(strDir), 5)
      return True
    except PermissionError:
      LogEntry("unable to create directory {} "
                "permission denied.".format(strDir), 2, True)
      return False
    except FileNotFoundError:
      LogEntry("unable to create directory {}"
                "Issue with the path".format(strDir), 2, True)
      return False
  else:
    return True

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

def GetFileHandle(strFileName, strperm):
  """
  This wraps error handling around standard file open function
  Parameters:
    strFileName: Simple string with filename to be opened
    strperm: single character string, usually w or r to indicate read vs write.
    other options such as "a" and "x" are valid too.
  Returns:
    File Handle object
  """
  dictModes = {}
  dictModes["w"] = "writing"
  dictModes["r"] = "reading"
  dictModes["a"] = "appending"
  dictModes["x"] = "opening"
  dictModes["wb"] = "binary write"

  cMode = strperm[:2].lower().strip()

  try:
    if len(strperm) > 1:
      objFileHndl = open(strFileName, strperm)
    else:
      objFileHndl = open(strFileName, strperm, encoding='utf-8-sig')
    return objFileHndl
  except PermissionError:
    LogEntry("unable to open output file {} for {}, "
          "permission denied.".format(strFileName, dictModes[cMode]))
    return ("Permission denied")
  except FileNotFoundError:
    LogEntry("unable to open output file {} for {}, "
          "Issue with the path".format(strFileName, dictModes[cMode]))
    return ("FileNotFound")
  except Exception as err:
    LogEntry("Unknown error: {}".format(err))
    return ("unknowErr")

def FetchEnv (strEnvName):
  if os.getenv(strEnvName) != "" and os.getenv(strEnvName) is not None:
    return os.getenv(strEnvName)
  else:
    return None

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

def main():
  global objLogOut
  global strScriptName
  global strScriptHost
  global strBaseDir
  global iMinQuiet
  global iTimeOut
  global iLogLevel
  global dictProxies
  global strConf_File

  lstSysArg = sys.argv

  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

  strBaseDir = os.path.dirname(sys.argv[0])
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\", "/")
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
  strLogDir = strBaseDir + "Logs/"
  if strLogDir[-1:] != "/":
    strLogDir += "/"

  chkdir(strLogDir)

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  strVersion = "{0}.{1}.{2}".format(
      sys.version_info[0], sys.version_info[1], sys.version_info[2])
  strScriptHost = platform.node().upper()

  print("This is a script to transfer expense items from Zoho expense to Payday. "
        "This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.strftime("%A %d %B %Y %H:%M:%S %Z")
  print("The time now is {}".format(dtNow))
  print("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile, "w", 1)
  iLoc = lstSysArg[0].rfind(".")
  strDefConf = lstSysArg[0][:iLoc] + ".ini"

  objParser = argparse.ArgumentParser(description="Script to transfer expense items from Zoho expense to Payday")
  objParser.add_argument("-o", "--out", type=str, help="Path to store json output files")
  objParser.add_argument("-i", "--input", type=str, help="Path to Mikrotik input file")
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Verbose output, vv level 2 vvvv level 4")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("-u", "--URL", type=str, help="Comma seperate list of base URLs to check")
  objParser.add_argument("-o", "--out", type=str, help="Path to store json output files")
  objParser.add_argument("-b", "--block", type=str, help="Comma seperate list of URLs not to check, all pages under each URL is ignored")
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Verbose output, vv level 2 vvvv level 4")

  args = objParser.parse_args()
  strConf_File = args.config
  iVerbose = args.verbosity
  LogEntry("conf file set to: {}".format(strConf_File))
  processConf()

  if FetchEnv("NOTIFYCHANNEL") is not None:
    strNotifyChannel = FetchEnv("NOTIFYCHANNEL")
  if strNotifyChannel == "":
      strNotifyChannel = None
  if FetchEnv("NOTIFYTOKEN") is not None:
    strNotifyToken = FetchEnv("NOTIFYTOKEN")
  if strNotifyToken == "":
      strNotifyToken = None
  if FetchEnv("NOTIFYURL") is not None:
    strNotifyURL = FetchEnv("NOTIFYURL")
  if strNotifyURL == "":
      strNotifyURL = None
  if FetchEnv("NOTIFYENABLE") is not None:
    strNotifyEnabled = FetchEnv("NOTIFYENABLE")


  if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None or strNotifyEnabled.lower() != "true":
    bNotifyEnabled = False
    LogEntry("Notify turned off or Missing configuration items for notifications, turning notifications off")
  else:
    bNotifyEnabled = True


  LogEntry("Verbosity: {}".format(args.verbosity))

if __name__ == '__main__':
  main()
