from pymongo import MongoClient
import csv
import base64
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

os.system('source /etc/mphrx/cust_env.sh')

class MongoDetailConstants:
    def __init__(self):
        self.envType = os.environ.get('ENVIRONMENT_TYPE')
        if not self.envType:
            raise ValueError("ENVIRONMENT_TYPE environment variable not set")
        self._PORT = "27018"
        self.custId = os.environ.get('CUSTID')
        if not self.custId:
            raise ValueError("CUSTID environment variable not set")


        if self.envType.upper() == "DEV":
            self._IP = "10.31.10.68"
            if not self._IP:
                raise ValueError("DB_HOSTNAME environment variable not set")
            self._USERNAME = "unimdev_minerva"
            self._PASSWORD = "unimdev_minerva"
            self._DATABASE = "unimdev_minervadb"
        elif self.envType.upper() == "QA":
            self._IP = "10.31.10.69"
            if not self._IP:
                raise ValueError("DB_HOSTNAME environment variable not set")
            self._USERNAME = "unimqa_minerva"
            self._PASSWORD = "unimqa_minerva"
            self._DATABASE = "unimqa_minervadb"
        elif self.envType.upper() == "UAT":
            self._IP = "10.31.10.70"
            if not self._IP:
                raise ValueError("DB_HOSTNAME environment variable not set")
            self._USERNAME = "uniuat_minerva"
            self._PASSWORD = "uniuat_minerva"
            self._DATABASE = "uniuat_minervadb"
        else:
            raise ValueError(f"The DB Credentials are not supported for this environment named as {self.envType}, Connect with the developer to include this support")
            os.exit()

    @property
    def IP(self):
        return self._IP

    @property
    def PORT(self):
        return self._PORT

    @property
    def USERNAME(self):
        return self._USERNAME

    @property
    def PASSWORD(self):
        return self._PASSWORD

    @property
    def DATABASE(self):
        return self._DATABASE

    @IP.setter
    def IP(self, value):
        raise ValueError("Cannot modify the environment value of IP")

    @PORT.setter
    def PORT(self,value):
        raise ValueError("Connot modify the environment value of PORT")

    @USERNAME.setter
    def USERNAME(self,value):
        raise ValueError("Cannot modify the environment value of USERNAME")

    @PASSWORD.setter
    def PASSWORD(self,value):
        raise ValueError("Cannot modify the environment value of PASSWORD")

    @DATABASE.setter
    def DATABASE(self,value):
        raise ValueError("Cannot modify the environment value of DATABASE")


def connection_Details():
    conDetail = MongoDetailConstants()
    return conDetail

def establishing_Connection():
    conDetail = connection_Details()
    link = "mongodb://" + conDetail.USERNAME + ":" + conDetail.PASSWORD + "@" + conDetail.IP + ":" + conDetail.PORT + "/"+conDetail.DATABASE
    client = MongoClient(link)
    print("Connection Established")
    return client

def getDB():
    conDetail = connection_Details()
    client = establishing_Connection()
    return client[conDetail.DATABASE]

def append_to_csv(fileName, data):
    with open(fileName, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

def get_Csv(data,filename, filepath):
    # file_Data={"<strong>SL No.</strong>":" ","<strong>Data</strong>":" ","<strong>Numero da Carteirinha</strong>":" ","<strong>CPF</strong>":" ","<strong>Nome</strong>":" ","<strong>Data de nascimento</strong>":" "}
    fields = ["SL No.","Data","Numero da Carteirinha","CPF","Nome","Data de nascimento"]
    count = 0;
    filename = os.path.join(filepath,filename)
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(fields)
    except:
        print("File Already Exist")
    for i in data:
        count += 1
        file_data = []
        file_data.append(count)
        file_data.append(i.get("dateCreated").strftime("%d/%m/%Y"))
        file_data.append(extract_Card_Number(i.get("cardNumber")))
        file_data.append(i.get("CPF"))
        file_data.append([x.get("patientFirstName") for x in i.get("name") if x.get("useCode") == "Human Name"][0])
        file_data.append(i.get("dateOfBirth").strftime("%d/%m/%Y"))
        append_to_csv(filename,file_data)

def extract_Card_Number(data):
    cardNumbers = set()
    for i in data:
        if i.get("typeCode") == 'cardNumber':
            cardNumbers.add(i.get("idValue"))
    return cardNumbers

def sendEmail(filename,path):
    mailAttachment = []
    filname_with_path = os.path.join(path,filename)
    data = open(filname_with_path,'rb').read()
    base64_encoded_invalidCPF = base64.b64encode(data).decode('UTF-8')
    invalidCPFAttachment = {}
    invalidCPFAttachment["attachmentName"] = filename
    invalidCPFAttachment["attachmentDesc"] = "This File Contains Invalid CPF Details"
    invalidCPFAttachment["derefUri"] = base64_encoded_invalidCPF
    mailAttachment.append(invalidCPFAttachment)
    subject = "Relatório Semanal: Relatório de CPF Inválido"
    emailIds = ["ashahi@mphrx.com","ssharma6@mphrx.com"] # Comment For Production
    # emailIds = ["res@unimed.coop.br"] # Uncomment For Production
    body = f"Olá, pessoal\nEsperamos que vocês estejam bem, por favor consulte o anexo para ver a lista de CPFs inválidos identificados durante a ingestão de dados de {datetime.now()-timedelta(days=7)} para {datetime.now()}.\n\nObrigado e Cumprimentos\nMphRx"
    mail_from = "ashahi@mphrx.com"
    message = MIMEMultipart()
    emailResponse = dict()
    for mail_id in emailIds:
        message["From"] = mail_from
        message["To"] = mail_id
        message["Subject"] = subject
        message.attach(MIMEText(body))
        with open(filname_with_path,'rb') as file:
            part = MIMEBase("application","octet-stream",Name = filename)
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",f"attachment; filename={filename}"
        )
        message.attach(part)
        smtp = smtplib.SMTP("smtp-mail.outlook.com",587)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(mail_from,"Mphrx@1234")
        response = smtp.sendmail(mail_from,mail_id,message.as_string())
        smtp.close()
        if response:
            emailResponse[mail_id] = f"Failed to send Email at {mail_id}"
        else:
            emailResponse[mail_id] = f"Successfully sent an Email at {mail_id}"
    return emailResponse

