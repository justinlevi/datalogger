from __future__ import print_function

import time
import pijuice
import subprocess
import datetime
import os
import sys
import json
import argparse
import boto3
import decimal

# Helper class to convert a DynamoDB item to JSON.


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

DELTA_MIN = 5

with open('/home/pi/data.json') as json_file:
    data = json.load(json_file)

# Rely on RTC to keep the time
subprocess.call(["sudo", "hwclock", "--hctosys"])

# Record start time
start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

# Set RTC alarm 5 minutes from now
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

end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

data['temps'].append({
    'start': start,
    'temp': temp,
    'end': end,
    'battery': battery['data'],
})


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('dataLogger')

response = table.put_item(
    Item={
        'start': start,
        'temp': decimal.Decimal(temp),
        'end': end,
        'battery': decimal.Decimal(battery['data']),
    }
)

print("PutItem succeeded:")
print(json.dumps(response, indent=4, cls=DecimalEncoder))


with open('/home/pi/data.json', 'w') as outfile:
    json.dump(data, outfile)

subprocess.call(["/usr/bin/aws", "s3", "cp",
                 "./data.json", "s3://justinleviwinter"])

# PiJuice shuts down power to Rpi after 20 sec from now
# This leaves sufficient time to execute the shutdown sequence
pj.power.SetPowerOff(20)
subprocess.call(["sudo", "poweroff"])
