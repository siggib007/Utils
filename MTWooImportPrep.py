'''
Script that reads in a csv with MikroTik products and prepares them for import into WooCommerce
Fetches additional data from include URL

Author Siggi Bjarnason Copyright 2025
Website http://supergeek.us

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
import csv
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

try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print("Failed to load tkinter, CLI only mode.")
  btKinterOK = False
# End imports

iTimeOut = 120

def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    print("please upgrade to python 3")
    sys.exit(5)

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
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = "Bearer " + strNotifyToken

  strNotifyURL = strNotifyURL

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

def GetURL(strURL):
  WebRequest = None
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"

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

def GetImgURLs(strURL):
  strRet = ""
  WebRequest = GetURL(strURL, timeout=iTimeOut)
  if iVerbose > 1:
    LogEntry ("call resulted in status code {}".format(WebRequest.status_code))
  strHTML = WebRequest.text
  objSoup = BeautifulSoup(strHTML,features="html5lib")
  if iVerbose > 1:
    LogEntry("Fetched URL and parsed into a beautiful Soup, response length is {}".format(len(strHTML)))
  for objLink in objSoup.findAll("img"):
    strImg = objLink.get("src")
    if strImg[:4] == "http":
      strRet += strImg + "\n"
      if iVerbose > 2:
        LogEntry("Found an image: {}".format(strImg))
  return strRet

def main():
  global strConf_File
  global objLogOut
  global strScriptName
  global strScriptHost
  global strSaveFolder
  global iVerbose
  global dictLinks
  global strGetURL
  global lstNewLinks
  global dictSiteMap
  global lstBlockedURLs
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global strNotifyEnabled
  global bNotifyEnabled
  global bQuiet
  global lstURLs

  bNotifyEnabled = False


  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
  csvDelim = ","

  lstSysArg = sys.argv

  strRealPath = os.path.realpath(lstSysArg[0])
  strBaseDir = os.path.dirname(lstSysArg[0])
  if strBaseDir != "":
    if strBaseDir[-1:] != "/":
      strBaseDir += "/"
  strLogDir  = strBaseDir + "Logs"
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])

  strScriptName = os.path.basename(lstSysArg[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + "/" + strScriptName[:iLoc] + ISO + ".log"
  iLoc = lstSysArg[0].rfind(".")
  strDefConf = lstSysArg[0][:iLoc] + ".ini"

  objParser = argparse.ArgumentParser(description="Script to create WooCommerce import files from MikroTik product pages")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("-o", "--out", type=str, help="Path to store json output files")
  objParser.add_argument("-i", "--input", type=str, help="Path to Mikrotik input file")
  objParser.add_argument("-q", "--quiet", action="store_true", help="Suppress output to screeen regardless of verbosity, only log to file")
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Verbose output, vv level 2 vvvv level 4")
  args = objParser.parse_args()
  bQuiet = args.quiet

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    if not bQuiet:
      print ("\nPath '{0}' for log file didn't exists, so I create it!\n".format(strLogDir))

  strScriptHost = platform.node().upper()
  if not bQuiet:
    print ("This script prepares an import script for Woocommerce for MikroTik Products."
    "\nThis is running under Python Version {}".format(strVersion))
    print ("Running from: {}".format(strRealPath))
    now = time.asctime()
    print ("The time now is {}".format(now))
    print ("Logs saved to {}".format(strLogFile))

  objLogOut = open(strLogFile,"w", encoding='utf8')

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

  LogEntry("Verbosity: {}".format(iVerbose))

  if args.input is None:
    strFilein = ""
  else:
    strFilein = args.input

  if strFilein == "":
    if btKinterOK:
      print("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
      root = tk.Tk()
      root.withdraw()
      strFilein = filedialog.askopenfilename (title = "Select the WP Export file",filetypes = (("CSV files","*.csv"),("all files","*.*")))
    else:
      strFilein = getInput("Please provide full path and filename for the MikroTik product file to be processed: ")
  if strFilein == "":
    print("No filename provided unable to continue")
    sys.exit(9)

  if os.path.isfile(strFilein):
    print("OK found {}".format(strFilein))
  else:
    print("Can't find MikroTik product file {}".format(strFilein))
    sys.exit(4)
  iLoc = strFilein.rfind(".")
  strFileExt = strFilein[iLoc+1:]
  strInDir = os.path.dirname(strFilein)

  if args.out is not None:
    strSaveFolder = args.out
  if strSaveFolder == "":
    strSaveFolder = strInDir
  else:
    strSaveFolder = strSaveFolder.replace("\\","/")
    if strSaveFolder[-1:] != "/":
      strSaveFolder += "/"
  LogEntry("Save Folder set to {}".format(strSaveFolder))
  if not os.path.exists (strSaveFolder) :
    os.makedirs(strSaveFolder)
    LogEntry ("\nPath '{0}' for data files didn't exists, so I create it!\n".format(strSaveFolder))

  if strFileExt.lower() == "csv":
    objFileIn = GetFileHandle (strFilein, "r")
  else:
    LogEntry("only able to process csv files. Unable to process {} files".format(strFileExt))
    sys.exit(5)

  objReader = csv.DictReader(objFileIn, delimiter=csvDelim)
  for dictTemp in objReader:
      LogEntry("Working on {} - {} - {} - {}".format(
          dictTemp["Product code"], dictTemp["Product name"], dictTemp["Product Line"],dictTemp["URL"]))


if __name__ == '__main__':
  main()
