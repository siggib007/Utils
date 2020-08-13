strDelim = ","
import csv
print ("Field Size Limit: {}".format(csv.field_size_limit()))
with open("C:/temp/QualysReport.csv",newline="") as hCSV:
	myReader = csv.reader(hCSV, delimiter=strDelim)
	# print(next(myReader))
	line = next(myReader)
	for x in list(range(0,len(line))):
		print ("{}:{}".format(x,line[x]))
	print("Header section: {} - {} - {}".format(line[0],line[1],line[21]))
	for line in myReader:
		print ("{} : {} - {} - {}".format(myReader.line_num,line[0],line[1],line[21]))
		if myReader.line_num > 100:
			break
	# while myReader:
	# 	lstLine = next(myReader)
	# 	print ("{} : {} - {}".format(myReader.line_num,lstLine[0],lstLine[1]))
