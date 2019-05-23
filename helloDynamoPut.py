import boto3
import json
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


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('dataLogger')

response = table.put_item(
    Item={
        'date': '5-17-2019:10:53',
        'temp': decimal.Decimal(67.5),
    }
)

print("PutItem succeeded:")
print(json.dumps(response, indent=4, cls=DecimalEncoder))
