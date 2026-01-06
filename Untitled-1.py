import csv as c
x=['hi','I','am','Nitya']
with open("nit.csv",'r') as csvfile:
    reader=c.reader(csvfile)
    for i in reader:
        if i==None:
            print("The file is empty")
        else:
            print(i)
    