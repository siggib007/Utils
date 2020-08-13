'''
IP Calculator
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is a command line IP address subnet calculator for IPv4
Execute the script and pass in an ip address as a parameter
Any of these three formats are valid
IPCalc.py 218.55.213.56/27
IPCalc.py 218.55.213.56 255.255.255.224
IPCalc.py 218.55.213.56 0.0.0.31

IPCalc.py -h will print out full usage instructions.

The script will output
- mask in other two formats
- host count
- Subnet IP
- broadcast IP
- WHOIS details from ARIN

Following packages need to be installed as administrator
pip install requests
pip install jason

'''
# Import libraries
import sys
import requests
import json
import os
import string
# End imports

#Global Variables/Constants
bWhoisQuery=True
iLoc =sys.argv[0].rfind('\\')
strScriptName = sys.argv[0][iLoc+1:]
strScriptPath = sys.argv[0][:iLoc]
Hex_Digits = string.hexdigits
Hex_set = set(Hex_Digits)

# Function section

# Function BinMask2Dec
# Convert bitmask to Decimal
# Takes in an integer from 1 to 32 as mask reprisenting number of bits in the subnet
# converts that to a decimal number that can be converted lated to a dotted decimal
def BitMask2Dec(iBitMask):
	if iBitMask < 0 or iBitMask > 32:
		return 0
	# end if
	iBitLeft = 32 - iBitMask
	strBinMask=("1"*iBitMask) + ("0"*iBitLeft)
	return int(strBinMask,2)
# End Function

# Function DotDecGen
# Takes a decimal value and converts it to a dotted decimal string
# Number has to be greater than 0 and 32 bits.
def DotDecGen (iDecValue):
	if iDecValue < 1 or iDecValue > 4294967295:
		return "Invalid"
	# end if

	# Convert decimal to hex
	HexValue = hex(iDecValue)

	#Ensure the results is 8 hex digits long.
	#IP's lower than 16.0.0.0 have trailing 0's that get trimmed off by hex function
	HexValue = "0"*8+HexValue[2:]
	HexValue = "0x"+HexValue[-8:]
	# Convert Hex to dot dec
	strTemp = str(int(HexValue[2:4],16)) + "." + str(int(HexValue[4:6],16)) + "."
	strTemp = strTemp + str(int(HexValue[6:8],16)) + "." + str(int(HexValue[8:10],16))
	return strTemp
# End Function


# Function ValidateIP
# Takes in a string and validates that it follows standard IP address format
# Should be four parts with period deliniation
# Each nubmer should be a number from 0 to 255.
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
# end function

# Function DotDec2Int
# Takes in a string like an IP address or a mask
# returns decimal integer representation of that string
def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		return 0
	# end if

	Quads = strValue.split(".")
	for Q in Quads:
		QuadHex = hex(int(Q))
		strwp = "00"+ QuadHex[2:]
		strHex = strHex + strwp[-2:]
	# next

	return int(strHex,16)
# end function

# Function ValidMask
# Takes in a string containing a dotted decimal mask
# validates that it is valid, by checking if it follows normal IP format
# and that bits are all sequential, such as 111111100000 not 1100111110001111, etc
def ValidMask(strToCheck):
	iNumBits=0
	if ValidateIP(strToCheck) == False:
		return 0
	# end if

	iDecValue = DotDec2Int(strToCheck)
	strBinary = bin(iDecValue)

	strTemp = "0"*32 + strBinary[2:]
	strBinary = strTemp[-32:]
	cBit = strBinary[0]
	bFound = False
	x=0
	for c in strBinary:
		x=x+1
		if cBit != c:
			iNumBits = x-1
			if bFound:
				return 0
			else:
				cBit=c
				bFound = True
			# end if
		# end if
	# next
	if iNumBits==0:
		iNumBits = x
	# end if
	return iNumBits
# end function

# Function MaskType
# Takes is a string with a subnet mask and determines if it is:
# - standard dotted decimal format
# - inverse dotted decimal format
# - neither, aka invalid mask format
def MaskType (strToCheck):
	if ValidMask(strToCheck)==False:
		return "Invalid Mask"
	# end if

	Quads = strToCheck.split(".")
	if int(Quads[0]) == int(Quads[3]):
		if int(Quads[0]) ==255:
			return "dotDec"
		else:
			return "inv"
		# end if
	# end if

	if int(Quads[0]) > int(Quads[3]):
		return "dotDec"
	else:
		return "inv"
	# end if
# End Function

# Function SubnetCompare
# Takes in three integers, two are int represenation of IP addresses, one is int of a mask
def SubnetCompare (iIP1,iIP2,iMask):
	iSubnet1 = iIP1 | iMask
	iSubnet2 = iIP2 | iMask
	return iSubnet1==iSubnet2
# End function

# Function ConvertMask
# Switches between dotted decimal and inverse dotted decimal
def ConvertMask (strToCheck):
	if ValidMask(strToCheck)==False:
		return "Invalid Mask"
	# end if
	strTemp = ""
	Quads = strToCheck.split(".")
	for Q in Quads:
		if strTemp =="":
			strTemp = str(255-int(Q))
		else:
			strTemp = strTemp + "." + str(255-int(Q))
		# End if
	#next
	return strTemp
# End function

# Function IPCalc
# This function takes in a string of IP address and does the actual final colculation
def IPCalc (strIPAddress):
	strIPAddress=strIPAddress.strip()
	strIPAddress=strIPAddress.replace("\t"," ")
	strIPAddress=strIPAddress.replace("  "," ")
	strIPAddress=strIPAddress.replace(" /","/")
	dictIPInfo={}
	strMask=""
	iBitMask=0
	if " " in strIPAddress:
		IPAddrParts = strIPAddress.split(" ")
		strIPAddress=IPAddrParts[0]
		strMask = IPAddrParts[1]
	if "/" in strIPAddress:
		IPAddrParts = strIPAddress.split("/")
		strIPAddress=IPAddrParts[0]
		try:
			iBitMask=int(IPAddrParts[1])
		except ValueError:
			iBitMask=0
		# end try
		strMask = DotDecGen(BitMask2Dec(iBitMask))
		if strMask != "Invalid":
			dictIPInfo['Maskmsg'] = "You provided the mask as a bit mask"
		else:
			dictIPInfo['MaskErr'] = str(iBitMask) + " is an invalid bit mask, changing to /32"
			iBitMask=32
			strMask = DotDecGen(BitMask2Dec(iBitMask))
		# end if
	# end if

	iBitMask = ValidMask(strMask)
	if iBitMask==0:
		if strMask=="":
			dictIPInfo['MaskErr'] = "You didn't provide a mask, assuming host only"
		else:
			dictIPInfo['MaskErr'] = strMask + " is an invalid mask, changing to host only"
		iBitMask=32
		strMask = DotDecGen(BitMask2Dec(iBitMask))
	# end if

	strMask2 = ConvertMask(strMask)
	strType = MaskType(strMask)
	if strType =="dotDec":
		dictIPInfo['Mask'] = strMask
		dictIPInfo['InvMask'] = strMask2
	elif strType == "inv":
		dictIPInfo['Mask'] = strMask2
		dictIPInfo['InvMask'] = strMask
	# end if

	if ValidateIP(strIPAddress):
		dictIPInfo['IPAddr'] = strIPAddress
		dictIPInfo['BitMask'] = str(iBitMask)
		iHostcount = 2**(32 - iBitMask)
		dictIPInfo['Hostcount'] = iHostcount
		iDecIPAddr = DotDec2Int(strIPAddress)
		iDecSubID = iDecIPAddr-(iDecIPAddr%iHostcount)
		iDecBroad = iDecSubID + iHostcount - 1
		dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
		dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)
		dictIPInfo['iDecIPAddr'] = iDecIPAddr
		dictIPInfo['iDecSubID'] = iDecSubID
		dictIPInfo['iDecBroad'] = iDecBroad
	else:
		dictIPInfo['IPError'] = "'" + strIPAddress + "' is not a valid IP!"
	# End if
	return dictIPInfo
# end function

# function FormatIPv6
# This function takes in a string and inserts : after every 4 characters, upto 32 char
def FormatIPv6(strAddr):
	strTemp = ""
	iCount = 0
	bCol = False
	if strAddr[0:2]=="0x":
		iStart = 2
	else:
		iStart = 0
	# end if
	for x in range (iStart,32,4):
		Q = strAddr[x:x+4].lstrip("0")
		if Q == "":
			if bCol:
				Q = "0:"
			else:
				iCount = iCount + 1
			# end if
		else:
			if iCount == 1:
				Q = "0:" + Q + ":"
			elif iCount > 1:
				Q = ":" + Q
				bCol = True
			else:
				Q = Q + ":"
			# end if
			iCount = 0
		# end if
		strTemp = strTemp + Q
	# next
	strTemp = strTemp.strip(":")
	if strTemp.count(":") < 7 and "::" not in strTemp:
		strTemp = strTemp + "::"
	# end if
	return strTemp
#end function

# function IPv6Calc
# This function takes in a string of IPv6 address and does the actual final colculation
def IPv6Calc (IPAddress):
	if all(c in Hex_set for c in IPAddress['IPAddr']):
		iHostcount = 2**(128 - IPAddress['BitMask'])
		IPAddress['Hostcount'] = iHostcount
		iDecIPAddr = int(IPAddress['IPAddr'],16)
		iDecSubID = iDecIPAddr-(iDecIPAddr%iHostcount)
		iDecBroad = iDecSubID + iHostcount - 1
		IPAddress['Subnet'] = FormatIPv6(hex(iDecSubID))
		IPAddress['Broadcast'] = FormatIPv6(hex(iDecBroad))
		IPAddress['IPAddr'] = FormatIPv6(IPAddress['IPAddr'])
		return IPAddress
	else:
		return "Invalid IP: " + IPAddress['IPAddr']
	#end if
# end function

# function QueryArin
# This function takes in an IP Address in a string and executes a Whois Query against ARIN
def QueryARIN (strIPAddress):
	#execute Whois Query against ARIN.
	dictARINResp={}
	strURL="http://whois.arin.net/rest/ip/"+strIPAddress
	strHeader={'Accept': 'application/json'}
	try:
		WebRequest = requests.get(strURL, headers=strHeader)
	except:
		return "Failed to connect to ARIN"
	# end try
	if WebRequest.status_code !=200:
		return "Request returned error code " + str(WebRequest.status_code)
	if isinstance(WebRequest,requests.models.Response)==False:
		return "response is unknown type"
	# end if

	# print (WebRequest.text)
	try:
		jsonWebResult = json.loads(WebRequest.text)
	except:
		return "Failed to decode the response"
	# end try

	if "net" not in jsonWebResult:
		return "Response not a Net Object"
	#end if
	dictARINResp['Org'] = jsonWebResult['net']['orgRef']['@name']
	dictARINResp['Handle'] = jsonWebResult['net']['orgRef']['@handle']
	if isinstance(jsonWebResult['net']['netBlocks']['netBlock'],dict):
		dictARINResp['StartIP'] = jsonWebResult['net']['netBlocks']['netBlock']['startAddress']['$']
		dictARINResp['EndIP'] = jsonWebResult['net']['netBlocks']['netBlock']['endAddress']['$']
		dictARINResp['CIDR'] = jsonWebResult['net']['netBlocks']['netBlock']['cidrLength']['$']
		dictARINResp['Type'] = jsonWebResult['net']['netBlocks']['netBlock']['type']['$']
	else:
		dictARINResp['StartIP'] = jsonWebResult['net']['netBlocks']['netBlock'][0]['startAddress']['$']
		dictARINResp['EndIP'] = jsonWebResult['net']['netBlocks']['netBlock'][0]['endAddress']['$']
		dictARINResp['CIDR'] = jsonWebResult['net']['netBlocks']['netBlock'][0]['cidrLength']['$']
		dictARINResp['Type'] = jsonWebResult['net']['netBlocks']['netBlock'][0]['type']['$']
	# End if
	dictARINResp['Ref'] = jsonWebResult['net']['ref']['$']
	dictARINResp['Name'] = jsonWebResult['net']['name']['$']
	return dictARINResp
# end function

# function PrintUsage
# This function takes no arguments prints out usage instructions
def PrintUsage():
    print("Usage: python {} IPAddress mask".format(strScriptName))
    print("       python {} inputFile ResultFile".format(strScriptName))
    print("Examples:")
    print("python {} 218.55.213.55/27".format(strScriptName))
    print("python {} 218.55.213.55 255.255.255.224".format(strScriptName))
    print("python {} 218.55.213.55 0.0.0.31".format(strScriptName))
    print("python {} 2607:fb90:7c90::/44 ".format(strScriptName))
    print(r"python {} c:\temp\iplist.txt c:\temp\ipcalcresult.csv".format(strScriptName))
    print("\nTo run in an interactive mode, where you are continually prompted for next subnet")
    print("  python {} -i".format(strScriptName))
# end function

# function CheckIPv6
# This function validates that a given strip is a valid IPv6 and mask
def CheckIPv6(strToCheck):
	dictIPv6Check={}
	strIPAddress=strToCheck

	if "/" in strIPAddress:
		strIPparts = strIPAddress.split("/")
		dictIPv6Check['IPAddr'] = strIPparts[0]
		try:
			dictIPv6Check['BitMask'] = int(strIPparts[1])
		except ValueError:
			dictIPv6Check['BitMask'] = 128
			dictIPv6Check['Msg'] = "Invalid mask provided, changed to 128"
		# end try
	else:
		dictIPv6Check['IPAddr'] = strIPAddress
		dictIPv6Check['BitMask'] = 128
		dictIPv6Check['Msg'] = "No mask provided. Assume 128"
	# end if
	if dictIPv6Check['BitMask'] > 128 or dictIPv6Check['BitMask'] < 1:
		dictIPv6Check['Msg'] = "Invalid mask provided, changed to 128"
		dictIPv6Check['BitMask'] = 128
	# end if
	if dictIPv6Check['IPAddr'][-2:] == "::":
		dictIPv6Check['IPAddr'] = dictIPv6Check['IPAddr'] + "0"*4
	# end if
	strIPparts = dictIPv6Check['IPAddr'].split(":")
	if len(strIPparts) > 8:
		return strToCheck + " to many parts to be a valid IPv6 address!"
	# end if
	iMissing = 9 - len(strIPparts)
	strAdd = ("0000:" * iMissing).strip(":")
	strIPAddress = ""
	for q in strIPparts:
		if q == "":
			strIPAddress = strIPAddress + strAdd + ":"
		else:
			strIPAddress = strIPAddress + ("0" * 4 + q)[-4:] + ":"
		#end if
	#next
	strIPAddress = strIPAddress.strip(":")
	strIPAddress = strIPAddress.replace(":","")
	if len(strIPAddress) != 32:
		return strToCheck + " is not a valid IPv6 address!"
	#end if
	dictIPv6Check['IPAddr'] = strIPAddress
	if all(c in Hex_set for c in strIPAddress):
		return dictIPv6Check
	else:
		return strToCheck + " is not hex"
# End Function

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

# End function section

# Main section of the script
SysArgs = sys.argv
iSysArgLen = len(sys.argv)
strMask = ""
iBitMask = ""
bContinue = True

if iSysArgLen < 2:
	strInput = getInput ("Please provide subnet: ")
	strInputParts = strInput.split()
	if len(strInputParts)>0:
		strIPAddress = strInputParts[0]
	else:
		strIPAddress = strInput
	if len(strInputParts)>1:
		strMask = strInputParts[1]
else:
	strIPAddress = SysArgs[1]

if iSysArgLen > 2:
	strMask = SysArgs[2]
# End If

if strIPAddress == "-i":
	bInteractive = True
else:
	bInteractive = False

while bContinue:
	bContinue = bInteractive
	if bInteractive:
		strInput = getInput ("Please provide subnet: ")
		strInputParts = strInput.split()
		if len(strInputParts)>0:
			strIPAddress = strInputParts[0]
		else:
			strIPAddress = strInput
		if len(strInputParts)>1:
			strMask = strInputParts[1]

	if strIPAddress.lower() == "quit" or strIPAddress.lower() == "exit":
		sys.exit(0)

	if strIPAddress=="-?" or strIPAddress=="?" or "-h" in strIPAddress or strIPAddress.lower() == "help" :
		PrintUsage()
		sys.exit(1)
	# end if

	if (":" in strIPAddress and ":\\" not in strIPAddress) or len(strIPAddress)==32 :
		IPv6Info = CheckIPv6(strIPAddress)
		IP_Result = IPv6Calc(IPv6Info)

		if "Msg" in IP_Result:
			print (IP_Result['Msg'])
		# end if
		print ("IP Addr: " + IP_Result['IPAddr'])
		print ("Bit Mask: " + str(IP_Result['BitMask']))
		iHostcount = IP_Result['Hostcount']
		if iHostcount == 1:
			print ("Host only")
		if iHostcount == 2:
			print ("only subnet and broadcast")
		if iHostcount > 2:
			print ("Host count: " + str(iHostcount-2))

		print ("Subnet IP: " + IP_Result['Subnet'])
		print ("Broadcast IP: " + IP_Result['Broadcast'])
		if bWhoisQuery:
			print ("Please stand by while I query ARIN for more details...")
			QueryResult = QueryARIN(IP_Result['IPAddr'])
			if isinstance(QueryResult,dict):
				strType = QueryResult['Type']
				if strType=="RV" or strType=="AP" or strType=="AF":
					print ("Assigned by " + strOrg)
				else:
					strOrgURL = "  https://whois.arin.net/rest/org/"+QueryResult['Handle']
					strOrg = QueryResult['Org']
					if strType == "IU":
						strOrg = QueryResult['Name']
						strOrgURL = ""
					#end if
					strStart = QueryResult['StartIP']
					strEnd = QueryResult['EndIP']
					strCIDR = QueryResult['CIDR']
					strRef = QueryResult['Ref']
					print ("Information from ARIN")
					print ("Org: "+strOrg+strOrgURL  )
					print ("Netblock: " + strStart +"/"+strCIDR+"("+strStart+"-"+strEnd+")")
					print (strRef)
					print ("Type:" + strType)
				# end if
			# End If
			if isinstance(QueryResult,str):
				print (QueryResult)
			# end if
		#end if
		sys.exit(0)
	# end if

	if "\\" in strIPAddress or ".txt" in strIPAddress or ".csv" in strIPAddress :
		print ("File processing Mode: Infile="+strIPAddress+" Outfile="+strMask)
		if os.path.isfile(strIPAddress):
			if strMask=="":
				iLoc = strIPAddress.find('.')
				strMask=strIPAddress[:iLoc]+"-out.csv"
				print ("No putput file provided, will use: "+strMask)
			#end if
			print("reading " + strIPAddress)
			fhInput = open(strIPAddress,'r')
			try:
				fhOutput = open(strMask,'w')
			except IOError as e:
				print("Failed to create {0}. Error {1} : {2}".format(strMask,e.errno,e.strerror))
				sys.exit(3)
			# end try
			strOut = ("IP Address,Bit Mask,Mask,Inverse Mask,Subnet IP,Broadcast IP,Host count,"
						"Net Block Start,Net Block End,CIDR,Org,Org Reference,Messages\n")
			fhOutput.write (strOut)
			for strLine in fhInput:
				strIPAddress = strLine.strip()
				print("Processing "+strIPAddress)
				if ":" in strIPAddress or len(strIPAddress)==32 :
					IPv6Info = CheckIPv6(strIPAddress)
					IP_Result = IPv6Calc(IPv6Info)
					if "IPError" in IP_Result:
						strOut = IP_Result['IPError']
					else:
						strOut = (str(IP_Result['IPAddr'])+","+str(IP_Result['BitMask'])+",,,"
								+str(IP_Result['Subnet'])+","+str(IP_Result['Broadcast'])+","
								+str(IP_Result['Hostcount']))
				else:
					IP_Result = IPCalc(strIPAddress)
					if "IPError" in IP_Result:
						strOut = IP_Result['IPError']
					else:
						strOut = (str(IP_Result['IPAddr'])+","+str(IP_Result['BitMask'])+","
								+str(IP_Result['Mask'])+","+str(IP_Result['InvMask'])+","
								+str(IP_Result['Subnet'])+","+str(IP_Result['Broadcast'])+","
								+str(IP_Result['Hostcount']))
					# end if
				# end if
				if bWhoisQuery and "IPAddr" in IP_Result:
					print ("Please stand by while I query ARIN for more details...")
					QueryResult = QueryARIN(IP_Result['IPAddr'])
					if isinstance(QueryResult,dict):
						strType = QueryResult['Type']
						if strType=="RV" or strType=="AP" or strType=="AF":
							strOut = strOut + "," + "Assigned by " + QueryResult['Org']
						else:
							strOrgURL = "  https://whois.arin.net/rest/org/"+QueryResult['Handle']
							strOrg = QueryResult['Org']
							if strType == "IU":
								strOrg = QueryResult['Name']
								strOrgURL = ""
							#end if
							strStart = QueryResult['StartIP']
							strEnd = QueryResult['EndIP']
							strCIDR = QueryResult['CIDR']
							strRef = QueryResult['Ref']
							strOrg = strOrg.replace(",",";")
							strOut = (strOut + "," + strStart + "," + strEnd + "," + strCIDR + ","
										+ strOrg + "," + strOrgURL)
						# end if
					# End If
					if isinstance(QueryResult,str):
						strOut = strOut + "," + QueryResult
					# end if
				if "MaskErr" in IP_Result and "IPError" not in IP_Result:
					strOut = strOut + "," + IP_Result['MaskErr'].replace(",",";")
				else:
					strOut = strOut + ","
				# end if
				fhOutput.write(strOut+"\n")
			#next
		else:
			print (strIPAddress+" does not seem to exists, bailing out!!")
			sys.exit(2)
		#end if
	else:
		print ("You provided IP address of '" + strIPAddress + " " + strMask + "'")

		if strMask != "":
			strType = MaskType(strMask)
			if strType =="dotDec":
				print ("The mask provided is a normal dotted decimal mask")
			elif strType == "inv":
				print ("You provided an inverse mask")
			# else:
			# 	print(strMask + " is not a valid mask")
		# end if

		IP_Result = IPCalc (strIPAddress + " " + strMask)
		if "IPError" in IP_Result:
			print(IP_Result['IPError'])
		else:
			if "MaskErr" in IP_Result:
				print (IP_Result['MaskErr'])
			# end if
			if "Maskmsg" in IP_Result:
				print (IP_Result['Maskmsg'])
			# end if
			strIPAddress = IP_Result['IPAddr']
			print ("IP Addr: " + strIPAddress)
			print ("Bit Mask: " + IP_Result['BitMask'])
			print ("Mask: " + IP_Result['Mask'])
			print ("Inverse Mask: " + IP_Result['InvMask'])
			iHostcount = IP_Result['Hostcount']
			if iHostcount == 1:
				print ("Host only")
			if iHostcount == 2:
				print ("only subnet and broadcast")
			if iHostcount > 2:
				print ("Host count: " + str(iHostcount-2))

			print ("Subnet IP: " + IP_Result['Subnet'])
			print ("Broadcast IP: " + IP_Result['Broadcast'])
			print ("Integer value of that IP: {}".format(IP_Result['iDecIPAddr']))
			print ("Integer value of the subnet IP: {}".format(IP_Result['iDecSubID']))
			print ("Integer value of the broadcast IP: {}".format(IP_Result['iDecBroad']))

			if bWhoisQuery:
				print ("Please stand by while I query ARIN for more details...")
				QueryResult = QueryARIN(strIPAddress)
				if isinstance(QueryResult,dict):
					strType = QueryResult['Type']
					strOrg = QueryResult['Org']
					if strType=="RV" or strType=="AP" or strType=="AF":
						print ("Assigned by " + strOrg)
					else:
						strOrgURL = "  https://whois.arin.net/rest/org/"+QueryResult['Handle']
						if strType == "IU":
							strOrg = QueryResult['Name']
							strOrgURL = ""
						#end if
						strStart = QueryResult['StartIP']
						strEnd = QueryResult['EndIP']
						strCIDR = QueryResult['CIDR']
						strRef = QueryResult['Ref']
						print ("Information from ARIN")
						print ("Org: "+strOrg+strOrgURL  )
						print ("Netblock: " + strStart +"/"+strCIDR+"("+strStart+"-"+strEnd+")")
						print (strRef)
						print ("Type:" + strType)
					# end if
				# End If
				if isinstance(QueryResult,str):
					print (QueryResult)
				# end if
			#end if
		#end if
	# end if