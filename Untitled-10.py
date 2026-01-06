import mysql.connector
import csv as c
import os

mydb = mysql.connector.connect(host="localhost", user="root", password="mysql", database="demo")

mycursor = mydb.cursor()
image_folder="image"
image_name="scene.jpg"
image_path = os.path.join(image_folder, image_name)

query="insert into image values (%s)"

mycursor.execute(query,(image_path,))
mydb.commit()

print("Image path inserted successfully.")