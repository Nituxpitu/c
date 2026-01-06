import mysql.connector 
import csv as c

mydb=mysql.connector.connect(host="localhost",user="root",password="mysql",database="demo")
mycursor=mydb.cursor()

with open("stock.csv", 'r', encoding='utf-8-sig') as csvfile:
    reader = c.DictReader(csvfile)
    query = "INSERT INTO data (Model, Qty, Purchase, Total, Sales, Balance) VALUES (%s, %s, %s, %s, %s, %s)"
    for row in reader:
        values = (
                    row['Model'], 
                    row['Qty'], 
                    row['Purchase'], 
                    row['Total'], 
                    row['Sales'], 
                    row['Balance']
                )
        try:
            mycursor.execute(query,values)
            print("Done the data is stored in the database")
        except:
            print("Error inserting row probably same data try to enter again:", row)
    mydb.commit()








