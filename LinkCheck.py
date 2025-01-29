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

def processPage(strURL):
  global dictLinks
  global strBadLinks

  for strBlock in lstBlockedURLs:
    if strBlock in strURL:
      if iVerbose > 0:
        LogEntry("Not processing {} because {} is blocked.".format(strURL,strBlock))
      return []

  bDig = False
  for strMainURL in lstURLs:
    iLen = len(strMainURL)
    if strURL[:iLen] == strMainURL:
      bDig = True


  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"

  lstLinks = []
  if strURL in dictLinks:
    if iVerbose > 2:
      LogEntry("{} has already been processessed".format(strURL))
    return[]
  else:
    WebRequest = GetURL(strURL,dictHeader)
    dictLinks[strURL] = {}
    if WebRequest is None:
      strStatus = "Link failure"
    else:
      strStatus = WebRequest.status_code
    dictLinks[strURL]["dig"] = bDig
    dictLinks[strURL]["code"] = strStatus
    dictSiteMap[strURL]["code"] = strStatus
    dictLinks[strURL]["src"] = dictSiteMap[strURL]["src"]
    if strStatus != 200:
      LogEntry("URL:{} Status:{}".format(strURL,strStatus))
      strBadLinks += "Link {} on {} returned status {}\n".format(strURL,dictSiteMap[strURL]["src"],strStatus)
  if not bDig:
    if iVerbose > 1:
      LogEntry("{} is not one of our links, not digging deeper".format(strURL))
    return []
  else:
    if iVerbose > 1:
      LogEntry("{} is one of our links, parsing for links".format(strURL))

  if WebRequest is None or WebRequest.status_code != 200:
    strHTML = ""
    LogEntry("Setting HTML string to an empty string")
  else:
    strHTML = WebRequest.text

  objSoup = BeautifulSoup(strHTML,features="html.parser")
  if iVerbose > 3:
    LogEntry("Fetched URL and parsed into a beautiful Soup, response length is {}".format(len(strHTML)))
  for objLink in objSoup.findAll("a"):
    strTemp = objLink.get("href")
    if strTemp is not None and strTemp[:4].lower() == "http":
      if strTemp not in dictSiteMap: # dictLinks and strTemp not in lstLinks and strTemp not in lstNewLinks:
        if strTemp[-4:] == ".jpg" or strTemp[-4:] == ".png" or strTemp[-5:] == ".webp":
          continue
        lstLinks.append(strTemp)
        dictSiteMap[strTemp] = {}
        dictSiteMap[strTemp]["src"] = strURL
        if iVerbose > 2:
          LogEntry("{} added to the list".format(strTemp))
      else:
        if iVerbose > 3:
          LogEntry("Already seen {}".format(strTemp))
    else:
      if iVerbose > 3:
        LogEntry("{} is not a valid link".format(strTemp))
  return lstLinks

def FetchLinks(lstLinks,strURL):
  lstNewLinks = []

  if iVerbose > 1:
    LogEntry("Got {} links. Digging into them".format(len(lstLinks)))
  for strLink in lstLinks:
    lstTemp = processPage(strLink)
    lstNewLinks.extend(lstTemp)
    if iVerbose > 1:
      LogEntry("Found {} new links".format(len(lstTemp)))
  iListLen = len(lstNewLinks)
  if iVerbose > 1:
    LogEntry("Found {} new and unseen links".format(len(lstNewLinks)))
  if iListLen > 0:
    FetchLinks(lstNewLinks,strURL)

def main():
  global strConf_File
  global objLogOut
  global strScriptName
  global strScriptHost
  global strSaveFolder
  global iTimeOut
  global iVerbose
  global dictLinks
  global strGetURL
  global lstNewLinks
  global dictSiteMap
  global strBadLinks
  global lstBlockedURLs
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global strNotifyEnabled
  global bNotifyEnabled
  global bQuiet
  global lstURLs
  global strBlockedURLs

  strBadLinks = ""
  bNotifyEnabled = False
  strBlockedURLs = ""

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

  strScriptName = os.path.basename(lstSysArg[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + "/" + strScriptName[:iLoc] + ISO + ".log"
  iLoc = lstSysArg[0].rfind(".")
  strDefConf = lstSysArg[0][:iLoc] + ".ini"

  objParser = argparse.ArgumentParser(description="Script to crawl a set of URLs, looking for links. Validates they're 200 OK")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("-u", "--URL", type=str, help="Comma seperate list of base URLs to check")
  objParser.add_argument("-o", "--out", type=str, help="Path to store json output files")
  objParser.add_argument("-b", "--block", type=str, help="Comma seperate list of URLs not to check, all pages under each URL is ignored")
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
    print ("This script crawls specified URLs and tests all links found."
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


  LogEntry("Verbosity: {}".format(args.verbosity))

  if args.block is not None:
    strBlockedURLs = args.block
  lstBlockedURLs = strBlockedURLs.split(",")
  if iVerbose > 3:
    if len(lstBlockedURLs) == 0 or lstBlockedURLs[0] == "":
      LogEntry("No Blocklist")
    else:
      LogEntry("Not checking the following due to blocklist: {}".format(lstBlockedURLs))

  if args.out is not None:
    strSaveFolder = args.out
  if strSaveFolder == "":
    strSaveFolder = strBaseDir + "Data"
  else:
    strSaveFolder = strSaveFolder.replace("\\","/")
    if strSaveFolder[-1:] != "/":
      strSaveFolder += "/"
  LogEntry("Save Folder set to {}".format(strSaveFolder))
  if not os.path.exists (strSaveFolder) :
    os.makedirs(strSaveFolder)
    LogEntry ("\nPath '{0}' for data files didn't exists, so I create it!\n".format(strSaveFolder))

  if args.URL is not None:
    strGetURL = args.URL
  if iVerbose > 1:
    LogEntry("GetURL: {}".format(strGetURL))
  if strGetURL is None or strGetURL[:4].lower() != "http":
    LogEntry("No valid URL, can't continue",True)

  dictLinks = {}
  dictSiteMap = {}

  lstURLs = strGetURL.split(",")
  if iVerbose > 2:
    LogEntry("lstURL: {}".format(lstURLs))

  for strURL in lstURLs:
    dictSiteMap[strURL] = {}
    dictSiteMap[strURL]["src"] = "root"
    try:
      del dictLinks[strURL]
      if iVerbose > 2:
        LogEntry("item deleted from dictlinks")
    except:
      if iVerbose > 2:
        LogEntry("item not in dictlinks")

    if iVerbose > 2:
      LogEntry("Starting to work on {}".format(strURL))
    lstLinks = processPage(strURL)
    FetchLinks(lstLinks,strURL)

  strSiteMap = strSaveFolder + "SiteMap.json"
  strLinksOut = strSaveFolder + "AllLinks.json"
  with open(strSiteMap, "w") as outfile:
      json.dump(dictSiteMap, outfile)
  with open(strLinksOut, "w") as outfile:
      json.dump(dictLinks, outfile)
  if bNotifyEnabled:
    SendNotification("{} on {}: Bad Links:\n{}".format(strScriptName,strScriptHost,strBadLinks))
  else:
    LogEntry("{} on {}: Bad Links:\n{}".format(strScriptName,strScriptHost,strBadLinks))
  LogEntry("Done!!")


if __name__ == '__main__':
  main()
