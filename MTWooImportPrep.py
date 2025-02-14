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
import re
import time
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

def Convert2Int(strInt):
    match = re.search(r'\d+', strInt)
    if match:
        return int(match.group())
    return None

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

def LogEntry(strMsg):

  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  if not bQuiet:
    print (strMsg)

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

def StripPrice(strCheck):
  strPattern = r"<p>\$\d+\.*\d*</p>"
  strReplace = ""
  strTemp = re.sub(strPattern,strReplace,strCheck)
  strPattern = r"<tr>\s*<td>Suggested price</td>\s*<td>\$\d+\.\d*</td>\s*</tr>"
  strTemp = re.sub(strPattern,strReplace,strTemp)
  return strTemp.strip()

def GetProductDetails(strURL):
  strRet = ""
  dictRet = {}
  WebRequest = GetURL(strURL)
  if WebRequest is None:
    return {"Images":"","Details":""}
  if iVerbose > 1:
    LogEntry ("call resulted in status code {}".format(WebRequest.status_code))
  if WebRequest.status_code != 200:
    return {"Images":"","Details":""}
  strHTML = WebRequest.text
  objSoup = BeautifulSoup(strHTML,features="html5lib")
  if iVerbose > 1:
    LogEntry("Fetched URL and parsed into a beautiful Soup, response length is {}".format(len(strHTML)))
  for objLink in objSoup.findAll("a"):
    strImg = objLink.get("href")
    if strImg is not None and strImg[:4] == "http" and strImg[-10:] == "hi_res.png":
      strRet += strImg + ","
      if iVerbose > 2:
        LogEntry("Found an image: {}".format(strImg))
  dictRet["Images"] = strRet
  strRet = ""
  for objDiv in objSoup.findAll("div"):
    objClass = objDiv.get("class")
    if objClass is not None and "product-page" in objClass:
      if iVerbose > 2:
        LogEntry("Found a div, class: {}".format(objClass))
      for objP in objDiv.findAll("p"):
        strTemp = str(objP)
        strRet += StripPrice(strTemp) + "\n"
  for objSpec in objSoup.find_all(id="specifications"):
    for objChild in objSpec.children:
      strTemp = str(objChild)
      if strTemp[0] == "<":
        strRet += StripPrice(strTemp) + "\n"
  dictRet["Details"] = StripPrice(strRet)
  return dictRet

def main():
  global objLogOut
  global strScriptName
  global strScriptHost
  global iVerbose
  global bQuiet

  strSaveFolder = ""

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

  iVerbose = args.verbosity

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

  dictOut = {}
  lstOut = []
  objReader = csv.DictReader(objFileIn, delimiter=csvDelim)
  for dictTemp in objReader:
    LogEntry("Working on {} - {} - {} - {}".format(
        dictTemp["Product code"], dictTemp["Product name"], dictTemp["Product Line"],dictTemp["URL"]))
    lstDimensions = dictTemp["Dimensions"].split("x")
    dictRet = GetProductDetails(dictTemp["URL"])
    dictOut["Type"] = "simple"
    dictOut["SKU"] = dictTemp["Product code"]
    dictOut["Name"] = dictTemp["Product name"]
    dictOut["Published"] = "1"
    dictOut["Is Featured?"] = "0"
    dictOut["Visibility in catalog"] = "visible"
    dictOut["Short Description"] = dictTemp["Description"]
    dictOut["Description"] = dictRet["Details"]
    dictOut["Tax status"] = "taxable"
    dictOut["In stock?"] = "backorder"
    dictOut["Stock"] = "0"
    dictOut["Backorders allowed?"] = "notify"
    dictOut["Sold individually?"] = "0"
    dictOut["Weight (kg)"] = ""
    iTemp = Convert2Int(lstDimensions[0])
    if iTemp is None:
      iTemp = ""
    else:
      iTemp = iTemp/10
    dictOut["Length (cm)"] = iTemp
    if len(lstDimensions) > 1:
      iTemp = Convert2Int(lstDimensions[1])
      if iTemp is None:
        iTemp = ""
      else:
        iTemp = iTemp/10
      dictOut["Width (cm)"] = iTemp
    else:
      dictOut["Width (cm)"] = ""
    if len(lstDimensions) > 2:
      iTemp = Convert2Int(lstDimensions[2])
      if iTemp is None:
        iTemp = ""
      else:
        iTemp = iTemp/10
      dictOut["Height (cm)"] = iTemp
    else:
      dictOut["Height (cm)"] = ""
    dictOut["Regular price"] = int(float(dictTemp["MSRP ISK"]) * 1.25)
    dictOut["Categories"] = dictTemp["Product Line"] + "," + dictTemp["Product Category"]
    dictOut["Tags"] = "networking"
    dictOut["Images"] = dictRet["Images"]
    dictOut["External URL"] = dictTemp["URL"]
    dictOut["Brands"] = "MikroTik"
    dictOut["MPN"] = dictTemp["Product code"]
    dictOut["Meta: _yoast_wpseo_focuskw"] = dictTemp["Product code"]
    dictOut["Meta: _yoast_wpseo_metadesc"] = dictTemp["Product code"] + dictTemp["Description"][:120]
    iAttrCount = 1
    if dictTemp["Dimensions"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Dimensions"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Dimensions"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Ingress Protection"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Ingress Protection"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Ingress Protection"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Wi-Fi Gen"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Wi-Fi Gen"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Wi-Fi Gen"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Architecture"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Architecture"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Architecture"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["CPU"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "CPU"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["CPU"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["CPU core count"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "CPU core count"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["CPU core count"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["CPU nominal frequency"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "CPU nominal frequency"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["CPU nominal frequency"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["License level"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "License level"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["License level"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Operating System"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Operating System"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Operating System"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Size of RAM"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Size of RAM"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Size of RAM"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Storage size"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Storage size"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Storage size"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["PoE in"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "PoE in"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["PoE in"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["PoE out"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "PoE out"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["PoE out"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["PoE-out ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "PoE-out ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["PoE-out ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["PoE in input Voltage"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "PoE in input Voltage"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["PoE in input Voltage"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Number of DC inputs"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Number of DC inputs"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Number of DC inputs"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["DC jack input Voltage"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "DC jack input Voltage"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["DC jack input Voltage"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Max power consumption (W)"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Max power consumption (W)"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Max power consumption (W)"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Wireless 2.4 GHz number of chains"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Wireless 2.4 GHz number of chains"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Wireless 2.4 GHz number of chains"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Antenna gain dBi for 2.4 GHz"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Antenna gain dBi for 2.4 GHz"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Antenna gain dBi for 2.4 GHz"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Wireless 5 GHz number of chains"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Wireless 5 GHz number of chains"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Wireless 5 GHz number of chains"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Antenna gain dBi for 5 GHz"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Antenna gain dBi for 5 GHz"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Antenna gain dBi for 5 GHz"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["10/100 Ethernet ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "10/100 Ethernet ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["10/100 Ethernet ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["10/100/1000 Ethernet ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "10/100/1000 Ethernet ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["10/100/1000 Ethernet ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["2.5G Ethernet ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "2.5G Ethernet ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["2.5G Ethernet ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["USB ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "USB ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["USB ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Ethernet Combo ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Ethernet Combo ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Ethernet Combo ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["SFP ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "SFP ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["SFP ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["SFP+ ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "SFP+ ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["SFP+ ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["1G/2.5G/5G/10G Ethernet ports"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "1G/2.5G/5G/10G Ethernet ports"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["1G/2.5G/5G/10G Ethernet ports"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["SIM slots"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "SIM slots"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["SIM slots"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["Memory Cards"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "Memory Cards"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["Memory Cards"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    if dictTemp["USB slot type"] != "":
      dictOut["Attribute {} name".format(iAttrCount)] = "USB slot type"
      dictOut["Attribute {} value(s)".format(iAttrCount)] = dictTemp["USB slot type"]
      dictOut["Attribute {} visible".format(iAttrCount)] = "1"
      dictOut["Attribute {} global".format(iAttrCount)] = "0"
      iAttrCount += 1
    lstOut.append(dictOut)
    dictOut = {}
  objFileIn.close()
  lstFieldNames = lstOut[0].keys() if lstOut else []
  for objRow in lstOut:
    if len(objRow.keys()) > len(lstFieldNames):
      lstFieldNames = objRow.keys()
  strOutFile = strSaveFolder + "MTWoocommerceImport{}.json".format(ISO)
  objFileOut = GetFileHandle(strOutFile, "w")
  objFileOut.write(json.dumps(lstOut, indent=2))
  objFileOut.close()
  LogEntry("Done processing MikroTik product file, json saved to {}".format(strOutFile))
  strOutFile = strSaveFolder + "MTWoocommerceImport{}.csv".format(ISO)
  with open(strOutFile, mode='w', newline='', encoding='utf-8') as objFileOut:
    objWriter = csv.DictWriter(objFileOut, fieldnames=lstFieldNames)
    objWriter.writeheader()
    for objRow in lstOut:
        objWriter.writerow(objRow)

  LogEntry("CSV output saved to {}".format(strOutFile))
  objLogOut.close()

if __name__ == '__main__':
  main()
