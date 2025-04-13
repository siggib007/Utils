'''
Aurdel Export Script
Author Siggi Bjarnason Copyright 2025
Website https://supergeek.us

Description:
This script will call the Audrel API to fetch the details of a particular part number

Following packages need to be installed as administrator
pip install xmltodict
pip install requests

'''
# Import libraries
import sys
import os
import time
import urllib.parse as urlparse
import subprocess
import argparse
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

strBaseURL = "https://api.aurdel.com/Prices/getPrice"

def FetchEnv (strEnvName):
  if os.getenv(strEnvName) != "" and os.getenv(strEnvName) is not None:
    return os.getenv(strEnvName)
  else:
    return None

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

def CleanString(strClean):
  if strClean is None:
    return ""

  for cBad in lstBadChar:
    strClean = strClean.replace(cBad, "")

  strClean = strClean.replace(".","-")
  strClean = strClean.strip()
  if len(strClean) > 50:
    strClean = strClean[:50] + strClean[-4:]
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

def FetchXML (strItemID):
  dictParams = {}
  dictParams["database"] = "item"
  dictParams["customerid"] = strCustID
  dictParams["companyid"] = strCompID
  dictParams["apikey"]  = strAPIKey
  dictParams["itemid"] = strItemID
  strParams = urlparse.urlencode(dictParams)
  strURL = strBaseURL + "?" + strParams

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

def processConf():
  global strCustID
  global strCompID
  global strAPIKey
  global strSaveFolder

  strCustID = None
  strCompID = None
  strAPIKey = None
  strSaveFolder = ""

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
      if strVarName == "CustomerID":
        strCustID = strValue
      if strVarName == "CompanyID":
        strCompID = strValue
      if strVarName == "APIKey":
        strAPIKey = strValue
      if strVarName == "SaveFolder":
        strSaveFolder = strValue

  LogEntry ("Done processing configuration, moving on")

def main():
  global objLogOut
  global strCustID
  global strCompID
  global strAPIKey
  global strConf_File
  global strSaveFolder

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

  iLoc = sys.argv[0].rfind(".")
  strDefConf = sys.argv[0][:iLoc] + ".ini"
  objParser = argparse.ArgumentParser(description="Script to fetch details on particulat part number")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("-o", "--out", type=str, help="Path to store json output files")
  objParser.add_argument("-i", "--input", type=str, help="List of part numbers to process")
  args = objParser.parse_args()
  strConf_File = args.config
  LogEntry("conf file set to: {}".format(strConf_File))
  processConf()

  if FetchEnv("CUSTOMERID") is not None:
    strCustID = FetchEnv("CUSTOMERID")
  if strCustID == "":
      strCustID = None
  if FetchEnv("COMPANYID") is not None:
    strCompID = FetchEnv("COMPANYID")
  if strCompID == "":
      strCompID = None
  if FetchEnv("APIKEY") is not None:
    strAPIKey = FetchEnv("APIKEY")
  if strAPIKey == "":
      strAPIKey = None

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

  if strCustID is None or strCompID is None or strAPIKey is None:
    LogEntry("Unable to continue, missing customerid, companyid or apikey")
    objLogOut.close()
    sys.exit(1)

  if args.input is None:
     strInput = getInput("Please enter part number to process: ")
  else:
      strInput = args.input.strip()

  strXML = FetchXML(strInput)
  try:
    dictInput = xmltodict.parse(strXML)
  except xml.parsers.expat.ExpatError as err:
    dictInput={}
    LogEntry("Expat Error: {}\n{}".format(err,strXML[:99]))
    objLogOut.close()
    sys.exit(1)

  #LogEntry("File read in, here are top level keys {}".format(dictInput.keys()))

  if "Error" in dictInput.keys():
    LogEntry("Error {} in response:{}\n{}".format(dictInput["Error"]["Code"],dictInput["Error"]["Info"],dictInput["Error"]["Details"]))
    objLogOut.close()
    sys.exit(1)

  dictItems = dictInput["database"]["DELTACO.SE"]["data"]["items"]["item"]
  #LogEntry("File read in, here are top level keys {}".format(dictItems.keys()))
  print("MFG:{} MPN:{} EAN:{}".format(dictItems["manufacturer"]["description"], dictItems["manufacturer"]["@id"], dictItems["ean"]))
  print("Short:{}".format(dictItems["description"]["short"]))
  print("Long:{}".format(dictItems["description"]["long"]))
  print("Price:{} {}".format(dictItems["price"]["net"],dictItems["price"]["@currencycode"]))
  print("Stock:{}".format(dictItems["stock"]["@quantity"]))
  print("Pieces Per Carton:{}".format(dictItems["piecespercarton"]))
  print("Categories:{}".format(",".join(dictItems["categories"]["category"]["subcategory"])))


  LogEntry("Done!")
  objLogOut.close()
  print("Log closed")


if __name__ == '__main__':
    main()