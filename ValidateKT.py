def ValidateKT(strKennitala):
  lstSum = []
  lstCheck = [3,2,7,6,5,4,3,2]
  for index,char in enumerate(strKennitala):
    lstSum.append(int(char) * lstCheck[index])
  intSum = sum(lstSum)
  intCheck = intSum % 11

  return (11 - intCheck) == int(strKennitala[9])

input("Kennitala: ")
strKennitala = input().strip()
strKennitala = strKennitala.replace("-", "").replace(" ", "").replace(".", "").replace(",", "")
print("Kennitala: " + strKennitala)
if len(strKennitala) != 10:
  print("Kennitala er ekki skráð")
if ValidateKT(strKennitala):
  print("Kennitala er skráð")
