'''
Script to convert json file to CSV
Version: 3.6
Author Siggi Bjarnason Copyright 2019

'''
# Import libraries
import sys
import os
import time
import json

try:
	import tkinter as tk
	from tkinter import filedialog
	btKinterOK = True
except:
	print ("Failed to load tkinter, CLI only mode.")
	btKinterOK = False
# End imports

# Initialize stuff
strJSONfile = ""


#Start doing stuff
print ("This is a script to convert json file to a CSV file. This is running under Python Version {0}.{1}.{2}".format(
	sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

def getInput(strPrompt):
	if sys.version_info[0] > 2 :
		return input(strPrompt)
	else:
		print("Please upgrade to python 3 or greater")
		sys.exit()
# end getInput

def ConvertJson2CSV(Itm2Bconverted):
	if isinstance(Itm2Bconverted,dict):
		for strKey in Itm2Bconverted.keys():
			if isinstance(Itm2Bconverted[strKey],list):
				Write2CSV(Itm2Bconverted[strKey],strKey)
			elif isinstance(Itm2Bconverted[strKey],dict):
				Write2CSV([Itm2Bconverted[strKey]],"")
			else:
				print ("{} is a {}, writing to CSV file as is.".format(strKey,type(Itm2Bconverted[strKey])))
				objFileOut.write ("\n{},{}\n".format(strKey,Itm2Bconverted[strKey]))
	elif isinstance(Itm2Bconverted,list):
		Write2CSV(Itm2Bconverted,"")

def CSVClean (str2Clean):
	strTemp = str(str2Clean)
	strTemp = strTemp.replace(",","|")
	return strTemp

def Write2CSV(lstItem,strHeader):
	strLine = ""
	lstHeaders = []
	if strHeader != "":
		print ("Item is a section named {}".format(strHeader))
	objFileOut.write("\n{}\n".format(strHeader))
	print ("item is a {} and has {} elements".format(type(lstItem),len(lstItem)))
	for outitem in lstItem:
		for InnerItem in outitem.keys():
			if InnerItem not in lstHeaders:
				lstHeaders.append(InnerItem)
	for strHeadKey in lstHeaders:
		strLine += strHeadKey + ","
	strLine = strLine[:-1]
	objFileOut.write ("{}\n".format(strLine))
	for dictItem in lstItem:
		strLine = ""
		for strHeadKey in lstHeaders:
			if strHeadKey in dictItem:
				if isinstance(dictItem[strHeadKey],dict):
					if len(dictItem[strHeadKey]) == 1:
						strLine += "{},".format(CSVClean(dictItem[strHeadKey]))
					else:
						strLine += "dictionary with {} items,".format(len(dictItem[strHeadKey]))
				elif isinstance(dictItem[strHeadKey],list):
					if len(dictItem[strHeadKey]) == 1:
						if isinstance(dictItem[strHeadKey][0],(list,dict)):
							strLine += "{} with {} elements,".format(type(dictItem[strHeadKey][0]),len(dictItem[strHeadKey][0]))
						else:
							strLine += "{},".format(CSVClean(dictItem[strHeadKey][0]))
					else:
						strLine += "list with {} items,".format(len(dictItem[strHeadKey]))
				else:
					strLine += "{},".format(CSVClean(dictItem[strHeadKey]))
			else:
				strLine += ","
		strLine = strLine[:-1]
		# print (strLine)
		objFileOut.write(strLine + "\n")

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
	strJSONfile = sa[1]

if strJSONfile == "":
	if btKinterOK:
		print ("File name to be imported is missing. Opening up a file open dialog box, please select the file you wish to import.")
		root = tk.Tk()
		root.withdraw()
		strJSONfile = filedialog.askopenfilename(title = "Select the json file",filetypes = (("json files","*.json"),("Text files","*.txt"),("all files","*.*")))
	else:
		strJSONfile = getInput("Please provide full path and filename for the json file to be imported: ")

if strJSONfile == "":
	print ("No filename provided unable to continue")
	sys.exit()

if os.path.isfile(strJSONfile):
	print ("OK found {}".format(strJSONfile))
else:
	print ("Can't find json file {}".format(strJSONfile))
	sys.exit(4)

iLoc = strJSONfile.rfind(".")
strOutFile = strJSONfile[:iLoc] + ".csv"

print ("writing output to {}".format(strOutFile))

objFileOut = open(strOutFile,"w")

with open(strJSONfile,"r") as objFilejson:
	dictFile = json.load(objFilejson)

print ("File loaded, result is a: {}".format(type(dictFile)))
if isinstance(dictFile,(list,dict)):
	ConvertJson2CSV(dictFile)
else:
	print("file did not load as a json dictionary or list, can't process")

print ("All Done :-D")
