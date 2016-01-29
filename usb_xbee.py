#!/usr/bin/python

import serial, time, datetime, sys
from xbee import ZigBee
import time
import sqlite3
import datetime
from datetime import date, timedelta
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText



#SQL connection
conn=sqlite3.connect('/doors/door_status.db')
curs=conn.cursor()

#serial port setup
SERIALPORT = "/dev/ttyUSB0"    # the com/serial port the XBee is connected to, the pi GPIO should always be ttyAMA0
BAUDRATE = 9600      # the baud rate we talk to the xbee
ser = serial.Serial(SERIALPORT, BAUDRATE)
xbee = ZigBee(ser)

#inits
door1status = 'Closed'
door2status = 'Closed'


#read the cred.ini for account info.
f = open('cred.ini', 'r')

username = f.readline()
password = f.readline()
fromAddress = f.readline()
toAddress = f.readline()


f.close()


#save the reading to the sqllite db
def save_door_reading (open_close, doorid):
    # I used triple quotes so that I could break this string into
    # two lines for formatting purposes
    dtnowsql = str(datetime.datetime.now() - timedelta(hours=5))

    curs.execute("INSERT INTO status VALUES( (?), (?), (?) )" (dtnowsql, open_close, doorid))

    # commit the changes
    conn.commit()

#send email
def send_email (door,stus):

    global username
    global password
    global fromAddress
    global toAddress


    msg = MIMEMultipart()
    msg['From'] = fromAddress
    msg['To'] = toAddress
    msg['Subject'] = door + ' Status: ' + stus
    message = door + ' Status: ' + stus
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.gmail.com',587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(username, password)

    mailserver.sendmail(fromAddress,toAddress,msg.as_string())

    mailserver.quit()



def get_door1_value(data):

        readings =[]

        #check the data contains the dio-4 sample.  Put in to ingnore some kind of startup frame that crashed the program
        if 'dio-4' in str(data):
            for item in data:
                    readings.append(item.get('dio-4'))

            value1 = readings[0]

            return value1



def get_door2_value(data):
        
        #print str(data)
        readings =[]

        #check the data contains the dio-1 sample.  Put in to ingnore some kind of startup frame that crashed the program
        if 'dio-1' in str(data):
            for item in data:
                    readings.append(item.get('dio-1'))

            value1 = readings[0]


        return value1


def door1():
    try:

        #datetime
        strdtnow = str(datetime.datetime.now())
        dtnow = datetime.datetime.now()

        global door1status

        response = xbee.wait_read_frame()

        if 'dio-4' in str(response):
            value_door1 = get_door1_value(response['samples'])
        else:
            value_door1 = door1status
        


        if value_door1:
            doorstatus1 = 'Closed'
        else:
            doorstatus1 = 'Open'

        print 'Time: ' + strdtnow + '  Door1 is ' + doorstatus1

        if doorstatus1 != door1status:
            #save_door_reading(doorstatus1, 'Door1')
            door1status = doorstatus1

            eightpm = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 20,0,0)
            ninepm = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 21,0,0)
            fiveam = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 5,0,0)

            if door1status == 'Open' and ((dtnow > eightpm) and (dtnow < ninepm)):
                #txt message
                print "Sending Email Door1 " + doorstatus1
                send_email("Door1", doorstatus1 + 'Open After Eight PM')
            elif door1status == 'Open' and ((dtnow > ninepm) or (dtnow < fiveam)):
                #call
                print "Sending Email Door1 " + doorstatus1
                send_email("Door1", doorstatus1 + 'Open After Nine PM')
            else:
               #send normal email
                print "Sending Email Door1 " + doorstatus1
                send_email("Door1", doorstatus1)





    except KeyboardInterrupt:
       print 'error/exception'
 

def door2():
    try:
        
        #datetime
        strdtnow = str(datetime.datetime.now())
        #dtnow = datetime.datetime.now()

        global door2status

        response = xbee.wait_read_frame()

        if 'dio-1' in str(response):
            value_door2 = get_door2_value(response['samples'])
        else:
            value_door2 = door2status

        if value_door2:
            doorstatus2 = 'Closed'
        else:
            doorstatus2 = 'Open'

        print 'Time: ' + strdtnow + '  Door2 is ' + doorstatus2

        if doorstatus2 != door2status:
            #save_door_reading(doorstatus2, 'Door2')
            door2status = doorstatus2
            
            eightpm = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 20,0,0)
            ninepm = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 21,0,0)
            fiveam = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, 5,0,0)

            if door2status == 'Open' and ((dtnow > eightpm) and (dtnow < ninepm)):
                #txt message
                print "Sending Email Door2 " + doorstatus2
                send_email("Door2", doorstatus2 + 'Open After Eight PM')
            elif door2status == 'Open' and ((dtnow > ninepm) or (dtnow < fiveam)):
                #call
                print "Sending Email Door2 " + doorstatus2
                send_email("Door2", doorstatus2 + 'Open After Nine PM')
            else:
               #send normal email
                print "Sending Email Door2 " + doorstatus2
                send_email("Door2", doorstatus2)
        


    except KeyboardInterrupt:
       print 'error/exception'
      





print 'Starting Up Monitor'
# Continuously read and print packets

try:
    while True:
        door1() #do door1 stuff

        door2() #do door2 stuff
    
        

except KeyboardInterrupt:
    pass

        

ser.close()
