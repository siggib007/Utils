'''
Script Transfers expenses from Zoho Expense to payday

Author Siggi Bjarnason 21 april 2025
Öruggt Net Copyright 2025.

Following packages need to be installed
pip install requests
pip install jason

'''
# Import libraries
import os
import time
import platform
import sys
import csv
import subprocess
import argparse
import fnmatch

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
csvDelim = ","

# Define few Defaults
iTimeOut = 180  # Max time in seconds to wait for network response
iMinQuiet = 2  # Minimum time in seconds between API calls

# sub defs
def ListAttachments(strDirectory, strPattern):
    """
    Lists all files in the given directory that match the specified pattern.
    Parameters:
        strDirectory: The directory to search in.
        strPattern: The pattern to match (e.g., '[0-9]*' for files starting with a number).
    Returns:
        A list of matching file names.
    """
    lstFiles = []
    for file in os.listdir(strDirectory):
        if fnmatch.fnmatch(file, strPattern):
            lstFiles.append(file)
    return lstFiles

def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    return raw_input(strPrompt)

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
  objFileIn.close()
  objLogOut.close()
  print("objLogOut closed")

  sys.exit(9)

def LogEntry(strMsg, iMsgLevel=0, bAbort=False):
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
  if iVerbose > iMsgLevel:
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

def MakeAPICall(strURL, dictHeader, strMethod, dictPayload="", lstFiles=[], strUser="", strPWD=""):
  """
  Handles the actual communication with the API, has a backoff mechanism
  MinQuiet defines how many seconds must elapse between each API call.
  Sets a global variable iStatusCode, with the HTTP code returned by the API (200, 404, etc)
  Parameters:
    strURL: Simple String. API EndPoint to call
    dictHeader: Simple string with the header to pass along with the call
    strMethod: Simple string. Call method such as GET, PUT, POST, etc
    dictPayload: Optional. Any payload to send along in the appropriate structure and format
    lstFiles: Optional. List of files (full absolute paths) to be uploaded, if any
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
  LogEntry("It's been {} seconds since last API call".format(fDelta), 4)
  if fDelta > iMinQuiet:
    tLastCall = time.time()
  else:
    iDelta = int(fDelta)
    iAddWait = iMinQuiet - iDelta
    LogEntry("It has been less than {} seconds since last API call, "
              "waiting {} seconds".format(iMinQuiet, iAddWait), 4)
    iTotalSleep += iAddWait
    time.sleep(iAddWait)

  strErrCode = ""
  strErrText = ""
  dictReturn = {}

  LogEntry("Doing a {} to URL: {}".format(strMethod, strURL), 1)
  try:
    if strMethod.lower() == "get":
      if strUser != "":
        LogEntry(
            "I have none blank credentials so I'm doing basic auth", 3)
        WebRequest = requests.get(strURL, timeout=iTimeOut, headers=dictHeader,
                                  auth=(strUser, strPWD), verify=False, proxies=dictProxies)
      else:
        LogEntry("credentials are blank, proceeding without auth", 3)
        WebRequest = requests.get(
            strURL, timeout=iTimeOut, headers=dictHeader, verify=False, proxies=dictProxies)
      LogEntry("get executed", 4)
    if strMethod.lower() == "post":
      if dictPayload:
        dictTmp = dictPayload.copy()
        if "password" in dictTmp:
            dictTmp["password"] = dictTmp["password"][:2]+"*********"
        if "clientSecret" in dictTmp:
            dictTmp["clientSecret"] = dictTmp["clientSecret"][:2]+"*********"
        if strUser != "":
          LogEntry("I have none blank credentials so I'm doing basic auth", 3)
          LogEntry("with user auth and payload of: {}".format(dictTmp), 4)
          WebRequest = requests.post(strURL, json=dictPayload, timeout=iTimeOut,
                                      headers=dictHeader, auth=(strUser, strPWD),
                                      verify=False, proxies=dictProxies,files=lstFiles)
        else:
          LogEntry("credentials are blank, proceeding without auth", 3)
          LogEntry("with payload of: {}".format(dictTmp), 4)
          WebRequest = requests.post(
              strURL, json=dictPayload, timeout=iTimeOut, headers=dictHeader,
              files=lstFiles, verify=False, proxies=dictProxies)
      else:
        LogEntry("No payload, doing a simple post", 3)
        WebRequest = requests.post(
            strURL, headers=dictHeader, verify=False, proxies=dictProxies, files=lstFiles)
      LogEntry("post executed", 4)
  except Exception as err:
    dictReturn["condition"] = "Issue with API call"
    dictReturn["errormsg"] = err
    return ({"Success": False}, [dictReturn])

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry("response is unknown type", 1)
    strErrCode = "ResponseErr"
    strErrText = "response is unknown type"

  LogEntry("call resulted in status code {}".format(
    WebRequest.status_code), 3)
  iStatusCode = int(WebRequest.status_code)

  if iStatusCode not in (200,201,204):
    strErrCode += str(iStatusCode)
    strErrText += "HTTP Error"
    LogEntry("HTTP Error: {}".format(iStatusCode), 3)
    LogEntry("Response: {}".format(WebRequest.content), 4)
  if strErrCode != "":
    dictReturn["condition"] = "problem with your request"
    dictReturn["errcode"] = strErrCode
    dictReturn["errormsg"] = strErrText
    return ({"Success": False}, [dictReturn])
  else:
    if "<html>" in WebRequest.text[:99] or WebRequest.text== "":
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
      objFileHndl = open(strFileName, strperm, encoding="utf-8")
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

def ValidateKT(strKennitala):
  """
  This script takes a kennitala (an Icelandic SSN) and checks if it is valid.
  It does this by checking the length and if it is a number.
  Then it checks the checksum of the kennitala.
  Parameters:
    strKennitala: simple string containing the kennitala to be validated
  Returns:
    Boolean indicating if the kennitala is valid or not.
  """
  strKennitala = strKennitala.replace("-", "").replace(" ", "").replace(".", "").replace(",", "")
  if len(strKennitala) != 10 or not strKennitala.isdigit():
    return False
  lstSum = []
  lstCheck = [3,2,7,6,5,4,3,2]
  for index,char in enumerate(strKennitala[:8]):
    lstSum.append(int(char) * lstCheck[index])
  intSum = sum(lstSum)
  intCheck = intSum % 11
  return (11 - intCheck) == int(strKennitala[8])

def processConf():
  global strBaseURL
  global strClientID
  global strClientSecret
  global strAttachments
  global strInfile
  global strProxy
  global csvDelim
  global bDeductable

  strBaseURL = None
  strClientID = None
  strClientSecret = None
  strAttachments = None
  strInfile = None
  strProxy = None
  bDeductable = True

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
      if strVarName == "API_URL":
        if strValue != "":
          strBaseURL = strValue
      if strVarName == "CLIENT_ID":
        if strValue != "":
          strClientID = strValue
      if strVarName == "CLIENT_SECRET":
        if strValue != "":
          strClientSecret = strValue
      if strVarName == "ATTACHMENTS":
        if strValue != "":
          strAttachments = strValue
      if strVarName == "IN_FILE":
        if strValue != "":
          strInfile = strValue
      if strVarName == "PROXY":
        if strValue != "":
          strProxy = strValue
      if strVarName == "CSV_DELIM":
        if strValue != "":
          csvDelim = strValue
      if strVarName == "DEDUCTABLE":
        bDeductable = strValue.lower() == "true"


  LogEntry ("Done processing configuration, moving on")

def main():
  global objLogOut
  global objFileIn
  global strScriptName
  global strScriptHost
  global strBaseDir
  global iMinQuiet
  global iTimeOut
  global dictProxies
  global strConf_File
  global iVerbose
  global strBaseURL
  global strClientID
  global strClientSecret
  global strAttachments
  global strInfile
  global strProxy
  global csvDelim
  global bDeductable

  lstSysArg = sys.argv
  strInfile = ""
  strAttachments = ""

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

  objParser = argparse.ArgumentParser(description="Script to transfer expense items from Zoho expense to Payday. All items overwrite configuration file settings as well as environment variables.")
  objParser.add_argument("-i", "--input", type=str, help="Path to Expense file to be processed")
  objParser.add_argument("-p", "--prompt", action="store_true", help="Ignore any input file and prompt for a file to be processed")
  objParser.add_argument("-a", "--attachments", type=str, help="Path to attachments to be processed")
  objParser.add_argument("-d", "--deductable", type=str, help="Is the VAT in this file deductable? True/False. Default is True")
  objParser.add_argument("-v", "--verbosity", action="count", default=1, help="Verbose output, vv level 2 vvvv level 4")
  objParser.add_argument("-c", "--config",type=str, help="Path to configuration file, where you can configure API keys, and other items", default=strDefConf)
  objParser.add_argument("-u", "--URL", type=str, help="Base URL for API calls")
  args = objParser.parse_args()
  strConf_File = args.config
  iVerbose = args.verbosity
  LogEntry("Verbosity set to {}".format(iVerbose))
  LogEntry("conf file set to: {}".format(strConf_File))
  processConf()

  if args.input is not None:
    strInfile = args.input

  if FetchEnv("API_URL") is not None:
    strBaseURL = FetchEnv("API_URL")
  if strBaseURL == "":
      strBaseURL = None
  if args.URL is not None:
    strBaseURL = args.URL
  if FetchEnv("CLIENT_ID") is not None:
    strClientID = FetchEnv("CLIENT_ID")
  if strClientID == "":
      strClientID = None
  if FetchEnv("CLIENT_SECRET") is not None:
    strClientSecret = FetchEnv("CLIENT_SECRET")
  if strClientSecret == "":
      strClientSecret = None

  if strBaseURL is None or strClientID is None or strClientSecret is None:
    CleanExit("No URL or API auth config, exiting")

  if FetchEnv("ATTACHMENTS") is not None:
    strAttachments = FetchEnv("ATTACHMENTS")

  if FetchEnv("CSV_DELIM") is not None:
    csvDelim = FetchEnv("CSV_DELIM")

  if args.attachments is not None:
    strAttachments = args.attachments

  if FetchEnv("DEDUCTABLE") is not None:
    strDeduct = FetchEnv("DEDUCTABLE")
    bDeductable = strDeduct.lower() == "true"
  if args.deductable is not None:
    bDeductable = args.deductable.lower() == "true"

  if not os.path.exists(strAttachments):
      CleanExit("Attachments path {} does not exist".format(strAttachments))
  strAttachments = strAttachments.replace("\\", "/")

  if not os.path.exists(strInfile):
      LogEntry("Input file {} does not exist".format(strInfile))
      strInfile = ""

  if strInfile == "" or args.prompt:
    if btKinterOK:
      root = tk.Tk()
      root.withdraw()
      strInfile = filedialog.askopenfilename(title="Select file to process", initialdir=strBaseDir)
    else:
      strInfile = ""

  if strInfile == "":
    strInfile = getInput("Please enter the path to the file to be processed: ")

  if strInfile == "":
    CleanExit("No input file provided, exiting")

  iLoc = strInfile.rfind(".")
  strFileExt = strInfile[iLoc+1:]

  if strFileExt.lower() == "csv":
    objFileIn = GetFileHandle (strInfile, "r")
  else:
    CleanExit("only able to process csv files. Unable to process {} files".format(strFileExt))

  if FetchEnv("PROXY") is not None:
      strProxy = os.getenv("PROXY")
      dictProxies = {}
      dictProxies["http"] = strProxy
      dictProxies["https"] = strProxy
      LogEntry("Proxy has been configured for {}".format(strProxy), 5)
  else:
      dictProxies = {}

  strKennitala = getInput("Please enter the kennitala of the user to be used: ")
  while not ValidateKT(strKennitala):
    strKennitala = getInput("Invalid Kennital. Please enter a valid kennitala of the user to be used: ")
  if strBaseURL[-1:] != "/":
    strBaseURL += "/"
  strMethod = "post"
  dictHeader = {}
  dictHeader["Content-type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Api-Version"] = "alpha"

  dictBody = {}
  dictBody["clientId"] = strClientID
  dictBody["clientSecret"] = strClientSecret

  strURL = "{}auth/token".format(strBaseURL)

  APIResp = MakeAPICall(strURL, dictHeader, strMethod, dictBody)
  if APIResp[0]["Success"] == False:
    CleanExit(APIResp)
  else:
    strAccessToken = APIResp[1]["accessToken"]

  strMethod = "get"
  dictHeader["Authorization"] = "Bearer {}".format(strAccessToken)
  strURL = "{}accounting/accounts".format(strBaseURL)
  APIResp = MakeAPICall(strURL, dictHeader, strMethod)
  if APIResp[0]["Success"] == False:
    CleanExit(APIResp)
  else:
    dictAccounts = APIResp[1]
    dictAcctRef = {}
    for dictAccount in dictAccounts:
      strAcctID = dictAccount["id"]
      strAcctCode = dictAccount["code"]
      dictAcctRef[strAcctCode] = strAcctID

  lstBadAccctCodes = []
  objReader = csv.DictReader(objFileIn, delimiter=csvDelim)
  for dictTemp in objReader:
    if dictTemp["Category Account Code"] not in dictAcctRef:
      if dictTemp["Category Account Code"] not in lstBadAccctCodes:
        lstBadAccctCodes.append(dictTemp["Category Account Code"])
  if len(lstBadAccctCodes) > 0:
      CleanExit("Unable to find the following account codes in the list of accounts: {}".format(lstBadAccctCodes))
  objFileIn.close()
  objFileIn = GetFileHandle(strInfile, "r")

  strURL = "{}expenses/paymenttypes".format(strBaseURL)
  APIResp = MakeAPICall(strURL, dictHeader, strMethod)
  if APIResp[0]["Success"] == False:
    CleanExit(APIResp)
  else:
    dictPaymentTypes = APIResp[1]
  print("Please select a payment type from the list below")
  print("ID: Name (Description)")
  for i in range(len(dictPaymentTypes)):
    strPayTypeName = dictPaymentTypes[i]["title"]
    strPayTypeDescr = dictPaymentTypes[i]["description"]
    print("{}: {} ({})".format(i, strPayTypeName, strPayTypeDescr))
  strPayType = getInput("Please enter the payment type ID: ")
  if not isInt(strPayType):
    CleanExit("Payment type ID must be an integer")
  if int(strPayType) < 0 or int(strPayType) >= len(dictPaymentTypes):
    CleanExit("Payment type ID must be between 0 and {}".format(len(dictPaymentTypes)-1))

  strPayTypeID = dictPaymentTypes[int(strPayType)]["id"]
  LogEntry("Payment type ID {}: {}, was selected".format(strPayType,strPayTypeID))

  strMethod = "post"
  strURL = "{}expenses".format(strBaseURL)

  strEntryID = ""
  objReader = csv.DictReader(objFileIn, delimiter=csvDelim)
  for dictTemp in objReader:
    if dictTemp["Category Account Code"] in dictAcctRef:
      strAcctID = dictAcctRef[dictTemp["Category Account Code"]]
    else:
      LogEntry("Unable to find account code {} in the list of accounts".format(dictTemp["Category Account Code"]))
      continue
    strDescription = dictTemp["Expense Description"]
    if dictTemp["Tax Percentage"] == "":
      dictTemp["Tax Percentage"] = 0.0
    if strEntryID == dictTemp["Entry Number"]:
      dictLine = {}
      dictLine["quantity"] = 1
      dictLine["description"] = strDescription
      dictLine["unitPriceIncludingVat"] = dictTemp["Expense Total Amount (in Reimbursement Currency)"]
      dictLine["vatPercentage"] = dictTemp["Tax Percentage"]
      dictLine["accountId"] = strAcctID
      dictBody["lines"].append(dictLine)
    else:
      if strEntryID != "":
        lstFiles = []
        APIResp = MakeAPICall(strURL, dictHeader, strMethod, dictBody, lstFiles)
        print("APIResp: {}".format(APIResp))
      strEntryID = dictTemp["Entry Number"]
      print("Working on: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}".format(
          dictTemp["Expense Description"],dictTemp["Expense Item Date"], dictTemp["Is Reimbursable"], dictTemp["Category Account Code"],
          dictTemp["Entry Number"],dictTemp["Mileage Type"],dictTemp["Distance"],dictTemp["Mileage Unit"],dictTemp["Mileage Rate"],
          dictTemp["Vehicle Name"],dictTemp["Expense Total Amount (in Reimbursement Currency)"],
          dictTemp["Expense Category"],dictTemp["Merchant Name"],dictTemp["Report Number"],dictTemp["Tax Percentage"]
          ))
      lstAttachments = ListAttachments(strAttachments, dictTemp["Entry Number"] + "*")
      lstFiles = []
      for strfile in lstAttachments:
        strFilePath = strAttachments + "/" + strfile
        if os.path.isfile(strFilePath):
          lstFiles.append(("attachment",(strfile, open(strFilePath, 'rb'))))
        else:
          LogEntry("Unable to find attachment file {}".format(strFilePath), 2, True)
      dictBody = {}
      dictBody["creditor"] = {}
      if dictTemp["Mileage Type"] == "NonMileage":
        dictBody["creditor"]["Name"] = dictTemp["Merchant Name"]
        strDescription = dictTemp["Expense Description"]
      else:
        dictBody["creditor"]["ssn"] = strKennitala
        strDescription= "Mileage for {} - {} {} @ {}".format(dictTemp["Vehicle Name"],dictTemp["Distance"],dictTemp["Mileage Unit"],dictTemp["Mileage Rate"])
        dictBody["comment"] = dictTemp["Expense Description"]

      dictBody["date"] = dictTemp["Expense Item Date"]
      dictBody["deductible"] = bDeductable
      dictBody["status"] = "PAID"
      dictBody["paidDate"] = dictTemp["Expense Item Date"]
      dictBody["paymentType"] = {}
      dictBody["paymentType"]["id"] = strPayTypeID
      #dictBody["reference"] = dictTemp["Report Number"]
      dictBody["reference"] = "Another Import Test"
      dictBody["lines"] = []
      dictLine = {}
      dictLine["quantity"] = 1
      dictLine["description"] = strDescription
      dictLine["unitPriceIncludingVat"] = dictTemp["Expense Total Amount (in Reimbursement Currency)"]
      dictLine["vatPercentage"] = dictTemp["Tax Percentage"]
      dictLine["accountId"] = strAcctID
      dictBody["lines"].append(dictLine)
  objFileIn.close()
  objLogOut.close()




if __name__ == '__main__':
  main()
