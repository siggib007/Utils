'''
Script to import CSV files
Version: 3.6
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install pymysql

'''
# Import libraries
import sys
import os
import string
import time
import pymysql
import csv

try:
	import tkinter as tk
	from tkinter import filedialog
	btKinterOK = True
except:
	print ("Failed to load tkinter, CLI only mode.")
	btKinterOK = False
# End imports

#Default values, overwrite these in the ini file
bTruncateTable = True   # Truncate the table prior to insert
bConvertBool = True     # Convert strings true/false into 1 and 0 for insert into database boolean field.
bRecordStats = True     # Log events and record stats in the database.

# Initialize stuff
strDelim = ","          # what is the field seperate in the input file
strCSVName = ""
iLoc = sys.argv[0].rfind(".")
strConf_File = sys.argv[0][:iLoc] + ".ini"
strScriptName = os.path.basename(sys.argv[0])
localtime = time.localtime(time.time())
gmt_time = time.gmtime()
iGMTOffset = (time.mktime(localtime) - time.mktime(gmt_time))/3600

#Start doing stuff
print ("This is a script to import csv files. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

if os.path.isfile(strConf_File):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file {}, make sure it is the same directory as this script".format(strConf_File))
	sys.exit(4)

strLine = "  "
print ("Reading in configuration")
objINIFile = open(strConf_File,"r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	iCommentLoc = strLine.find("#")
	if iCommentLoc > -1:
		strLine = strLine[:iCommentLoc].strip()
	else:
		strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		strVarName = strConfParts[0].strip()
		strValue = strConfParts[1].strip()
		if strVarName == "APIBaseURL":
			strBaseURL = strValue
		if strVarName == "APIRequestHeader":
			strHeadReq = strValue
		if strVarName == "QUserID":
			strUserName = strValue
		if strVarName == "QUserPWD":
			strPWD = strValue
		if strVarName == "Server":
			strServer = strValue
		if strVarName == "dbUser":
			strDBUser = strValue
		if strVarName == "dbPWD":
			strDBPWD = strValue
		if strVarName == "InitialDB":
			strInitialDB = strValue
		if strVarName == "TableName":
			strTableName = strValue
		if strVarName == "TruncateTable":
			bTruncateTable = strValue.lower() == "true"
		if strVarName == "ConvertBool":
			bConvertBool = strValue.lower() == "true"
		if strVarName == "RecordStats":
			bRecordStats = strValue.lower() == "true"
		if strVarName == "FieldDelim":
			strDelim = strValue
		if strVarName == "CSVFileName":
			strCSVName = strValue
		if strVarName == "DateTimeFormat":
			strDTFormat = strValue

strScriptName = strScriptName[:-3] + "-" + strTableName

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
	strCSVName = sa[1]

if strCSVName == "":
	if btKinterOK:
		print ("File name to be imported is missing. Opening up a file open dialog box, please select the file you wish to import.")
		root = tk.Tk()
		root.withdraw()
		strCSVName = filedialog.askopenfilename(title = "Select CSV file",filetypes = (("CSV files","*.csv"),("Text files","*.txt"),("all files","*.*")))
	else:
		strCSVName = getInput("Please provide full path and filename for the CSV file to be imported: ")

if strCSVName == "":
	print ("No filename provided unable to continue")
	sys.exit()

if os.path.isfile(strCSVName):
	print ("OK found {}".format(strCSVName))
else:
	print ("Can't find CSV file {}".format(strCSVName))
	sys.exit(4)

def LogEntry(strMsg):
	if bRecordStats:
		strTemp = ""
		strDBMsg = DBClean(strMsg)
		strSQL = "INSERT INTO tblLogs (dtTimestamp, vcScriptName, vcLogEntry) VALUES (now(),'{}',{});".format(strScriptName,strDBMsg)
		if dbConn !="":
			lstReturn = SQLQuery (strSQL,dbConn)
			if not ValidReturn(lstReturn):
				strTemp = ("   Unexpected issue inserting log entry to the database: {}\n{}".format(lstReturn,strSQL))
			elif lstReturn[0] != 1:
				strTemp = ("   Records affected {}, expected 1 record affected when inserting log entry to the database".format(lstReturn[0]))
		else:
			strTemp = ". Database connection not established yet"

		strMsg += strTemp
	print (strMsg)

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
		if strSQL[:6].lower() == "select" or strSQL[:4].lower() == "call" or strSQL[:4].lower() == "show" or strSQL[:8].lower() == "describe":
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
	except Exception as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "unknown Error: unable to execute: {}\n{}".format(err,strSQL)

def DBClean(strText):
	if strText.strip() == "":
		return "NULL"
	elif isinstance(strText,int):
		return int(strText)
	elif isinstance(strText,float):
		return float(strText)
	else:
		strTemp = strText.encode("ascii","ignore")
		strTemp = strTemp.decode("ascii","ignore")
		strTemp = strTemp.replace("\\","\\\\")
		strTemp = strTemp.replace("'","\\'")
		try:
			strTemp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.mktime(time.strptime(strTemp,strDTFormat))))
		except ValueError:
			pass
		if bConvertBool:
			if strTemp.lower() == "false":
				strTemp = "0"
			if strTemp.lower() == "true":
				strTemp = "1"
		return "'" + strTemp + "'"

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

lstFields = []
dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
LogEntry("Starting the import of {} into database on {}".format(strCSVName,strServer))
LogEntry("Date Time format set to: {}".format(strDTFormat))

if bRecordStats:
	strSQL = "INSERT INTO tblScriptExecuteList (vcScriptName,dtStartTime,iGMTOffset) VALUES('{}',now(),{});".format(strScriptName,iGMTOffset)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		sys.exit(9)
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	strSQL = "select iExecuteID from tblScriptExecuteList where dtStartTime = (select max(dtStartTime) from tblScriptExecuteList where vcScriptName = '{}');".format(strScriptName)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		sys.exit(9)
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
		iEntryID = -10
	else:
		iEntryID = lstReturn[1][0][0]

	LogEntry("Recorded start entry, ID {}".format(iEntryID))

strSQL = "show columns from {};".format(strTableName)
lstReturn = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstReturn):
	print ("Unexpected: {}".format(lstReturn))
	sys.exit(9)
else:
	if lstReturn[0] > 0:
		for FieldName in lstReturn[1]:
			lstFields.append(FieldName[0])

if len(lstFields)>0:
	iFieldCount = len(lstFields)
	if bTruncateTable:
		LogEntry ("Truncating exiting table")
		strSQL = "delete from {};".format(strTableName)
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("Unexpected: {}".format(lstReturn))
			sys.exit(9)
		else:
			LogEntry ("Deleted {} old records".format(lstReturn[0]))
else:
	LogEntry ("{} has no fields, aborting.".format(lstFields))
	sys.exit()

with open(strCSVName,newline="") as hCSV:
	myReader = csv.reader(hCSV, delimiter=strDelim)
	lstLine = next(myReader)
	if len(lstFields) != len(lstLine):
		LogEntry ("Houston we have a problem. The field counts don't line up and I'm not programed to handle that, aborting.")
		sys.exit()
	print ("CSV Headers: {}".format(lstLine))
	x=0
	print ("CSV Header: <> Database Field")
	for FieldName in lstFields:
		print ("{} <> {}".format(lstLine[x],FieldName))
		x += 1

	LogEntry ("Starting import...")

	for lstLine in myReader :
		x=0
		strSQL = "insert into {} (".format(strTableName)
		for Field in lstFields :
			strSQL += Field + ","
		strSQL = strSQL[:-1] + ") values ("
		for csvValue in lstLine:
			strSQL +=  DBClean(csvValue) + ","
			x += 1
			if x > iFieldCount-1:
				break
		if len(lstLine) > len(lstFields):
			LogEntry("\nLine {} {} has {} values, expecting {}. Dropping extra values".format(myReader.line_num,lstLine,len(lstLine),iFieldCount))
		if len(lstLine) < len(lstFields):
			LogEntry("\nLine {} {} has {} values, expecting {}. Padding missing".format(myReader.line_num,lstLine[0],len(lstLine),iFieldCount))
			for i in list(range(x,iFieldCount)):
				strSQL += "NULL,"
		strSQL = strSQL[:-1]+");"
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("\nLine {} Unexpected return: {}".format(myReader.line_num, lstReturn))
			sys.exit(9)
		else:
			if lstReturn[0] != 1:
				print ("\n{} row inserted, line {}".format(lstReturn[0],myReader.line_num))
		if bRecordStats:
			strSQL = "update tblScriptExecuteList set dtStopTime=now(), bComplete=0, iRowsUpdated={} where iExecuteID = {} ;".format(myReader.line_num,iEntryID)
			lstReturn = SQLQuery (strSQL,dbConn)
			if not ValidReturn(lstReturn):
				LogEntry ("Unexpected: {}".format(lstReturn))
			elif lstReturn[0] != 1:
				LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

		print ("imported {} records...".format(myReader.line_num),end="\r")

LogEntry ("\n{} records imported. Except as noted above all records imported successfully".format(myReader.line_num))
if bRecordStats:
	LogEntry("Updating completion entry")
	strSQL = "update tblScriptExecuteList set dtStopTime=now(), bComplete=1, iRowsUpdated={} where iExecuteID = {} ;".format(myReader.line_num,iEntryID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
LogEntry ("All Done!")