import config as config
import os
from datetime import datetime,timedelta

db = config.getDB()
collection = db["customCPFStatus"]
endTime = datetime.now()
startTime = datetime.now() - timedelta(days=7)
data = collection.find({"dateCreated": {'$gte': startTime, '$lte': endTime}})
sT= startTime.strftime("%d-%m-%Y")
eT = endTime.strftime("%d-%m-%Y")
path = os.path.join("tmp","FailedCPFReport")
new_path = os.path.join(path,"CSVFile")
filename = f"Invalid_CPF_Report({sT}_to_{eT}).csv"


try:
    os.remove(os.path.join(path,filename))
    print("File removed successfully")
except FileNotFoundError:
    print("File not found")
except:
    print("Error deleting file")

config.get_Csv(data, filename, new_path)
print("File Created Ready For Email...")
print("Emailing the file...")
status = config.sendEmail(filename,new_path)
print(status)

