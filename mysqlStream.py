#pip install pymysql

import time
import sys
import subprocess
try:
  import pymysql
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'pymysql'])
finally:
    import pymysql

strServer = ""
strUser = ""
strPWD = ""
strInitialDB = ""


def SQLConn (strServer,strUser,strPWD,strInitialDB):
	try:
		# Open database connection
		return pymysql.connect(strServer,strUser,strPWD,strInitialDB)
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
		dbCursor = db.cursor(pymysql.cursors.SSCursor)
		# Execute the SQL command
		dbCursor.execute(strSQL)
		# Capture headers

		return dbCursor
	except pymysql.err.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}".format(err)
	except pymysql.err.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}".format(err)

strSQL = "select * from tblLogs limit 2000000;"
strHeaders = ""
iLineNum = 0
iTotalSec = 0
tStart=time.time()

db = SQLConn (strServer,strUser,strPWD,strInitialDB)
print ("Executing: {}".format(strSQL))
dbCursor = SQLQuery (strSQL,db)
tStop=time.time()
iElapseSec = tStop - tStart
iTotalSec += iElapseSec
tStart=time.time()
print ("Query complete, {} seconds".format(iElapseSec))
for temp in dbCursor.description:
	strHeaders += temp[0] + ","
if strHeaders[-1]==",":
	strHeaders = strHeaders[:-1]

for dbRow in dbCursor:
	strLine = ""
	# print ("Type: {} | {}".format(type(dbRow), dbRow))
	for strElement in dbRow:
		if strElement is None:
			strLine += ","
		else:
			strLine += "{},".format(strElement[0,100])
	if strLine[-1]==",":
		strLine = strLine[:-1]
	# print (strLine)
	iLineNum += 1
	print ("writen {} lines.".format(iLineNum),end="\r")

print ()
# disconnect from server
db.close()
tStop=time.time()
iElapseSec = tStop - tStart
iTotalSec += iElapseSec

print ("Done, {} seconds. Total Time {} seconds".format(iElapseSec,iTotalSec))