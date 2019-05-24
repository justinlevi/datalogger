from __future__ import print_function

import time
import pijuice
import subprocess
import datetime
import time
import os
import sys
import json
import argparse
# import boto3
import decimal
import uuid
import requests
import re

# Helper class to convert a DynamoDB item to JSON.

headers = {
    "x-api-key": "da2-kon7ntg7jrfffd7xulfuncbyqu",
    "Content-Type": "application/graphql"
}

# curl -XPOST -H "Content-Type:application/graphql" -H "x-api-key:da2-kon7ntg7jrfffd7xulfuncbyqu" -d '{ "query": "query listData {listData { items { date id} }}" }' https://c7erukjz5vhrrgqetc5sf3ia2y.appsync-api.us-east-1.amazonaws.com/graphql


def run_query(
        mutation, variables
):  # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post(
        'https://c7erukjz5vhrrgqetc5sf3ia2y.appsync-api.us-east-1.amazonaws.com/graphql',
        json={
            'query': mutation,
            'variables': variables
        },
        headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                request.status_code, mutation))


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


parser = argparse.ArgumentParser()
parser.add_argument('--workTime', nargs='?', const=60, type=int)
args = parser.parse_args()

DELTA_MIN = 10

with open('/home/pi/data.json') as json_file:
    data = json.load(json_file)

# Rely on RTC to keep the time
subprocess.call(["sudo", "hwclock", "--hctosys"])

# Record start time
timestampStart = int(time.time())

# This script is started at reboot by cron.
# Since the start is very early in the boot sequence we wait for the i2c-1 device
while not os.path.exists('/dev/i2c-1'):
    time.sleep(0.1)

try:
    pj = pijuice.PiJuice(1, 0x14)
except:
    print("Cannot create pijuice object")
    sys.exit()

workTime = args.workTime if args.workTime else 60

# Do the work
for i in range(workTime):
    print('*', end='')
    sys.stdout.flush()
    time.sleep(1)
print()

temp = subprocess.getoutput(
    "/home/pi/.nvm/versions/node/v11.14.0/bin/ds18b20 -f -d 2")
battery = pj.status.GetChargeLevel()

# Do the work
for i in range(workTime):
    print('*', end='')
    sys.stdout.flush()
    time.sleep(1)
print()

# Set RTC alarm DELTA_MIN minutes from now
# RTC is kept in UTC
a = {}
a['year'] = 'EVERY_YEAR'
a['month'] = 'EVERY_MONTH'
a['day'] = 'EVERY_DAY'
a['hour'] = 'EVERY_HOUR'
t = datetime.datetime.utcnow()
a['minute'] = (t.minute + DELTA_MIN) % 60
a['second'] = 0
status = pj.rtcAlarm.SetAlarm(a)
if status['error'] != 'NO_ERROR':
    print('Cannot set alarm\n')
    sys.exit()
else:
    print('Alarm set for ' + str(pj.rtcAlarm.GetAlarm()))

# Enable wakeup, otherwise power to the RPi will not be
# applied when the RTC alarm goes off
pj.rtcAlarm.SetWakeupEnabled(True)
time.sleep(0.4)

timestampEnd = int(time.time())

data['temps'].append({
    'start': str(timestampStart),
    'temp': temp,
    'end': str(timestampEnd),
    'battery': battery['data'],
})

# dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
# table = dynamodb.Table('dataLogger')

# response = table.put_item(
#     Item={
#         'id': "ds18b20",
#         'date': timestampStart,
#         'battery': decimal.Decimal(battery['data']),
#         'temp': temp,
#     })

mutation = '''
    mutation createData($createdatainput: CreateDataInput!) {
        createData(input: $createdatainput) { id date temp battery }
    }
'''

variables = {
    'createdatainput': {
        'date': timestampStart,
        'deviceID': 'ds18b20',
        'battery': decimal.Decimal(battery['data']),
        'temp': re.findall("\d+\.\d+", temp)[0],
    }
}

result = run_query(mutation, variables)  # execute query
print("Graphql Create Data Succeeded:")
print(json.dumps(result, indent=4, cls=DecimalEncoder))

# print("PutItem succeeded:")
# print(json.dumps(response, indent=4, cls=DecimalEncoder))

# with open('/home/pi/data.json', 'w') as outfile:
#     json.dump(data, outfile)

# subprocess.call(["/usr/bin/aws", "s3", "cp", "./data.json", "s3://justinleviwinter"])

# PiJuice shuts down power to Rpi after 20 sec from now
# This leaves sufficient time to execute the shutdown sequence
pj.power.SetPowerOff(20)
subprocess.call(["sudo", "poweroff"])
