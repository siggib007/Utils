'''
Script that reads in a csv of session details
Creates ssh configuration file

Author Siggi Bjarnason Dec 2023
Copyright 2023 Siggi Bjarnason

'''
# Import libraries
import os
import time
import sys
import csv
import platform

iLogLevel = 5  # How much logging should be done. Level 10 is debug level, 0 is none
strConfFile = "C:/Users/siggib/.ssh/config"

def getInput(strPrompt):
  if sys.version_info[0] > 2:
    return input(strPrompt)
  else:
    return raw_input(strPrompt)

def CleanExit(strCause):
  """
  Handles cleaning things up before unexpected exit in case of an error.
  Things such as closing down open file handles, open database connections, etc.
  Logs any cause given, closes everything down then terminates the script.
  Remember to add things here that need to be cleaned up
  Parameters:
    Cause: simple string indicating cause of the termination, can be blank
  Returns:
    nothing as it terminates the script
  """
  if strCause != "":
    strMsg = "{} is exiting abnormally on {} because: {}".format(
        strScriptName, strScriptHost, strCause)
    strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
    objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
    print(strMsg)

  if objFileOut is None:
    objLogOut.write("Outfile not open")
  else:
    objFileOut.close()
    objLogOut.write("Outfile closed")

  objLogOut.close()
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

def GetFileHandle(strFileName, strperm):
  """
  This wraps error handling around standard file open function
  Parameters:
    strFileName: Simple string with filename to be opened
    strperm: single character string, usually w or r to indicate read vs write. other options such as "a" are valid too.
  Returns:
    File Handle object
  """
  dictModes = {}
  dictModes["w"] = "writing"
  dictModes["r"] = "reading"
  dictModes["a"] = "appending"
  dictModes["x"] = "opening"

  cMode = strperm[0].lower()

  try:
    objFileHndl = open(strFileName, strperm, encoding='utf8')
    return objFileHndl
  except PermissionError:
    print("unable to open output file {} for {}, "
              "permission denied.".format(strFileName, dictModes[cMode]))
    return("Permission denied")
  except FileNotFoundError:
    print("unable to open output file {} for {}, "
              "Issue with the path".format(strFileName, dictModes[cMode]))
    return("key not found")

def createSession(dictSession):
  """
  This handles the actual creation of configuration item in the configuration file
  Parameters:
    dictSession: dictionary of the session elements: Path, Hostname, User, Cred, FW and Port
  Returns:
    string with error or success
  """

  if "Label" not in dictSession:
    return "No Label"
  if dictSession["Label"] == "" or dictSession["Label"] is None:
    return "No Label"

  if "Address" in dictSession:
    strAddress = dictSession["Address"] or ""
  else:
    strAddress = ""
  if strAddress == "":
     return "No Address"
  if "Username" in dictSession:
    strUser = dictSession["Username"]  or ""
  else:
    strUser = ""
  if "Jump" in dictSession:
    strJump = dictSession["Jump"]  or ""
  else:
    strJump = ""
  if "Port" in dictSession:
    if isInt(dictSession["Port"]):
      iPort = int(dictSession["Port"])
    else:
      iPort = 22
  else:
    iPort = 22

  strOut = "\nHost " + dictSession["Label"] + "\n"
  strOut += "  HostName " + strAddress + "\n"
  if strUser != "":
    strOut += "  User " + strUser + "\n"
  if iPort != 22:
    strOut += "  Port " + str(iPort) + "\n"
  if strJump != "":
    strOut += "  ProxyCommand ssh -W %h:%p " + strJump + "\n"
  objFileOut.write (strOut)
  return "success!"

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

def main():
  global objLogOut
  global objFileOut
  global strScriptName
  global strScriptHost

  strCSVName = ""
  objFileOut = None

  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
  lstSysArg = sys.argv
  iSysArgLen = len(lstSysArg)

  strBaseDir = os.path.dirname(os.path.abspath(__file__))
  strRealPath = os.path.realpath(sys.argv[0])
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]

  strBaseDir = strBaseDir.replace("\\", "/")

  if strBaseDir[-1:] != "/":
      strBaseDir += "/"

  strLogDir = strBaseDir + "Logs/"

  if not os.path.exists(strLogDir):
      print("Attempting to create log directory: {}".format(strLogDir))
      os.makedirs(strLogDir)

  strScriptName = os.path.basename(os.path.abspath(__file__))
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  strScriptHost = platform.node().upper()
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2])

  print("This is a script to create an ssh configuration file based on an input csv file. "
        "This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print("The time now is {}".format(dtNow))
  print("Logs saved to {}".format(strLogFile))

  tmpObj = GetFileHandle(strLogFile,"w")
  if isinstance(tmpObj,str):
    CleanExit(tmpObj)
  else:
    objLogOut = tmpObj
  LogEntry("Starting up",3)

  if iSysArgLen > 1:
    strCSVName = lstSysArg[1]
    LogEntry("Processing input file named : {}".format(strCSVName), 4)
  else:
    if strCSVName == "":
      strCSVName = getInput("Please provide full path and filename for the CSV file to be imported: ")

  if strCSVName == "":
    print("No filename provided unable to continue")
    sys.exit()

  strCSVName = strCSVName.replace("\\", "/")
  if "/" not in strCSVName:
    strCSVName = strBaseDir + strCSVName

  if os.path.isfile(strCSVName):
    print("OK found {}".format(strCSVName))
  else:
    print("Can't find CSV file {}".format(strCSVName))
    sys.exit(4)

  tmpObj = GetFileHandle(strCSVName,"r")
  if isinstance(tmpObj,str):
    CleanExit(tmpObj)
  else:
    objCSVIn = tmpObj

  tmpObj = GetFileHandle(strConfFile,"w")
  if isinstance(tmpObj,str):
    CleanExit(tmpObj)
  else:
    objFileOut = tmpObj
  LogEntry("{} created".format(strConfFile),4)

  objReader = csv.DictReader(objCSVIn)
  for dictTemp in objReader:
    LogEntry("Working on {} - {} - jump: {}".format(dictTemp["Label"],dictTemp["Address"],dictTemp["Jump"]),4)
    strRet = createSession(dictTemp)
    LogEntry("create session returned: {}".format(strRet),4)

  # Closing thing out
  LogEntry("Done!", 1)
  objLogOut.close()
  objFileOut.close()


if __name__ == '__main__':
    main()
