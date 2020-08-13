'''
Script to execute a MySQL Query and save the results to a CSV file
Author Siggi Bjarnason Copyright 2018
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install requests
pip install xmltodict
pip install pymysql

'''
# Import libraries
import sys
import requests
import os
import time
import xmltodict
import urllib.parse as urlparse
import pymysql
import platform
import json
# End imports

ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
iLoc = sys.argv[0].rfind(".")
strConf_File = sys.argv[0][:iLoc] + ".ini"
strBaseDir = os.path.dirname(sys.argv[0])
if strBaseDir != "":
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
strLogDir  = strBaseDir + "Logs"

if not os.path.exists (strLogDir) :
  os.makedirs(strLogDir)
  print ("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))


strScriptName = os.path.basename(sys.argv[0])
iLoc = strScriptName.rfind(".")
strLogFile = strLogDir + "/" + strScriptName[:iLoc] + ISO + ".log"
strRealPath = os.path.realpath(sys.argv[0])
strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])

strScriptHost = platform.node().upper()
if strScriptHost == "DEV-APS-RHEL-STD-A":
  strScriptHost = "VMSAWS01"

print ("This is a script to execute SQL command and write results to CSV file. This is running under Python Version {}".format(strVersion))
print ("Running from: {}".format(strRealPath))
now = time.asctime()
print ("The time now is {}".format(now))
print ("Logs saved to {}".format(strLogFile))
objLogOut = open(strLogFile,"w",1)
strFieldDelim = ","
strAtlDelim = ";"


def SendNotification (strMsg):
  dictNotify = {}
  dictNotify["token"] = strNotifyToken
  dictNotify["channel"] = strNotifyChannel
  dictNotify["text"]=strMsg[:199]
  strNotifyParams = urlparse.urlencode(dictNotify)
  strURL = strNotifyURL + "?" + strNotifyParams
  bStatus = False
  try:
    WebRequest = requests.get(strURL)
  except Exception as err:
    LogEntry ("Issue with sending notifications. {}".format(err))
  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry ("response is unknown type")
  else:
    dictResponse = json.loads(WebRequest.text)
    if isinstance(dictResponse,dict):
      if "ok" in dictResponse:
        bStatus = dictResponse["ok"]
        LogEntry ("Successfully sent slack notification\n{} ".format(strMsg))
    if not bStatus or WebRequest.status_code != 200:
      LogEntry ("Problme: Status Code:[] API Response OK={}")
      LogEntry (WebRequest.text)

def CleanExit(strCause):
  if dbConn !="":
    dbConn.close()

  SendNotification("{} is exiting abnormally on {} {}".format(strScriptName,strScriptHost, strCause))
  objLogOut.close()
  sys.exit(9)

def LogEntry(strMsg,bAbort=False):
  strTemp = ""

  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print (strMsg)
  if bAbort:
    SendNotification("{} on {}: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    CleanExit("")

def processConf():
  global strServer
  global strDBUser
  global strDBPWD
  global strInitialDB
  global strOutFileName
  global strSQL
  global strNotifyURL
  global strNotifyToken
  global strNotifyChannel
  global strFieldDelim
  global strAtlDelim

  if os.path.isfile(strConf_File):
    LogEntry ("Configuration File exists")
  else:
    LogEntry ("Can't find configuration file {}, make sure it is the same directory as this script".format(strConf_File),True)

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
      strConfParts = strLine.split("=")
      if strVarName == "Server":
        strServer = strValue
      if strVarName == "dbUser":
        strDBUser = strValue
      if strVarName == "dbPWD":
        strDBPWD = strValue
      if strVarName == "InitialDB":
        strInitialDB = strValue
      if strVarName == "Query":
        iLoc = strLine.find("=")+1
        strSQL = strLine[iLoc:]
      if strVarName == "CSVFileName":
        strOutFileName = strValue
      if strVarName == "NotificationURL":
        strNotifyURL = strValue
      if strVarName == "NotifyChannel":
        strNotifyChannel = strValue
      if strVarName == "NotifyToken":
        strNotifyToken = strValue
      if strVarName == "FieldSeperate":
        strFieldDelim = strValue
      if strVarName == "AltDelim":
        strAtlDelim = strValue

  LogEntry ("Done processing configuration, moving on")

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
  try:
    # Open database connection
    return pymysql.connect(strServer,strDBUser,strDBPWD,strInitialDB)
  except pymysql.err.InternalError as err:
    LogEntry ("Error: unable to connect: {}".format(err),True)
  except pymysql.err.OperationalError as err:
    LogEntry ("Operational Error: unable to connect: {}".format(err),True)
  except pymysql.err.ProgrammingError as err:
    LogEntry ("Programing Error: unable to connect: {}".format(err),True)

def SQLQuery (strSQL,db):
  try:
    # prepare a cursor object using cursor() method
    print ("getting a cursor")
    dbCursor = db.cursor(pymysql.cursors.SSCursor)
    # Execute the SQL command
    print ("Execute query {}".format(strSQL))
    dbCursor.execute(strSQL)
    print ("returning...")
    return dbCursor
  except pymysql.err.InternalError as err:
    return "Internal Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except pymysql.err.ProgrammingError as err:
    return "Programing Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except pymysql.err.OperationalError as err:
    return "Programing Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except pymysql.err.IntegrityError as err:
    return "Integrity Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except pymysql.err.DataError as err:
    return "Data Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except pymysql.err.InterfaceError as err:
    return "Interface Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))

def isInt (CheckValue):
  # function to safely check if a value can be interpreded as an int
  if isinstance(CheckValue,int):
    return True
  elif isinstance(CheckValue,str):
    if CheckValue.isnumeric():
      return True
    else:
      return False
  else:
    return False

def ConvertFloat (fValue):
  if isinstance(fValue,(float,int,str)):
    try:
      fTemp = float(fValue)
    except ValueError:
      fTemp = "NULL"
  else:
    fTemp = "NULL"
  return fTemp

def QDate2DB(strDate):
  strTemp = strDate.replace("T"," ")
  return strTemp.replace("Z","")

def DBClean(strText):
  if strText is None:
    return ""
  strTemp = strText.encode("ascii","ignore")
  strTemp = strTemp.decode("ascii","ignore")
  strTemp = strTemp.replace("\\","\\\\")
  strTemp = strTemp.replace("'","\\'")
  return strTemp

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput


dbConn = ""
strHeaders = ""
iLineNum = 1
processConf()
LogEntry ("Opening {} to save results".format(strOutFileName))
if os.path.isfile(strOutFileName):
  strResponse = getInput("{} already exists, overwrite yes/no (default no): ".format(strOutFileName))
  if strResponse == "":
    strResponse = "no"
  if strResponse[0].lower() == 'y':
    objFileOut = open(strOutFileName,"w")
  else:
    LogEntry ("OK I'm not overwriting, exiting so you can adjust the configuration file")
    objLogOut.close()
    sys.exit()
else:
  objFileOut = open(strOutFileName,"w")
if strAtlDelim == "\\t" or strAtlDelim == "^t" or strAtlDelim == "tab":
  strAtlDelim = "\t"

if strFieldDelim == "\\t" or strFieldDelim == "^t" or strFieldDelim == "tab":
  strFieldDelim = "\t"
  LogEntry ("Field seperater is set as tab")
else:
  LogEntry ("Field seperater is set as {}".format(strFieldDelim))
dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
LogEntry("Database connection established, executing the query : {}".format(strSQL))
tStart=time.time()
dbCursor = SQLQuery (strSQL,dbConn)
print ("Query complete. Now processing cursor")
if isinstance(dbCursor,str):
  LogEntry("Results is only the following string: {}".format(dbCursor),True)
# iRowCount = dbCursor.rowcount
# Capture headers
for temp in dbCursor.description:
  strHeaders += temp[0] + strFieldDelim
if strHeaders[-1]==strFieldDelim:
  strHeaders = strHeaders[:-1]
# LogEntry ("Fetched {} rows".format(iRowCount))

objFileOut.write ("{}\n".format(strHeaders))
for dbRow in dbCursor:
  strLine = ""
  for strField in dbRow:
    if strField is None:
      strTemp = ""
    else:
      strTemp = str(strField).replace(strFieldDelim,strAtlDelim)
      strTemp = strTemp.replace("\n"," ")
      strTemp = strTemp.replace("\r"," ")
      strTemp = strTemp.replace("\t"," ")
    strLine += strTemp + strFieldDelim
  if strLine[-1] == strFieldDelim:
    strLine = strLine[:-1]
  objFileOut.write ("{}\n".format(strLine))
  iLineNum += 1
  print ("writen {} lines.".format(iLineNum),end="\r")

print()
LogEntry("Results written to {}".format(strOutFileName))
tStop=time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
now = time.asctime()
LogEntry ("Completed at {}".format(now))
LogEntry ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,iHours,iMin,iSec))
SendNotification ("{} completed successfully on {}".format(strScriptName, strScriptHost))
dbConn.close()
objFileOut.close()