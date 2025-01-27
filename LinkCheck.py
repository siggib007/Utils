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
  global bNotifyEnabled

  strNotifyURL = None
  strNotifyToken = None
  strNotifyChannel = None
  bNotifyEnabled = False
  strSaveFolder = None
  strGetURL = None

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

  if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None or strNotifyEnabled.lower() != "true":
    bNotifyEnabled = False
    LogEntry("Notify turned off or Missing configuration items for notifications, turning notifications off")
  else:
    bNotifyEnabled = True

  LogEntry ("Done processing configuration, moving on")

def processPage(strURL,strMainURL):
  global dictLinks
  global strBadLinks

  iLen = len(strMainURL)
  if strURL[:iLen] == strMainURL:
    bDig = True
  else:
    bDig = False

  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"

  lstLinks = []
  if strURL in dictLinks:
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
      strBadLinks += "Link {} on {} returned status {}".format(strURL,dictSiteMap[strURL]["src"],strStatus)
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
      if strTemp not in dictLinks and strTemp not in lstLinks and strTemp not in lstNewLinks:
        if strTemp[-4:] == ".jpg" or strTemp[-4:] == ".png":
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

  strBadLinks = ""

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
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Verbose output, vv level 2 vvvv level 4")
  args = objParser.parse_args()

  strConf_File = args.config
  iVerbose = args.verbosity
  LogEntry("conf file set to: {}".format(strConf_File))
  processConf()

  LogEntry("Verbosity: {}".format(args.verbosity))

  if strSaveFolder == "":
    strSaveFolder = strBaseDir + "Data"
  else:
    strSaveFolder = strSaveFolder.replace("\\","/")
    if strSaveFolder[-1:] != "/":
      strSaveFolder += "/"
  LogEntry("Save Folder set to {}".format(strSaveFolder))
  if not os.path.exists (strSaveFolder) :
    os.makedirs(strSaveFolder)
    print ("\nPath '{0}' for data files didn't exists, so I create it!\n".format(strSaveFolder))

  if args.URL is not None:
    strGetURL = args.URL

  if strGetURL is None or strGetURL[:4].lower() != "http":
    LogEntry("No valid URL, can't continue",True)

  dictLinks = {}
  dictSiteMap = {}
  lstNewLinks = []
  lstNewLinks2 = []
  lstNewLinks3 = []

  lstURLs = strGetURL.split(";")
  for strURL in lstURLs:
    dictSiteMap[strURL] = {}
    dictSiteMap[strURL]["src"] = "root"

    lstLinks = processPage(strURL,strURL)
    if iVerbose > 0:
      LogEntry("Found {} links. Digging into them".format(len(lstLinks)))
    for strLink in lstLinks:
      lstTemp = processPage(strLink,strURL)
      lstNewLinks.extend(lstTemp)
      if iVerbose > 0:
        LogEntry("Found {} new links".format(len(lstTemp)))
    if iVerbose > 0:
      LogEntry("Working on New list")
    for strLink in lstNewLinks:
      if iVerbose > 1:
        LogEntry("Working on {}".format(strLink))
      lstTemp = processPage(strLink,strURL)
      lstNewLinks2.extend(lstTemp)
      if iVerbose > 0:
        LogEntry("Found {} new links while on new list".format(len(lstTemp)))
    LogEntry("There are {} links left on list 2".format(len(lstNewLinks)))
    for strLink in lstNewLinks2:
      if iVerbose > 1:
        LogEntry("List2, Working on {}".format(strLink))
      lstTemp = processPage(strLink,strURL)
      lstNewLinks3.extend(lstTemp)
      if iVerbose > 0:
        LogEntry("Found {} new links while on new list2".format(len(lstTemp)))
    LogEntry("There are {} links left on list 3".format(len(lstNewLinks3)))

  strSiteMap = strSaveFolder + "SiteMap.json"
  strLinksOut = strSaveFolder + "AllLinks.json"
  with open(strSiteMap, "w") as outfile:
      json.dump(dictSiteMap, outfile)
  with open(strLinksOut, "w") as outfile:
      json.dump(dictLinks, outfile)
  LogEntry("Bad Links:\n{}".format(strBadLinks))
  LogEntry("Done!!")


if __name__ == '__main__':
  main()
