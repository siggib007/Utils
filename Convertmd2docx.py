'''
Script reads a text file with a list of files,
combines files into a single file, fixes few things
and converts formats using pandocs.
Input file needs to be in the same directory as the files it is listing
Paths require linux convention with /, windows convention of \\ will bomb.
Requires pandocs installed from https://pandoc.org/installing.html.
Read pandocs document regarding possible values for strOrigionalFormat and strConvert2
This script was written for python 3 and tested under Python Version 3.6.5
Author Siggi Bjarnason Copyright 2019
Website https://www.supergeek.us/

'''
import sys
import os
import time
import subprocess as proc

# Defining stuff
strFilein = "C:/book/source/manuscript/Book.txt"
strOutPath = "C:/book/"
strOutFile = "OnlineSafety.md"
strConvertedFileName = "OnlineSafety.docx"
strOrigionalFormat = "markdown"
strConvert2 = "docx"

lstStr2Delete = []
lstStr2Delete.append("{frontmatter}")
lstStr2Delete.append("{book: true, sample: true}")
lstStr2Delete.append("{mainmatter}")
lstStr2Delete.append("{book: true, sample: false}")
lstStr2Delete.append("{backmatter}")

dictReplacements = {}
dictReplacements["]("] = "](source/manuscript/resources/"


# Doing stuff

print ("This is a script to combine bunch of files into a single markdown file, then convert it to docx."
	"\n This is running under Python Version {0}.{1}.{2}".format(
	sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

if os.path.isfile(strFilein) :
	print ("Found input file, good to go")
else:
	print ("could not find input file. Please validate the strFilein variable. exiting")
	sys.exit()

if not os.path.exists (strOutPath) :
  os.makedirs(strOutPath)
  print ("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(strOutPath))

if strOutPath[-1:] != "/":
	strOutPath += "/"

strFullOutFile = strOutPath + strOutFile
print ("Output will be saved to {}".format(strFullOutFile))
strFullconverted = strOutPath + strConvertedFileName
print ("converted file will be written to {}".format(strFullconverted))
iLoc = strFilein.rfind("/")
strInPath = strFilein[:iLoc+1]
print ("Base path is: {}".format(strInPath))
objFileIn  = open(strFilein,"r")
objFileOut = open(strFullOutFile,"w")
strLine = "nada"

while strLine:
	strLine = objFileIn.readline()
	if strLine.strip() != "":
		if os.path.isfile(strInPath + strLine.strip()) :
			objtmpIn = open(strInPath + strLine.strip(),encoding='utf-8')
			strFileText = objtmpIn.read()
			strFileText = strFileText.encode("ascii","ignore")
			strFileText = strFileText.decode("ascii","ignore")
			for strFind in lstStr2Delete:
				strFileText = strFileText.replace(strFind,"")
			for strReplace in dictReplacements:
				strFileText = strFileText.replace(strReplace,dictReplacements[strReplace])
			objFileOut.write (strFileText+"\n")
			print ("{} is a done!".format(strInPath + strLine.strip()))
		else:
			print ("{} is NOT a valid file!".format(strInPath + strLine.strip()))
	else:
		pass
		# print ("blank line")


strCmdLine = "pandoc {} -f {} -t {} -o {}".format(strOutFile,strOrigionalFormat,strConvert2,strFullconverted)
print ("executing {}".format(strCmdLine))
proc.Popen(strCmdLine)
print ("All done !!! :-D")