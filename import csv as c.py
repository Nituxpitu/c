import csv as c
hedfile=["no","Name","age","contact"]
data=[{"Name":"Nitya","age":19,"contact":9924405051,"no":21},{"Name":"Aryan","age":20,"contact":9924405451,"no":22},{"Name":"raj","age":23,"contact":9924405411,"no":25}]
with open("Demo.csv",'w') as csvfile:
    writer=c.DictWriter(csvfile,fieldnames=hedfile)
    writer.writeheader()
    writer.writerows(data)
print("done")