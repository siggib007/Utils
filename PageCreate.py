'''
Script to deploy new database table view to VMInfo web server
Author Siggi Bjarnason Copyright 2020

Following packages need to be installed as administrator
pip install pymysql

'''
# Import libraries
import sys
import os
import time
import platform
import pymysql
import shutil
# End imports

ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

def CleanExit(strCause):
  objLogOut.close()
  print ("objLogOut closed")
  sys.exit(9)

def LogEntry(strMsg,bAbort=False):
  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print (strMsg)
  if bAbort:
    CleanExit("")

def processConf():
  global strServer
  global strDBUser
  global strDBPWD
  global strInitialDB
  global strTableName
  global strFieldList
  global strHeaders
  global strFileName
  global strTitle
  global strMenu
  global strHomeDir
  global strSourceFile
  global strAction

  strAction = "Add"

  LogEntry ("Looking for configuration file: {}".format(strConf_File))
  if os.path.isfile(strConf_File):
    LogEntry ("Configuration File exists")
  else:
    LogEntry ("Can't find configuration file {}, make sure it is the same directory as this script".format(strConf_File))
    LogEntry("{} on {}: Exiting.".format (strScriptName,strScriptHost))
    objLogOut.close()
    sys.exit(9)

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
      strFullValue = strConfParts[1].strip()
      if strVarName == "Server":
         strServer = strValue
      if strVarName == "dbUser":
        strDBUser = strValue
      if strVarName == "dbPWD":
        strDBPWD = strFullValue
      if strVarName == "InitialDB":
        strInitialDB = strValue
      if strVarName == "TableName":
        strTableName = strValue
      if strVarName == "FieldList":
        strFieldList = strValue
      if strVarName == "TableHeader":
        strHeaders = strFullValue
      if strVarName == "FileName":
        strFileName = strValue
      if strVarName == "PageTitle":
        strTitle = strFullValue
      if strVarName == "MenuName":
        strMenu = strValue
      if strVarName == "HomeDirectory":
        strHomeDir = strFullValue
      if strVarName == "SourceFile":
        strSourceFile = strValue
      if strVarName == "Action":
        strAction = strValue

  strHomeDir = strHomeDir.replace("\\","/")
  if strHomeDir[-1:] != "/":
    strHomeDir+= "/"
  LogEntry ("Done processing configuration, moving on")

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

def DBClean(strText):
  if strText is None:
    return ""
  strTemp = str(strText)
  strTemp = strTemp.encode("ascii","ignore")
  strTemp = strTemp.decode("ascii","ignore")
  strTemp = strTemp.replace("\\","\\\\")
  strTemp = strTemp.replace("'","\"")
  return strTemp

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

def AddPage():
  # Defining the query to be shown on the page
  strSQL = ("INSERT INTO NetTools.tbldynamic (vcTableName,vcFieldList,vcHeaders, "
            " vcPageName,vcPageTitle) VALUES ('{}','{}','{}','{}','{}');".format(strTableName,
            strFieldList,strHeaders,strFileName,strTitle))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("While inserting into tbldynamic. Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully inserted into tbldynamic")

  # Adding new page to the Menu
  strSQL = ("INSERT INTO NetTools.tblmenu (vcTitle,vcLink,vcHeader) "
            " VALUES ('{}','{}','{}');".format(strMenu,strFileName,strMenu))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("While inserting into tblMenu Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully inserted into tblMenu")
  
  # Retrieving the menu ID of the new page
  strSQL = "SELECT iMenuID FROM NetTools.tblmenu WHERE vcLink = '{}';".format(strFileName)
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] == 0:
    LogEntry ("Page {} not found in tblmenu".format(strFileName))
  else:
    iMenuID = lstReturn[1][0][0]
    LogEntry ("MenuID: {}".format(iMenuID))

  # Calculate the next position number
  iMaxOrder = 0
  strSQL = "SELECT MAX(iMenuOrder) FROM NetTools.tblmenutype WHERE iMenuOrder < 30;"
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] == 0:
    LogEntry ("max not possible, how weird")
  else:
    iMaxOrder = lstReturn[1][0][0]
    LogEntry ("Max Menu Order: {}".format(iMaxOrder))
  iMaxOrder += 1

  # specifying the position of the new menu item
  strSQL = ("INSERT INTO NetTools.tblmenutype (iMenuID,vcMenuType,iMenuOrder,iSubOfMenu) "
            " VALUES ({},'head',{},0);".format(iMenuID,iMaxOrder))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("While inserting into tblmenutype Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully inserted into tblmenutype")

  # copy files from template file to the new file
  strSource = strHomeDir + strSourceFile
  strDest = strHomeDir + strFileName
  try:
    shutil.copyfile(strSource,strDest)
  except IOError as e:
    LogEntry("Failed to copy {} to {}. Error:{}".format(strSource,strDest,e))
  except Exception as err:
    LogEntry("Unexpected Error: {}".format(err))

  LogEntry("Successfully copied {} to {}.".format(strSource,strDest))

def RemovePage():
  # Retrieving the menu ID of the page to delete
  strSQL = "SELECT iMenuID FROM NetTools.tblmenu WHERE vcLink = '{}';".format(strFileName)
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] == 0:
    LogEntry ("Page {} not found in tblmenu".format(strFileName))
    iMenuID = -15
  else:
    iMenuID = lstReturn[1][0][0]
    LogEntry ("MenuID: {}".format(iMenuID))

  # Deleting Menu Positioning entry
  strSQL = ("DELETE FROM NetTools.tblmenutype WHERE iMenuID = {};".format(iMenuID))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("Attempting to delete from tblmenutype. Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully deleted from tblmenutype")

  # Deleting Menu entry
  strSQL = ("DELETE FROM NetTools.tblmenu WHERE iMenuID = {};".format(iMenuID))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("Attempting to delete from tblmenu. Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully deleted from tblmenu")

  # Deleting Menu entry
  strSQL = ("DELETE FROM NetTools.tbldynamic WHERE vcPageName = '{}';".format(strFileName))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry("Attempting to delete from tbldynamic. Records affected {}, expected 1 record affected".format(lstReturn[0]))
  else:
    LogEntry ("Successfully deleted from tbldynamic")

  # Delete the actual file
  strDest = strHomeDir + strFileName
  try:
    os.remove(strDest)
  except IOError as e:
    LogEntry("Failed to delete {}. Error:{}".format(strDest,e))
  except Exception as err:
    LogEntry("Unexpected Error: {}".format(err))
  else:
    LogEntry("File {} deleted".format(strFileName))


def main():
  global objLogOut
  global strConf_File
  global strScriptName
  global strScriptHost
  global dbConn

  strBaseDir = os.path.dirname(sys.argv[0])
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
  strConf_File = sys.argv[0][:iLoc] + ".ini"

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print ("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])
  strScriptHost = platform.node().upper()


  print ("This is a script to create a new dynamic database table on VMInfo. " 
          " This is running under Python Version {}".format(strVersion))
  print ("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print ("The time now is {}".format(dtNow))
  print ("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)

  processConf()
  dbConn = ""
  dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)

  if strAction == "DELETE":
    LogEntry ("Delete action specified")
    RemovePage()
  else:
    LogEntry ("Action specified is not DELETE in all caps, so doing an addition")
    AddPage()

  dtNow = time.asctime()
  LogEntry ("Completed at {}".format(dtNow))
  objLogOut.close()

if __name__ == '__main__':
    main()

