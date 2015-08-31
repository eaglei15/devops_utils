#!/usr/bin/python
import time
import hashlib
import base64
import smtplib
import httplib, urllib
import boto.route53

awsInstanceIinfoBaseAPIAddr = "169.254.169.254"
ipv4RetrievalEndPoint = "latest/meta-data/public-ipv4"
inctanceRetrievalEndPoint = "latest/meta-data/instance-id"
env = sys.argv[1].lower()

if env == "prod":
    env = ""
else:
    env = env + "-"

notificationUser = "email_login@example.com"
notificationPass = "email_password"

# Get hosts public IP
conn = httplib.HTTPConnection(awsInstanceIinfoBaseAPIAddr)
conn.request("GET", ("/" + ipv4RetrievalEndPoint))
response = conn.getresponse()
instanceIPv4 = response.read()
conn.close()
   
# Get hosts intance id
conn = httplib.HTTPConnection(awsInstanceIinfoBaseAPIAddr)
conn.request("GET", ("/" + inctanceRetrievalEndPoint))
response = conn.getresponse()
instanceID = response.read()
conn.close()
  
print "\nInstance IP: " + instanceIPv4 + "\n"
print "Instance ID: " + instanceID + "\n"

recipients = ["user1@example.com","user2@example.com"]
timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
zoneDomain = "servers.example.com"
serversZone = zoneDomain + "."
serversHostPostfix = "." + zoneDomain
serverRecordSet = env + instanceID + serversHostPostfix
rsetUpdate = False
timeoutMax = 180
timeoutCounter = 0
waitIntervals = 30

def varDump(objParam):
    attrs = vars(objParam)
    print ', '.join("%s: %s" % item for item in attrs.items())
    
    
def logger(level, message):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    print "[" + timestamp + "] " + level.upper() + ": " + message
    
def emailNotification(gmailUser, gmailPass, recipients, serverRecordSet, zoneName, zoneId, operation, instanceIPv4):
    
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.login(gmailUser, gmailPass)
    
    headers = "\r\n".join(["from: " + "noreply@example.com",
                       "subject: Route53 server hostname " + operation,
                       "mime-version: 1.0",
                       "content-type: text/html"])
    
    body_of_email = "Records set <b>" + serverRecordSet + "</b> was " + operation + " for server with IP <b>" + instanceIPv4 + "</b> in zone: <b>" + zoneName + "</b>"
    content = headers + "\r\n\r\n" + body_of_email
    session.sendmail(gmailUser, recipients, content)

logger("INFO", "Starting, boto ver - " +  boto.Version)

# Open connection to Route 53 API
conn = boto.route53.connect_to_region('us-east-1')

# Get the zone id for our managed domain
zoneId = conn.get_zone(serversZone).id

# Get zone name for logging and notifications
zoneName = conn.get_zone(serversZone).name

# Get zone object
zone = conn.get_zone(serversZone)

# Check if record set exists for our zoneId 
if conn.get_all_rrsets(zoneId, type='A', name=(serverRecordSet + ".")):
    rsets = conn.get_all_rrsets(zoneId, type='A', name=serverRecordSet )

    for rset in rsets:
        if rset.name == serverRecordSet + "." and rset.resource_records[0] != instanceIPv4:
            logger("INFO", "Updating record set: " + serverRecordSet + " to " + instanceIPv4)
            statusObj = zone.update_a(serverRecordSet, instanceIPv4, ttl='60', comment=('Update on: ' + timestamp))

            # Wait until the status of the resource is INSYNC
            while statusObj.status != "INSYNC" and timeoutCounter <= timeoutMax:
                logger("INFO", "Record status " + statusObj.status + " " + str(timeoutCounter) + " sec")
                time.sleep(waitIntervals)
                timeoutCounter += waitIntervals
                statusObj.update()
    
            statusObj.update()
            
            if timeoutCounter >= timeoutMax and statusObj.status != "INSYNC":
                logger("INFO", "Timeout reached updating the record set " + serverRecordSet + " after " + str(timeoutCounter)  + " sec the satate is " + statusObj.update())
                exit(1)
            else:
                operation = "updated"
                logger("INFO", "Record set was succesfully " + operation + " for: " + serverRecordSet)
                emailNotification(notificationUser, notificationPass, recipients, serverRecordSet, zoneName, zoneId, operation, instanceIPv4)
        else:
             logger("INFO", "No update required for : " + serverRecordSet + " has the same IP: " + rset.resource_records[0])
else:
    logger("INFO", "Adding new record set: " + serverRecordSet)
    statusObj = zone.add_a(serverRecordSet, instanceIPv4, ttl='60', comment=('Update on: ' + timestamp))
    # Wait until the status of the resource is INSYNC
    while statusObj.status != "INSYNC" and timeoutCounter <= timeoutMax:
        logger("INFO", "Record status " + statusObj.status + " " + str(timeoutCounter) + " sec")
        time.sleep(waitIntervals)
        timeoutCounter += waitIntervals
        statusObj.update()
    
    if timeoutCounter >= timeoutMax and statusObj.status != "INSYNC":
        logger("INFO", "Timeout reached creating the record set " + serverRecordSet + "after " + str(timeoutCounter)  + " sec the satate is " + statusObj.update())
        exit(1)
    else:
        operation = "created"
        logger("INFO", "Record set was succesfully " + operation + " for: " + serverRecordSet)
        emailNotification(notificationUser, notificationPass, recipients, serverRecordSet, zoneName, zoneId, operation, instanceIPv4)

    
#===============================================================================
# # List the record sets of the zone id to verify that the update went trough
# rsets = conn.get_all_rrsets(zoneId)
# for rset in rsets:
#     if rset.name == serverRecordSet + ".":
#         print "INFO: The record set for: " + rset.name + " set to IP: " + rset.resource_records[0]
#===============================================================================
    
