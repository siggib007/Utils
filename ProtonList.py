import os
import json
import shutil

iIndex = 0
strFolderPath = "C:/protonexport/siggi@infosechelp.net/mail_20240302_170047/"
strDestPath = "C:/protonexport/oruggtnet/"
for strFileName in os.listdir(strFolderPath):
    if strFileName.endswith(".json"):
        objFileIn = open(strFolderPath + strFileName, "r", encoding="utf-8")
        dictData = json.load(objFileIn)
        if "ToList" in dictData["Payload"]:
            if isinstance(dictData["Payload"]["ToList"], list):
                for dictAddress in dictData["Payload"]["ToList"]:
                    if "oruggtnet" in dictAddress["Address"]:
                        strEmailFile = dictData["Payload"]["ID"] + ".eml"
                        strDstEmails = dictData["Payload"]["Subject"] + \
                            str(iIndex)+".eml"
                        strDstEmails = strDstEmails.replace(":", " ")
                        strDstEmails = strDstEmails.replace("[", "")
                        strDstEmails = strDstEmails.replace("]", "")
                        strDstEmails = strDstEmails.replace("?", "")
                        print(dictData["Payload"]["Subject"])
                        shutil.copy(strFolderPath + strEmailFile,
                                    strDestPath + strDstEmails)
                        iIndex += 1
        objFileIn.close()
