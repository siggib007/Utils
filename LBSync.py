'''
Script to copy data from the VS View tool and store it in our database
Author Siggi Bjarnason Copyright 2021

Following packages need to be installed as administrator
pip install requests
pip install jason

'''
# Import libraries
import sys
import os
import time
import requests
import platform
import json
import pymysql

# End imports

ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
strF5URL = "https://t2securityselfhelp.eng.t-mobile.com/f5Output.json"

#avoid insecure warning
requests.urllib3.disable_warnings()

def FetchTextFile (strURL):
  try:
    WebRequest = requests.get(strURL, headers={}, verify=False)
  except Exception as err:
    LogEntry ("Issue with API call. {}".format(err))
    return None

  if isinstance(WebRequest, requests.models.Response) == False:
    LogEntry ("response is unknown type")
    return None
  
  return WebRequest.text

def LogEntry(strMsg):
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
	print(strMsg)

def CleanExit(strCause):
  LogEntry("{} is exiting abnormally on {} {}".format(strScriptName,strScriptHost, strCause))
  objLogOut.close()
  print ("objLogOut closed")
  # if dbConn != "":
  #   dbConn.close()
  # print ("dbConn closed")  
  # if VSVdbConn != "":
  #   VSVdbConn.close()
  # print ("VSVdbConn closed")  
  sys.exit(9)

def DBClean(strText):
  if strText is None:
    return ""
  strTemp = strText.encode("ascii","ignore")
  strTemp = strTemp.decode("ascii","ignore")
  strTemp = strTemp.replace("\\","\\\\")
  strTemp = strTemp.replace("'","\"")
  return strTemp.strip()

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
  try:
    # Open database connection
    return pymysql.connect(strServer,strDBUser,strDBPWD,strInitialDB)
  except pymysql.err.InternalError as err:
    print ("Error: unable to connect: {}".format(err))
    sys.exit(5)
  except pymysql.err.OperationalError as err:
    print ("Operational Error: unable to connect: {}".format(err))
    sys.exit(5)
  except pymysql.err.ProgrammingError as err:
    print ("Programing Error: unable to connect: {}".format(err))
    sys.exit(5)

def SQLQuery (strSQL,db):
  try:
    # prepare a cursor object using cursor() method
    dbCursor = db.cursor()
    # Execute the SQL command
    dbCursor.execute(strSQL)
    # Count rows
    iRowCount = dbCursor.rowcount
    if strSQL[:6].lower() == "select" or strSQL[:4].lower() == "call":
      dbResults = dbCursor.fetchall()
    else:
      db.commit()
      dbResults = ()
    return [iRowCount,dbResults]
  except pymysql.err.InternalError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Internal Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.ProgrammingError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.OperationalError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.IntegrityError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Integrity Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.DataError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Data Error: unable to execute: {}\n{}".format(err,strSQL)

def ValidReturn(lsttest):
  if isinstance(lsttest,list):
    if len(lsttest) == 2:
      if isinstance(lsttest[0],int) and isinstance(lsttest[1],tuple):
        return True
      else:
        return False
    else:
      return False
  else:
    return False

def ValidateIP(strToCheck):
	Quads = strToCheck.split(".")
	if len(Quads) != 4:
		return False
	# end if

	for Q in Quads:
		try:
			iQuad = int(Q)
		except ValueError:
			return False
		# end try

		if iQuad > 255 or iQuad < 0:
			return False
		# end if

	return True

def FetchF5Data(strF5URL):
  objFileOut = open("c:/temp/VSViewOut.csv","w",1)
  strF5File = FetchTextFile(strF5URL)
  lstF5json = strF5File.splitlines()

  for strF5json in lstF5json:
    dictF5VS = json.loads(strF5json)

    strNodeName = dictF5VS["Node"]

    lstVSName = dictF5VS["VS"].split("/")
    if len(lstVSName) > 0:
      strVSName = lstVSName[len(lstVSName)-1]
    else:
      strVSName = dictF5VS["VS"]
    strVSName = strVSName.replace(",","|")

    lstVIP = dictF5VS["IP"].split("/")
    if len(lstVIP) > 0:
      strVIP = lstVIP[len(lstVIP)-1]
    else:
      strVIP = dictF5VS["IP"]
    strVIP = strVIP.replace(",","|")

    # if "SNATPool" in dictF5VS["SNAT"]:
    #   strSNAT = dictF5VS["SNAT"]["SNATPool"]
    # else:
    #   strSNAT = dictF5VS["SNAT"]
    # if isinstance(strSNAT,list):
    #   strSNAT = "|".join(strSNAT)
    # else:
    #   strSNAT = strSNAT.replace(",","|")

    if "IPs" in dictF5VS["Pool"]:
      lstPool = []
      if isinstance(dictF5VS["Pool"]["IPs"],list):
        for strMember in dictF5VS["Pool"]["IPs"]:
          lstMember = strMember.split("/")
          if len(lstMember) > 0:
            strIPPort = lstMember[len(lstMember)-1]
            lstIPPort = strIPPort.split(":")
            if len(lstIPPort) > 0:
              strIPAddr = lstIPPort[0]
            else:
              strIPAddr = strIPPort
            if ValidateIP(strIPAddr):
              lstPool.append (strIPAddr)
          else:
            if ValidateIP(strMember):
              lstPool.append (strMember)
        strPool = "|".join(lstPool)
      else:
        strPool = dictF5VS["Pool"]["IPs"]
    else:
      strPool = ""
   
    if isinstance(strPool,list):
      strPool = "|".join(strPool)
    else:
      strPool = strPool.replace(",","|")
    
    strOut = "{},{},{},{}\n".format(strNodeName,strVSName,strVIP,strPool)
    objFileOut.write(strOut)
    LogEntry ("Node: {} VS: {}".format(strNodeName,strVSName))

def FetchA10Data(strTableName):

  LogEntry ("Starting to process A10, fetching data from table {}".format(strTableName))
  strSQL = "SELECT * FROM {};".format(strTableName)
  lstReturn = SQLQuery (strSQL,VSVdbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("While selecting from {} Unexpected response: {}".format(strTableName,lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] == 0:
    LogEntry ("No data returned")
  else:
    LogEntry ("Retrived {} rows".format(lstReturn[0]))
  
  for dbRow in lstReturn[1]:
    strNodeName = dbRow[0]
    strVSName = dbRow[1]
    strVIP = dbRow[3]
    strVIPPort = dbRow[4]
    iLoc = strVIPPort.find(" ")
    strVIPPort = strVIPPort[:iLoc]
    strPool = dbRow[6]
    iLoc = strPool.find("-(")
    strPoolName = strPool[:iLoc]
    strPoolMember = strPool[iLoc+2:-1]
    lstPoolMember = strPoolMember.split(";")
    if strVSName == "":
      LogEntry("VS name for VIP {} on {} is blank".format(strVIP,strNodeName))
      if strPoolName != "":
        strVSName = strPoolName
      else:
        strVSName = "vs-"+strVIP+"_"+strVIPPort.replace(" ","-")
    LogEntry ("Processing Node: {} VS: {} Pool Name: {}".format(strNodeName,strVSName,strPoolName))
    updateDB(strNodeName,strVSName,strVIP,strVIPPort,"Virtual")
    iLineNum = 1
    for strMember in lstPoolMember:
      i1st = strMember.rfind("-")
      i2nd = strMember.find(":")
      iAlt = strMember.rfind("_")
      if i1st == -1:
        i1st = iAlt
      strIPAddr = strMember[i1st+1:i2nd]
      strIPPort = strMember[i2nd+1:]
      iLineNum += 1
      print ("Processed {} IPs for {}.".format(iLineNum,strVSName),end="\r")
      if strIPAddr != "":
        updateDB(strNodeName,strVSName,strIPAddr,strIPPort,"Member")
    LogEntry("Processed {} IPs for {}.".format(iLineNum,strVSName))

def updateDB(strNodeName,strVSName,strIPAddr,strIPPort,strType):
  strNodeName = DBClean(strNodeName)
  strVSName = DBClean(strVSName)
  strIPAddr = DBClean(strIPAddr)
  strIPPort = DBClean(strIPPort)
  strType = DBClean(strType)
  strSQL = ("INSERT INTO {}.{} (vcNodeName,vcVSName,vcIPaddr,"
            " vcPort,vcType) VALUES ('{}','{}','{}','{}','{}');".format(strDestDB,strDestTable,strNodeName,
            strVSName,strIPAddr,strIPPort,strType))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("While inserting IP addresses into {}.{}. Unexpected response: {}".format(strDestDB,
        strDestTable,lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("While inserting IP addresses into {}.{}. "
            "Records affected {}, expected 1 record affected".format(strDestDB,strDestTable,lstReturn[0]))
  # else:
  #   LogEntry ("Successfully inserted into ")

def processConf(strConf_File):

  LogEntry ("Looking for configuration file: {}".format(strConf_File))
  if os.path.isfile(strConf_File):
    LogEntry ("Configuration File exists")
  else:
    LogEntry ("Can't find configuration file {}, make sure it is the same directory "
      "as this script and named the same with ini extension".format(strConf_File))
    LogEntry("{} on {}: Exiting.".format (strScriptName,strScriptHost))
    objLogOut.close()
    sys.exit(9)

  strLine = "  "
  dictConfig = {}
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
      dictConfig[strVarName] = strValue
      if strVarName == "include":
        LogEntry ("Found include directive: {}".format(strValue))
        strValue = strValue.replace("\\","/")
        if strValue[:1] == "/" or strValue[1:3] == ":/":
          LogEntry("include directive is absolute path, using as is")
        else:
          strValue = strBaseDir + strValue
          LogEntry("include directive is relative path,"
            " appended base directory. {}".format(strValue))
        if os.path.isfile(strValue):
          LogEntry ("file is valid")
          objINIFile = open(strValue,"r")
          strLines += objINIFile.readlines()
          objINIFile.close()
        else:
          LogEntry ("invalid file in include directive")

  LogEntry ("Done processing configuration, moving on")
  return dictConfig

def main():
  global objLogOut
  global strScriptName
  global strScriptHost
  global strBaseDir
  global dbConn
  global VSVdbConn
  global strDestDB
  global strDestTable

  dbConn = ""
  VSVdbConn = ""

  strBaseDir = os.path.dirname(sys.argv[0])
  strBaseDir = strBaseDir.replace("\\", "/")
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\","/")
  strScriptName = os.path.basename(sys.argv[0])
  iLoc = sys.argv[0].rfind(".")
  strConf_File = sys.argv[0][:iLoc] + ".ini"
  
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
    strLogDir  = strBaseDir + "Logs/"
  if strLogDir[-1:] != "/":
    strLogDir += "/"

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print ("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  objLogOut = open(strLogFile, "w", 1)

  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])
  strScriptHost = platform.node().upper()

  print ("This is a script to fetch data in the VS View Tool and cache it in our DB. This is running under Python Version {}".format(strVersion))
  print ("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print ("The time now is {}".format(dtNow))
  print ("Logs saved to {}".format(strLogFile))

  dictConfig = processConf(strConf_File)

  if "F5URL" in dictConfig:
    strF5URL = dictConfig["F5URL"]
  else:
    CleanExit("No F5 URL")
  LogEntry ("Found F5 URL: {} ".format(strF5URL))

  if "VSVServer" in dictConfig:
    strVSVServer = dictConfig["VSVServer"]
  else:
    CleanExit("No VSVServer provided")

  if "VSVUser" in dictConfig:
    strVSVUser = dictConfig["VSVUser"]
  else:
    CleanExit("No VSVUser provided")

  if "VSVPWD" in dictConfig:
    strVSVPWD = dictConfig["VSVPWD"]
  else:
    CleanExit("No VSVPWD provided")

  if "VSVInitialDB" in dictConfig:
    strVSVInitialDB = dictConfig["VSVInitialDB"]
  else:
    CleanExit("No VSVInitialDB provided")

  if "Server" in dictConfig:
    strDBServer = dictConfig["Server"]
  else:
    CleanExit("No DB Server provided")

  if "dbUser" in dictConfig:
    strDBUser = dictConfig["dbUser"]
  else:
    CleanExit("No dbUser provided")

  if "dbPWD" in dictConfig:
    strDBPWD = dictConfig["dbPWD"]
  else:
    CleanExit("No dbPWD provided")

  if "InitialDB" in dictConfig:
    strInitialDB = dictConfig["InitialDB"]
  else:
    CleanExit("No InitialDB provided")

  if "VSVTable" in dictConfig:
    strVSVTable = dictConfig["VSVTable"]
  else:
    CleanExit("No VSVTable provided")

  if "DestDB" in dictConfig:
    strDestDB = dictConfig["DestDB"]
  else:
    CleanExit("No DestDB provided")

  if "DestTable" in dictConfig:
    strDestTable = dictConfig["DestTable"]
  else:
    CleanExit("No DestTable provided")

  dbConn = SQLConn (strDBServer,strDBUser,strDBPWD,strInitialDB)
  VSVdbConn = SQLConn (strVSVServer,strVSVUser,strVSVPWD,strVSVInitialDB)

  LogEntry ("Pulling data from {}.{}.{} and saving to {}.{}.{}".format(strVSVServer,
    strVSVInitialDB,strVSVTable,strDBServer,strDestDB,strDestTable))
  LogEntry ("First Truncating exiting data in {}.{}.{}".format(strDBServer,strDestDB,strDestTable))
  strSQL = "delete from {}.{};".format(strDestDB,strDestTable)
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    CleanExit ("While Truncating exiting data in {}.{}.{} got unexpected results: {}".format(strDBServer,
        strDestDB,strDestTable,lstReturn))
  else:
    LogEntry ("Deleted {} old records".format(lstReturn[0]))

  FetchA10Data(strVSVTable)

  # FetchF5Data(strF5URL)

  LogEntry ("{} completed successfully on {}".format(strScriptName, strScriptHost))
  objLogOut.close()
  dbConn.close()
  VSVdbConn.close()

if __name__ == '__main__':
  main()
