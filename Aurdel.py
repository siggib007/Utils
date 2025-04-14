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
import csv
import json
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

# End imports

#avoid insecure warning
requests.urllib3.disable_warnings()

#Define and initialize
lstHTMLElements = ["</a>", "</p>", "</ol>",
                   "</li>", "</ul>", "</span>", "</div>"]

lstBadChar = ["?", "!", "'", '"', "~", "#", "%", "&", "*", ":", "<", ">", "?", "/", "\\",
              "{", " | ", "}", "$", "!", "@", "+", "=", "`"]

strBaseURL = "https://api.aurdel.com/Prices/getPrice"
strTranslateURL = "https://api-free.deepl.com/v2/translate"
strXchangeURL = "https://v1.apiplugin.io/v1/currency/"
iTimeOut = 20  # Connection timeout in seconds
iMinQuiet = 5  # Minimum time in seconds between API calls
tLastCall = 0
iTotalSleep = 0

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

  #strClean = strClean.replace(".","-")
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

def LogEntry(strMsg, iLogLevel=0):
  global iVerbose
  if iLogLevel > iVerbose:
    return
  if strMsg is None:
    return
  if objLogOut is None:
    print("Log file not open")
    return
  if objLogOut.closed == True:
    print("Log file closed")
    return
  if strMsg == "":
    return

  # Write to log file and console
  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
  objLogOut.flush()
  print(strMsg)

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

def processConf():
  global strCustID
  global strCompID
  global strAPIKey
  global strSaveFolder
  global strDeeplKey
  global strXchangeAPIKey
  global strXchangeAppID
  global iMarkup

  strCustID = None
  strCompID = None
  strAPIKey = None
  strSaveFolder = ""
  strDeeplKey = None
  strXchangeAPIKey = None
  strXchangeAppID = None
  iMarkup = 0


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
      if strVarName == "DEEPL_AUTH_KEY":
        strDeeplKey = strValue
      if strVarName == "XCHANGE_API_KEY":
        strXchangeAPIKey = strValue
      if strVarName == "XCHANGE_APPID":
        strXchangeAppID = strValue
      if strVarName == "Markup":
        strMarkup = strValue
        if isInt(strMarkup):
          iMarkup = int(strMarkup)
        else:
          LogEntry ("Markup value {} is not an integer".format(strMarkup))
          iMarkup = 0

  LogEntry ("Done processing configuration, moving on")

def FetchXchange(strBaseCurrency, strTargetCurrency):

  strAuthKey="Bearer " + strXchangeAPIKey
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = strAuthKey

  dictParams = {}
  dictParams["source"] = strBaseCurrency
  dictParams["target"] = strTargetCurrency
  strParams = urlparse.urlencode(dictParams)
  strURL = strXchangeURL + strXchangeAppID + "/rates?" + strParams

  try:
    WebRequest = requests.get(strURL, headers=dictHeader, verify=False, timeout=iTimeOut)
  except Exception as err:
    LogEntry("Issue with API call. {}".format(err))
    return 0

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry("response is unknown type")
    return 0

  if WebRequest.status_code != 200:
    LogEntry("Failed to get a exchange rate. Status code: {}".format(WebRequest.status_code))
    return 0
  if WebRequest.text is None:
    LogEntry("Response from exchange rate API is None")
    return 0
  dictResponse = json.loads(WebRequest.text)
  if "rates" not in dictResponse:
    LogEntry("No rates in response. Here is the response: {}".format(dictResponse))
    return 0
  if len(dictResponse["rates"]) == 0:
    LogEntry("Rates in response is zero length")
    return 0
  if isinstance(dictResponse["rates"], dict) == False:
    LogEntry("rates is not a dict")
    return 0

  return dictResponse["rates"]

def Translate(strText):
  global tLastCall
  global iTotalSleep
  global iStatusCode

  if strText is None:
    return ""

  fTemp = time.time()
  fDelta = fTemp - tLastCall
  LogEntry("It's been {} seconds since last API call".format(fDelta),3)
  if fDelta > iMinQuiet:
      tLastCall = time.time()
  else:
      iDelta = int(fDelta)
      iAddWait = iMinQuiet - iDelta
      LogEntry("It has been less than {} seconds since last API call, "
                "waiting {} seconds".format(iMinQuiet, iAddWait),3)
      iTotalSleep += iAddWait
      time.sleep(iAddWait)

  strAuthKey = "DeepL-Auth-Key " + strDeeplKey

  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = strAuthKey

  lstTexts = []
  lstTexts.append(strText)
  dictPayload = {}
  dictPayload["target_lang"] = "EN"
  dictPayload["text"] = lstTexts

  try:
    WebRequest = requests.post(strTranslateURL, timeout=iTimeOut, json=dictPayload, headers=dictHeader, verify=False)
  except Exception as err:
    LogEntry("Issue with API call. {}".format(err))
    return strText

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry("response is unknown type")
    return strText

  if WebRequest.status_code != 200:
    LogEntry("Failed to get a translation. Status code: {}".format(WebRequest.status_code))
    return strText
  if WebRequest.text is None:
    LogEntry("No response from translation API")
    return strText
  dictResponse = json.loads(WebRequest.text)
  if "translations" not in dictResponse:
    LogEntry("No translations in response. Here is the response: {}".format(dictResponse))
    return strText
  if len(dictResponse["translations"]) == 0:
    LogEntry("Translations in response is zero length")
    return strText
  if isinstance(dictResponse["translations"], list) == False:
    LogEntry("Translations is not a list")
    return strText
  if "text" not in dictResponse["translations"][0]:
    LogEntry("No text in first item in translation response")
    return strText
  if dictResponse["translations"][0]["text"] is None:
    LogEntry("text element in translation response is None")
    return strText
  if dictResponse["translations"][0]["text"] == "":
    LogEntry("Text in translation response is empty")
    return strText
  strText = dictResponse["translations"][0]["text"]
  return strText

def FetchPicture(dictPic):
  global dictPictures

  if not isinstance(dictPic, (dict,list)):
    return
  if isinstance(dictPic, list):
    for pic in dictPic:
      strPicFileName = CleanString(pic["filename"])
      strPicURL = pic["url"]
      if strPicFileName not in dictPictures:
        dictPictures[strPicFileName] = strPicURL
  else:
      strPicFileName = CleanString(dictPic["filename"])
      strPicURL = dictPic["url"]
      if strPicFileName not in dictPictures:
        dictPictures[strPicFileName] = strPicURL
  return

def ProcessItem(dictItem):
  global dictPictures

  dictOut = {}
  LogEntry("Aurdel ItemID:{}".format(dictItem["@id"]))
  dictOut["Aurdel ItemID"] = dictItem["@id"]
  dictOut["EAN"] = "" if dictItem["ean"] is None else "'" + dictItem["ean"]
  dictOut["Manufacturer"] = dictItem["manufacturer"]["description"]
  dictOut["SKU"] = dictItem["manufacturer"]["@id"]
  dictOut["Short description"] = Translate(dictItem["description"]["short"])
  LogEntry("MFG:{} MPN:{} EAN:{}".format(dictItem["manufacturer"]["description"], dictItem["manufacturer"]["@id"], dictItem["ean"]))
  LogEntry("Short:{}".format(dictItem["description"]["short"]))
  strLongDesc = Translate(dictItem["description"]["long"])
  dictOut["Description"] = strLongDesc
  LogEntry("Long:{}".format(strLongDesc))
  strCurrencyPrice = "{} {}".format(dictItem["price"]["net"],dictItem["price"]["@currencycode"])
  LogEntry("Price: {}".format(strCurrencyPrice.replace(",", ".")))
  strLabel = "Price ({})".format(dictItem["price"]["@currencycode"])
  strPrice = dictItem["price"]["net"]
  fPrice = float(strPrice.replace(",", "."))
  dictOut[strLabel] = fPrice
  fPriceISK = round(fPrice * fXchange, 2)
  dictOut["Purchase Price ISK"] = fPriceISK
  LogEntry("Purchase Price ISK: {}".format(dictOut["Purchase Price ISK"]))
  dictOut["Regular price"] = round(fPriceISK * (1 + (iMarkup / 100)), 2)
  LogEntry("Retail Price: {}".format(dictOut["Regular price"]))

  LogEntry("Aurdel Stock:{}".format(dictItem["stock"]["@quantity"]))
  dictOut["Aurdel Stock"] = dictItem["stock"]["@quantity"]
  if "piecespercarton" in dictItem:
    LogEntry("Pieces Per Carton:{}".format(dictItem["piecespercarton"]))
    dictOut["Pieces Per Carton"] = dictItem["piecespercarton"]
  LogEntry("Weight:{} {}".format(dictItem["weight"]["#text"],dictItem["weight"]["@unit"]))
  strWeightName = "Weight ({})".format(dictItem["weight"]["@unit"])
  dictOut[strWeightName] = dictItem["weight"]["#text"].replace(",",".")
  if "physicaldimensions" in dictItem:
    strLabel = "Width ({})".format(dictItem["physicaldimensions"]["width"]["@unit"])
    dictOut[strLabel] = dictItem["physicaldimensions"]["width"]["#text"].replace(",",".")
    strLabel = "Depth ({})".format(dictItem["physicaldimensions"]["depth"]["@unit"])
    dictOut[strLabel] = dictItem["physicaldimensions"]["depth"]["#text"].replace(",",".")
    strLabel = "Height ({})".format(dictItem["physicaldimensions"]["height"]["@unit"])
    dictOut[strLabel] = dictItem["physicaldimensions"]["height"]["#text"].replace(",",".")
    LogEntry("Dimensions: {} {} W x {} {} D x {} {} H".format(
      dictItem["physicaldimensions"]["width"]["#text"].replace(",","."),
      dictItem["physicaldimensions"]["width"]["@unit"],
      dictItem["physicaldimensions"]["depth"]["#text"].replace(",","."),
      dictItem["physicaldimensions"]["depth"]["@unit"],
      dictItem["physicaldimensions"]["height"]["#text"].replace(",","."),
      dictItem["physicaldimensions"]["height"]["@unit"]
      ))
  dictAttributes = {}
  if "specifications" in dictItem and "specification" in dictItem["specifications"]:
    for spec in dictItem["specifications"]["specification"]:
      strSpecDesc = Translate(spec["title"]["description"])
      strSpecValue = Translate(spec["values"]["value"]["description"])
      dictAttributes[strSpecDesc] = strSpecValue
  lstCatergories = []
  if isinstance(dictItem["categories"]["category"]["subcategory"], list):
    for cat in dictItem["categories"]["category"]["subcategory"]:
      strCatDesc = Translate(cat["description"])
      strCatDesc = strCatDesc.replace(" ＆ "," & ")
      lstCatergories.append(strCatDesc)
  else:
    strCatDesc = Translate(dictItem["categories"]["category"]["subcategory"]["description"]).replace(" ＆ "," & ")
    lstCatergories.append(strCatDesc)
  LogEntry("Categories:{}".format(",".join(lstCatergories)))
  dictOut["Categories"] = ",".join(lstCatergories)

  dictPictures = {}
  FetchPicture(dictItem["pictures"]["list"]["picture"])
  FetchPicture(dictItem["pictures"]["gallery"]["picture"])
  FetchPicture(dictItem["pictures"]["zoom"]["picture"])
  lstPixNames = []
  for pic in dictPictures:
    strPicFileName = CleanString(pic)
    lstPixNames.append(strPicFileName)
    strPicFileName = strSaveFolder + strPicFileName
    strPicURL = dictPictures[pic]
    LogEntry("Downloading picture {} to {}".format(strPicURL,strPicFileName))
    try:
      WebRequest = requests.get(strPicURL, headers={}, verify=False, timeout=iTimeOut)
      if isinstance(WebRequest, requests.models.Response) == False:
        LogEntry("response is unknown type")
        continue
      if WebRequest.status_code != 200:
        LogEntry("Unable to download image: {}".format(strPicURL))
        continue
      with open(strPicFileName, "wb") as objFileHndl:
        objFileHndl.write(WebRequest.content)
        objFileHndl.close()
    except Exception as err:
      LogEntry("Issue with API call. {}".format(err))
  dictOut["Images"] = ",".join(lstPixNames)
  iAttrCount = 1
  LogEntry("Attributes:")
  for strKey in dictAttributes.keys():
    LogEntry("   {}:{}".format(strKey,dictAttributes[strKey]))
    dictOut["Attribute {} name".format(iAttrCount)] = strKey
    dictOut["Attribute {} value(s)".format(iAttrCount)] = dictAttributes[strKey]
    dictOut["Attribute {} visible".format(iAttrCount)] = "1"
    dictOut["Attribute {} global".format(iAttrCount)] = "1"
    iAttrCount += 1
  return dictOut

def main():
  global objLogOut
  global strCustID
  global strCompID
  global strAPIKey
  global strConf_File
  global strSaveFolder
  global strDeeplKey
  global iVerbose
  global strXchangeAPIKey
  global strXchangeAppID
  global fXchange
  global iMarkup

  lstOut = []

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
    LogEntry("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  objLogOut = GetFileHandle(strLogFile, "w")

  iLoc = sys.argv[0].rfind(".")
  strDefConf = sys.argv[0][:iLoc] + ".ini"
  objParser = argparse.ArgumentParser(description="Script to fetch details on particulat part number")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file", default=strDefConf)
  objParser.add_argument("-o", "--out", type=str, help="Path to store output files")
  objParser.add_argument("-i", "--input", type=str, help="List of part numbers to process")
  objParser.add_argument("-m", "--markup", type=int, help="How much markup to use, overwrites config file")
  objParser.add_argument("-v", "--verbosity", action="count", default=0, help="Verbose output, vv level 2 vvvv level 4")
  args = objParser.parse_args()
  strConf_File = args.config
  iVerbose = args.verbosity
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
  if FetchEnv("DEEPL_AUTH_KEY") is not None:
    strDeeplKey = FetchEnv("DEEPL_AUTH_KEY")
  if FetchEnv("XCHANGE_API_KEY") is not None:
    strXchangeAPIKey = FetchEnv("XCHANGE_API_KEY")
  if FetchEnv("XCHANGE_APPID") is not None:
    strXchangeAppID = FetchEnv("XCHANGE_APPID")
  if strDeeplKey == "":
      strDeeplKey = None

  if args.markup is not None:
    iMarkup = args.markup
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

  if strCustID is None or strCompID is None or strAPIKey is None or strDeeplKey is None or strXchangeAPIKey is None or strXchangeAppID is None:
    LogEntry("Unable to continue, missing customerid, companyid or one of the apikeys")
    objLogOut.close()
    sys.exit(1)

  dictXchange = FetchXchange("EUR", "ISK")
  if "ISK" in dictXchange:
    LogEntry("EUR to ISK exchange rate: {}".format(dictXchange["ISK"]))
    fXchange = float(dictXchange["ISK"])
    fXchange = round(fXchange, 2)
  else:
    LogEntry("Unable to get exchange rate for ISK")
    objLogOut.close()
    sys.exit(1)
  LogEntry("Markup is set to {}%".format(iMarkup))
  if args.input is None:
     strInput = getInput("Please enter part number to process: ")
  else:
      strInput = args.input.strip()

  if strInput == "":
    LogEntry("Nothing to process, exiting")
    objLogOut.close()
    sys.exit(1)

  strXML = FetchXML(strInput)
  try:
    dictInput = xmltodict.parse(strXML)
  except xml.parsers.expat.ExpatError as err:
    dictInput={}
    LogEntry("Expat Error: {}\n{}".format(err,strXML[:99]))
    objLogOut.close()
    sys.exit(1)

  if "Error" in dictInput.keys():
    LogEntry("Error {} in response:{}\n{}".format(dictInput["Error"]["Code"],dictInput["Error"]["Info"],dictInput["Error"]["Details"]))
    objLogOut.close()
    sys.exit(1)

  if "items" in dictInput["database"]["DELTACO.SE"]["data"]:
    dictItems = dictInput["database"]["DELTACO.SE"]["data"]["items"]["item"]
    if isinstance(dictItems, list):
      for dictItem in dictItems:
        dictOut = ProcessItem(dictItem)
        lstOut.append(dictOut)
    else:
      dictOut = ProcessItem(dictItems)
      lstOut.append(dictOut)
  else:
    LogEntry("No items found in response")

  lstFieldNames = lstOut[0].keys() if lstOut else []
  for objRow in lstOut:
    if len(objRow.keys()) > len(lstFieldNames):
      lstFieldNames = objRow.keys()
  strOutFile = strSaveFolder + "Aurdel-Order-{}.json".format(ISO)
  objFileOut = GetFileHandle(strOutFile, "w")
  objFileOut.write(json.dumps(lstOut, indent=2))
  objFileOut.close()
  LogEntry("Done processing product list file, json saved to {}".format(strOutFile))
  strOutFile = strSaveFolder + "Aurdel-Order-{}.csv".format(ISO)
  with open(strOutFile, mode='w', newline='') as objFileOut:
    objWriter = csv.DictWriter(objFileOut, fieldnames=lstFieldNames)
    objWriter.writeheader()
    for objRow in lstOut:
        objWriter.writerow(objRow)

  LogEntry("CSV output saved to {}".format(strOutFile))

  LogEntry("Done!")
  objLogOut.close()
  print("Log closed")


if __name__ == '__main__':
    main()