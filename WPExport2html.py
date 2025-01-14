'''
Wordpress Export Script
Author Siggi Bjarnason Copyright 2020
Website https://supergeek.us

Description:
This script will read an Wordpress export XML file, download all attachments and write all posts and pages to their own files.

Following packages need to be installed as administrator
pip install xmltodict

Also make sure you have pandoc installed, here is a good way on windows
winget install --source winget --exact --id JohnMacFarlane.Pandoc

Or grab your correct install from https://github.com/jgm/pandoc/releases/latest

'''
# Import libraries
import sys
import os
import time
import urllib.parse as urlparse
import subprocess
import xml.parsers.expat
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
finally:
    import requests

try:
    import xmltodict
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'xmltodict'])
finally:
    import xmltodict

try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

# End imports

#avoid insecure warning
requests.urllib3.disable_warnings()

#Define and initialize
lstHTMLElements = ["</a>", "</p>", "</ol>",
                   "</li>", "</ul>", "</span>", "</div>"]

lstBadChar = ["?", "!", "'", '"', "~", "#", "%", "&", "*", ":", "<", ">", "?", "/", "\\",
              "{", " | ", "}", "$", "!", "@", "+", "=", "`"]

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
          objFileHndl = open(strFileName, strperm, encoding='utf8')
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

def CleanFileName(strClean):
  if strClean is None:
    return ""

  for cBad in lstBadChar:
    strClean = strClean.replace(cBad, "")

  strClean = strClean.replace(".","-")
  strClean = strClean.strip()
  strClean = strClean[:50]
  return strClean

def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    print("please upgrade to python 3")
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
    LogEntry("Issue with API call. {}".format(err))
    return None

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry("response is unknown type")
    return None

  return WebRequest.content

def LogEntry(strMsg):
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
	print(strMsg)

def Convert2doc(strPath):
  lstDirectory = os.listdir(strPath)
  print("\n\n Converting html files in {} to docx via pandoc \n".format(strPath))
  for strFileName in lstDirectory:
    if strFileName.endswith(".html"):
      strCmd = 'pandoc "' + strPath + strFileName + '" -o "' + strPath + os.path.splitext(strFileName)[0] + '.docx"'
      try:
        subprocess.call(strCmd)
      except Exception as err:
        LogEntry("Failure during Conver2Doc: {}".format(err))

def main():
  global objLogOut

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
    print("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  objLogOut = GetFileHandle(strLogFile, "w")

  strFilein = ""
  dictMissing = {}
  sa = sys.argv
  lsa = len(sys.argv)
  if lsa > 1:
    strFilein = sa[1]

  if strFilein == "":
    if btKinterOK:
      print("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
      root = tk.Tk()
      root.withdraw()
      strFilein = filedialog.askopenfilename (title = "Select the WP Export file",filetypes = (("XML files","*.xml"),("all files","*.*")))
    else:
      strFilein = getInput("Please provide full path and filename for the WP Export file to be processed: ")

  if strFilein == "":
    print("No filename provided unable to continue")
    sys.exit(9)

  if os.path.isfile(strFilein):
    print("OK found {}".format(strFilein))
  else:
    print("Can't find WP export file {}".format(strFilein))
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
    LogEntry("Path {} is OK".format(strOutPath))

  if strFileExt.lower() == "xml":
    objFileIn = GetFileHandle (strFilein, "r")
  else:
    LogEntry("only able to process XML files. Unable to process {} files".format(strFileExt))
    sys.exit(5)


  strXML = objFileIn.read()
  objFileIn.close()
  try:
      dictInput = xmltodict.parse(strXML)
  except xml.parsers.expat.ExpatError as err:
      dictInput={}
      LogEntry("Expat Error: {}\n{}".format(err,strXML[:99]))

  LogEntry("File read in, here are top level keys {}".format(dictInput.keys()))
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
              objFileOut = GetFileHandle(strFileOut,"w")
              if not isinstance(objFileOut,str):
                try:
                  objFileOut.write(strContent)
                except Exception as err:
                  LogEntry("Error while write to file {}. {}".format(strFileOut,err))
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
              LogEntry("Fetching URL: {}".format(strURL))
              strContent = FetchFile(strURL)
              if strContent is not None:
                LogEntry("Saving attachment to {}".format(strFileOut))
                objFileOut = GetFileHandle(strFileOut, "wb")
                if not isinstance(objFileOut,str):
                  try:
                    objFileOut.write(strContent)
                  except Exception as err:
                    LogEntry("Error while write to file {}. {}".format(strFileOut,err))
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
        LogEntry("No Item list")
    else:
      LogEntry("No channel item")
  else:
    LogEntry("No rss feed")

  #LogEntry("Done! Was missing ways to handle these types:")
  #for strKey in dictMissing.keys():
  #  LogEntry("{}: {}".format(strKey,",".join(dictMissing[strKey])))

  if os.path.exists(strOutPath + "page/"):
    Convert2doc(strOutPath + "page/")
  if os.path.exists(strOutPath + "post/"):
    Convert2doc(strOutPath + "post/")

  LogEntry("Done!")
  objLogOut.close()
  print("Log closed")

if __name__ == '__main__':
    main()