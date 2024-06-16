'''
Wordpress Export Script
Author Siggi Bjarnason Copyright 2020
Website https://supergeek.us

Description:
This script will read an Wordpress export XML file, download all attachments and write all posts and pages to their own files.

Following packages need to be installed as administrator
pip install xmltodict

'''
# Import libraries
import sys
import os
import string
import time
import requests
import xmltodict
import urllib.parse as urlparse
import subprocess as proc
import xml.parsers.expat
import platform
try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print ("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

# End imports

#avoid insecure warning
requests.urllib3.disable_warnings()

#Define and initialize
lstHTMLElements = ["</a>", "</p>", "</ol>",
                   "</li>", "</ul>", "</span>", "</div>"]

lstBadChar = ["?", "!", "'", '"', "~", "#", "%", "&", "*", ":", "<", ">", "?", "/", "\\", 
              "{", " | ", "}", "$", "!", "@", "+", "=", "`"]

def CleanFileName(strClean):
  if strClean is None:
    return ""

  for cBad in lstBadChar:
    strClean = strClean.replace(cBad, "")
  
  strClean = strClean.replace(".","-")
  strClean = strClean.strip()
  return strClean


def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    print ("please upgrade to python 3")
    sys.exit(5)

def IsHTML(strCheck):
  if strCheck is None:
    return False
  for strHTMLElement in lstHTMLElements:
    if strHTMLElement in strCheck:
      return True
  return False

def FetchFile (strURL):
  try:
    WebRequest = requests.get(strURL, headers={}, verify=False)
  except Exception as err:
    LogEntry ("Issue with API call. {}".format(err))
    return None

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry ("response is unknown type")
    return None
  
  return WebRequest.content

def LogEntry(strMsg):
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
	print(strMsg)

ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

strBaseDir = os.path.dirname(sys.argv[0])
strBaseDir = strBaseDir.replace("\\", "/")
strRealPath = os.path.realpath(sys.argv[0])
strRealPath = strRealPath.replace("\\","/")
if strBaseDir == "":
  iLoc = strRealPath.rfind("/")
  strBaseDir = strRealPath[:iLoc]
if strBaseDir[-1:] != "/":
  strBaseDir += "/"
strLogDir  = strBaseDir + "Logs/"
if strLogDir[-1:] != "/":
  strLogDir += "/"

iLoc = sys.argv[0].rfind(".")

if not os.path.exists (strLogDir) :
  os.makedirs(strLogDir)
  print ("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

strScriptName = os.path.basename(sys.argv[0])
iLoc = strScriptName.rfind(".")
strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
objLogOut = open(strLogFile, "w", 1)

strFilein = ""
dictMissing = {}
sa = sys.argv
lsa = len(sys.argv)
if lsa > 1:
  strFilein = sa[1]

if strFilein == "":
  if btKinterOK:
    print ("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
    root = tk.Tk()
    root.withdraw()
    strFilein = filedialog.askopenfilename (title = "Select the WP Export file",filetypes = (("XML files","*.xml"),("all files","*.*")))
  else:
    strFilein = getInput("Please provide full path and filename for the WP Export file to be processed: ")

if strFilein == "":
  print ("No filename provided unable to continue")
  sys.exit(9)

if os.path.isfile(strFilein):
  print ("OK found {}".format(strFilein))
else:
  print ("Can't find WP export file {}".format(strFilein))
  sys.exit(4)


iLoc = strFilein.rfind(".")
strFileExt = strFilein[iLoc+1:]
iLoc = strFilein.find(".")
strOutPath = strFilein[:iLoc]
if strOutPath[-1:] != "/":
	strOutPath += "/"

if not os.path.exists(strOutPath):
  os.makedirs(strOutPath)
  LogEntry("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(
      strOutPath))
else:
  LogEntry ("Path {} is OK".format(strOutPath))

if strFileExt.lower() == "xml":
  objFileIn = open(strFilein, "r", encoding='utf-8')
else:
  LogEntry ("only able to process XML files. Unable to process {} files".format(strFileExt))
  sys.exit(5)


strXML = objFileIn.read()
try:
    dictInput = xmltodict.parse(strXML)
except xml.parsers.expat.ExpatError as err:
    LogEntry ("Expat Error: {}\n{}".format(err,strXML))
    iErrCode = "Expat Error"
    iErrText = "Expat Error: {}\n{}".format(err,strXML)

LogEntry ("File read in, here are top level keys {}".format(dictInput.keys()))
if "rss" in dictInput:
  if "channel" in dictInput["rss"]:
    if "item" in dictInput["rss"]["channel"]:
      if isinstance (dictInput["rss"]["channel"]["item"],list):
        # LogEntry("Here are the keys in first item entry: {}".format(
        #     dictInput["rss"]["channel"]["item"][0].keys()))
        for dictItem in dictInput["rss"]["channel"]["item"]:
          strPostType = dictItem["wp:post_type"]
          strPostTitle = dictItem["title"]
          strContent = dictItem["content:encoded"]
          if strPostTitle is None:
            strPostTitle = "None"
          else:
            strPostTitle = CleanFileName (strPostTitle)
          if strPostType[:4] == "post" or strPostType == "page":
            strItemPath = strOutPath + strPostType
            if strItemPath[-1:] != "/":
              strItemPath += "/"
            if not os.path.exists(strItemPath):
              os.makedirs(strItemPath)
              LogEntry("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(
                  strItemPath))
            if IsHTML(strContent):
              strFileOut = strItemPath + strPostTitle + ".html"
              strContent = "<h1>{}</h1>\n<h2>{} by {}. Posted on {} GMT</h2>\n{}".format(
                  dictItem["title"], strPostType[0].upper()+strPostType[1:], dictItem["dc:creator"], 
                  dictItem["wp:post_date_gmt"], strContent)
            else:
              strFileOut = strItemPath + strPostTitle + ".txt"
              strContent = "{}\n{} by {}. Posted on {} GMT\n{}".format(
                  dictItem["title"], strPostType[0].upper()+strPostType[1:], dictItem["dc:creator"],
                  dictItem["wp:post_date_gmt"], strContent)
            objFileOut = open(strFileOut,"w",1)
            try:
              objFileOut.write(strContent)
            except Exception as err:
              LogEntry ("Error while write to file {}. {}".format(strFileOut,err))
            
            objFileOut.close()
          elif strPostType == "attachment":
            strItemPath = strOutPath + strPostType
            if strItemPath[-1:] != "/":
              strItemPath += "/"
            if not os.path.exists(strItemPath):
              os.makedirs(strItemPath)
              LogEntry("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(
                  strItemPath))
            strURL = dictItem["wp:attachment_url"]
            iLoc = strURL.rfind("/")+1
            strFileOut = strItemPath + strURL[iLoc:]
            LogEntry ("Fetching URL: {}".format(strURL))
            strContent = FetchFile(strURL)
            if strContent is not None:
              LogEntry ("Saving attachment to {}".format(strFileOut))
              objFileOut = open(strFileOut, "wb", 1)
              objFileOut.write(strContent)
              objFileOut.close()
          else:
            if strPostType not in dictMissing:
              dictMissing[strPostType] = dictItem.keys()

          LogEntry("{} | {} | {} ".format(
              dictItem["title"], strPostType, dictItem["dc:creator"]))
      else:
        LogEntry("item is not a list, it is a {}".format(
            type(dictInput["rss"]["channel"]["item"])))
    else:
      LogEntry ("No Item list")
  else:
    LogEntry ("No channel item")
else:
  LogEntry ("No rss feed")

LogEntry ("Done! Was missing ways to handle these types:")
for strKey in dictMissing.keys():
  LogEntry ("{}: {}".format(strKey,",".join(dictMissing[strKey])))
