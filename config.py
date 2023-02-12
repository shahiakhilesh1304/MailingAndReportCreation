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

class MongoDetailConstants:

    def __init__(self):
        self.custId = os.environ.get('CUSTID')
        if not self.custId:
            raise ValueError("CUSTID environment variable not set")
        self.envType = os.environ.get('ENVIRONMENT_TYPE')
        if not self.envType:
            raise ValueError("ENVIRONMENT_TYPE environment variable not set")
        self._IP = os.environ.get('DB_HOSTNAME')
        if not self._IP:
            raise ValueError("DB_HOSTNAME environment variable not set")
        self._PORT = "27018"
        self._USERNAME = "{0}_minerva".format(self.custId)
        self._PASSWORD = "{0}_minerva".format(self.custId)
        self._DATABASE = "{0}_minervadb".format(self.custId)

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

def append_to_csv(fileName, data):
    with open(fileName, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

def get_Csv(data,filename):
    # file_Data={"<strong>SL No.</strong>":" ","<strong>Data</strong>":" ","<strong>Numero da Carteirinha</strong>":" ","<strong>CPF</strong>":" ","<strong>Nome</strong>":" ","<strong>Data de nascimento</strong>":" "}
    fields = ["SL No.","Data","Numero da Carteirinha","CPF","Nome","Data de nascimento"]
    count = 0;
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

def sendEmail(filename):
    mailAttachment = []
    data = open(filename,'rb').read()
    base64_encoded_invalidCPF = base64.b64encode(data).decode('UTF-8')
    invalidCPFAttachment = {}
    invalidCPFAttachment["attachmentName"] = filename
    invalidCPFAttachment["attachmentDesc"] = "This File Contains Invalid CPF Details"
    invalidCPFAttachment["derefUri"] = base64_encoded_invalidCPF
    mailAttachment.append(invalidCPFAttachment)
    subject = "Relatório Semanal: Relatório de CPF Inválido"
    emailIds = ["ashahi@mphrx.com"] # Comment For Production
    # emailIds = ["res@unimed.coop.br"] # Uncomment For Production
    body = f"Olá, pessoal\nEsperamos que vocês estejam bem, por favor consulte o anexo para ver a lista de CPFs inválidos identificados durante a ingestão de dados de {datetime.now()-timedelta(days=7)} para {datetime.now()}.\n\nObrigado e Cumprimentos\nMphRx"
    mail_from = "test_mphrx_unimed@hotmail.com"
    message = MIMEMultipart()
    emailResponse = dict()
    for mail_id in emailIds:
        message["From"] = mail_from
        message["To"] = mail_id
        message["Subject"] = subject
        message.attach(MIMEText(body))
        with open(filename,'rb') as file:
            part = MIMEBase("application","octet-stream")
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
        smtp.login(mail_from,"TestUnimed@123")
        response = smtp.sendmail(mail_from,mail_id,message.as_string())
        smtp.close()
        if response:
            emailResponse[mail_id] = f"Failed to send Email at {mail_id}"
        else:
            emailResponse[mail_id] = f"Successfully sent an Email at {mail_id}"
    return emailResponse

