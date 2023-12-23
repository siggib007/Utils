'''
Script that tests proxy responses

Author Siggi Bjarnason 23 Oktober 2023
Nanitor Copyright 2023.

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


def main():
    global objLogOut
    global strScriptName
    global strScriptHost
    global strBaseDir
    global iMinQuiet
    global iTimeOut
    global iLogLevel
    global dictProxies

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

    print("This is a script to test if a URL responds via proxy. "
          "This is running under Python Version {}".format(strVersion))
    print("Running from: {}".format(strRealPath))
    dtNow = time.strftime("%A %d %B %Y %H:%M:%S %Z")
    print("The time now is {}".format(dtNow))
    print("Logs saved to {}".format(strLogFile))
    objLogOut = open(strLogFile, "w", 1)

    strURL = ""

    # fetching secrets in environment
    if os.getenv("APIBASEURL") != "" and os.getenv("APIBASEURL") is not None:
        strURL = os.getenv("APIBASEURL")

    if len(sys.argv) > 1:
        strURL = sys.argv[1]

    if strURL == "":
        strURL = input("Please provide the URL to test: ")

    if strURL[-1:] != "/":
        strURL += "/"

    if os.getenv("TIMEOUT") != "" and os.getenv("TIMEOUT") is not None:
        if isInt(os.getenv("TIMEOUT")):
            iTimeOut = int(os.getenv("TIMEOUT"))
        else:
            LogEntry(
                "Invalid timeout, setting to defaults of {}".format(iTimeOut), 5)
    else:
        LogEntry("no timeout, setting to defaults of {}".format(iTimeOut), 5)

    if os.getenv("MINQUIET") != "" and os.getenv("MINQUIET") is not None:
        if isInt(os.getenv("MINQUIET")):
            iMinQuiet = int(os.getenv("MINQUIET"))
        else:
            LogEntry(
                "Invalid MinQuiet, setting to defaults of {}".format(iMinQuiet), 5)
    else:
        LogEntry("no MinQuiet, setting to defaults of {}".format(iMinQuiet), 5)

    if os.getenv("LOGLEVEL") != "" and os.getenv("LOGLEVEL") is not None:
        if isInt(os.getenv("LOGLEVEL")):
            iLogLevel = int(os.getenv("LOGLEVEL"))
            LogEntry("Loglevel set to {}".format(iLogLevel), 5)
        else:
            LogEntry(
                "Invalid LOGLEVEL, setting to defaults of {}".format(iLogLevel), 5)
    else:
        LogEntry("No LOGLEVEL, setting to defaults of {}".format(iLogLevel), 5)

    if os.getenv("PROXY") != "" and os.getenv("PROXY") is not None:
        strProxy = os.getenv("PROXY")
        dictProxies = {}
        dictProxies["http"] = strProxy
        dictProxies["https"] = strProxy
        LogEntry("Proxy has been configured for {}".format(strProxy), 5)
    else:
        dictProxies = {}

    strMethod = "get"
    dictHeader = {}
    dictHeader["Content-type"] = "application/json"
    dictHeader["Accept"] = "application/json"

    dictBody = {}

    APIResp = MakeAPICall(strURL, dictHeader, strMethod, dictBody)
    if APIResp[0]["Success"] == False:
        LogEntry(APIResp, 2)
    else:
        print("Response:\n{}".format(APIResp[1]))


if __name__ == '__main__':
    main()
