import csv as c
import firebase_admin
from firebase_admin import credentials, firestore



cred=credentials.Certificate("serviceaccountkey.json")
firebase_admin.initialize_app(cred)
db=firestore.client()
batch=db.batch()

with open("fdemo.csv",'r') as csvfile:
    reader=c.DictReader(csvfile)
    for row in reader:
        doc_ref = db.collection("New table").document()
        batch.set(doc_ref, row)
batch.commit()
print("Done")
