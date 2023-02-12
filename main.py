import config as config
import os
from datetime import datetime,timedelta

client = config.establishing_Connection()
db = client["unimdev_minervadb"]
collection = db["customCPFStatus"]
endTime = datetime.now()
startTime = datetime.now() - timedelta(days=7)
data = collection.find({"dateCreated": {'$gte': startTime, '$lte': endTime}})
sT= startTime.strftime("%d-%m-%Y")
eT = endTime.strftime("%d-%m-%Y")

filename = f"Invalid_CPF_Report({sT}_to_{eT}).csv"
print(filename)


try:
    os.remove(filename)
    print("File removed successfully")
except FileNotFoundError:
    print("File not found")
except:
    print("Error deleting file")

config.get_Csv(data, filename)
status = config.sendEmail(filename)
print(status)

