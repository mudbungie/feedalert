#!/usr/local/bin/python3.4

import sys, sqlite3, datetime, getopt, csv, smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#teams = ['Bears','Bengals','Bills','Broncos','Browns','Buccaneers','Chargers','Colts','Dolphins','Giants','Jaguars','Jets','Lions','Patriots','Raiders','Rams','Ravens','Redskins','Steelers','Texans','Vikings']


def sendEmail(html, to_addrs):
    auth_addrs = "dummy address"
    from_addrs = "contentalert@sldesksite.com"
    from_addrs_pass = "dummy pass"
    smtpServer = 'smtp.sendgrid.net'
    smtpPort = 587
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Link"
    msg['From'] = from_addrs
    msg['To'] = to_addrs

    # Record the MIME types of both parts - text/plain and text/html.
    message = MIMEText(html, 'html')

    # Attach into message container.
    msg.attach(message)

    # Send the message via local SMTP server.
    s = smtplib.SMTP(smtpServer, smtpPort)
    s.ehlo()
    s.starttls()
    s.ehlo()

    s.login(auth_addrs, from_addrs_pass)

    # sendmail function takes 3 arguments: sender's address, recipient's address, message
    s.sendmail(from_addrs, to_addrs, msg.as_string())
    s.quit()
    
    
if __name__ == "__main__":
	html = '<html><body><h1>Videos received by User</h1><br><br>'
	sendEmail(html,"rbijleveld@desksite.com")
