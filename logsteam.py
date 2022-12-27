#!/usr/bin/env python3
# coding: latin-1

##--> LIBRARIES
from datetime import datetime
import requests
import json
import time
import os

##--> VARIABLES
url = 'https://api.gocache.com.br/v1/' ###--> URL API END POINT
user_agent = 'LogSteam/1.0 (compatible; Logsteam/v1.0; https://github.com/Outs1d3r-Net/LogSteam)'
api_token = 'API_TOKEN_HERE' ###--> API TOKEN GOCACHE: <user_name>
limdata = '1000' ###--> QTT OF EVENTS
path_output = '/opt/API/GOCACHE/' ###--> PATH FOR OUTPUT DATA 
path_domain_date = str(datetime.now().date()).replace('-','_') ###--> FOR CREATE DIR WITH CURRENT DATE NAME
path_status = path_output+'status/' ###--> PATH FOR STATUS OUTPUT DATA
buckets3 = 'BUCKET_NAME' ###--> OUTPUT BUCKETS3
awsprofile = 'PROFILE_NAME' ###--> AWS PROFILE

##--> FUNCTIONS
###--> GET ALL DOMAINS IN GOCACHE API
def getdomains():

    global domains

    headers = {'Accept': 'application/json','GoCache-Token': api_token, 'User-Agent': user_agent}
    response = requests.request(method='GET', url=url+"domain", headers=headers)
    decodedResponse = json.loads(response.text)

    domains = decodedResponse['response']['domains']

    #### CREATE PATHS FOR OUTPUT DATA FOR ALL DOMAINS
    for domain in range(len(domains)):
        try:
            os.makedirs(os.path.dirname(path_output+"domains/"+str(domains[domain])+"/"+path_domain_date+"/"))
        except:
            continue

###--> CREATE TIMESTAMPS FOR REQUESTS
def gettimestamp():

    global startdate, enddate

    enddate = datetime.now().date().strftime('%m/%d/%y '+str(datetime.now().time()).split('.')[0])
    enddate = str(datetime.strptime(enddate, '%m/%d/%y %H:%M:%S').timestamp()).split('.')[0]

    startdate = str(int(enddate)-600) ####--> REMOVE 15 MIN FOR START DATE
    #print("Data de inicio:",startdate) ####--> FOR DEBUG
    #print("Date de fim:",enddate) ####--> FOR DEBUG
 
    try:    ####--> CREATE DIR OUTPUT IDs DB
        os.makedirs(os.path.dirname(path_status))
    except:
        pass

    try:    ####--> CREATE FILE OUTPUT IDs DB
        id_output = open(path_status+'IDs_output.txt','a')
        id_output.close()
    except:
        pass

###--> GET EVENTS IN GOCACHE
def getfirewalldata():
    for domain in range(len(domains)): ####--> SCROLL ALL DOMAINS
        param = {'offset':'0', 'limit':limdata, 'start_date':startdate, 'end_date':enddate}
        headers = {'Accept': 'application/json','GoCache-Token': api_token,'User-Agent': user_agent}
        response = requests.request(method='GET', url=url+"firewall/event/"+str(domains[domain]), params=param, headers=headers)
        decodedResponse = json.loads(response.text)

        time.sleep(1) ####--> BYPASS RATELIMIT GOCACHE
        
        ####--> GET EVENT'S NUMBER'S
        if len(decodedResponse['response']['events']) <= 1:
            try:    ####--> FOR ONE
                eventID = str(decodedResponse['response']['events'][0]['id'])
                eventTSTAMP = str(decodedResponse['response']['events'][0]['timestamp'])
            except:    ####--> FOR NOTHING
                #print("[*] Exception 1 - No events found for this domain:",str(domains[domain])) ####--> FOR DEBUG
                pass 
        else:
            for evt in range(len(decodedResponse['response']['events'])):
                try:    ####--> FOR MULTIPLE EVENTS
                    eventID = str(decodedResponse['response']['events'][evt]['id'])
                    eventTSTAMP = str(decodedResponse['response']['events'][evt]['timestamp'])

                    ####--> VERIFY IF EVENT ID IS NEW
                    with open(path_status+'IDs_output.txt') as ver:
                        if not eventID in ver.read():
                            param = {'timestamp':eventTSTAMP}
                            headers = {'Accept': 'application/json','GoCache-Token': api_token,'User-Agent': user_agent}
                            response = requests.request(method='GET', url=url+"firewall/event/"+str(domains[domain])+"/"+eventID, params=param, headers=headers)
                            decodedResponseEvent = json.loads(response.text)

                            ####--> OUTPUT JSON EVENT DATA
                            eventOUTPUT = open(path_output+"domains/"+str(domains[domain])+"/"+path_domain_date+"/"+str(domains[domain])+"_"+''.join(str(datetime.now().time()).split('.')[0].split(':')[0:2])+'.json','a')
                            eventOUTPUT.write(str(json.dumps(decodedResponseEvent))+"\n")
                            eventOUTPUT.close()

                            ####--> REGISTER EVENT ID IN FILE DB
                            idREG = open(path_status+'IDs_output.txt','a')
                            idREG.write(eventID+"\n")
                            idREG.close()

                            time.sleep(1) ####--> BYPASS RATELIMIT GOCACHE
                except:
                    #print("[*] Exception 2 - I still don't understand your reason!") ####--> FOR DEBUG
                    pass 

def uploadtobuckets3():
    os.system("aws s3 sync "+path_output+"domains "+"s3://"+buckets3+"/ --profile "+awsprofile)
    time.sleep(5)
    try:
        os.system("rm -rf "+path_output+"domains")
    except:
        pass

##--> MAIN
getdomains()
gettimestamp()
getfirewalldata()
time.sleep(5)
uploadtobuckets3()
