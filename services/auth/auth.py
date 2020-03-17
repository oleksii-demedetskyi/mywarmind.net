import requests
import json

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

def lambda_handler(event, context):
    print(json.dumps(event))

    if event['queryStringParameters'] == None:
        print("ABORT: Missing queryStringParameters")
        return {
            'statusCode': 301,
            'headers': {
                'Location': "https://www.bungie.net/en/OAuth/Authorize?client_id=30989&response_type=code"
            }
        }

    if not 'code' in event['queryStringParameters']:
        print("ABORT: Missing code in queryStringParameters")
        return {
            'statusCode': 301,
            'headers': {
                'Location': "https://www.bungie.net/en/OAuth/Authorize?client_id=30989&response_type=code"
            }
        }

    response = requests.post(
       'https://www.bungie.net/platform/app/oauth/token/',
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data = {
            "grant_type": "authorization_code",
            "code": event['queryStringParameters']['code'],
            "client_id": "30989"
        }
    )

    if not response.status_code == 200:
        print("ABORT: Unsuccessfull request")
        return {
            'statusCode': 500,
            'body': response.text
        }

    tokenResponse = response.json()

    token = tokenResponse['access_token']
    membership_id = tokenResponse['membership_id']

    return {
        'statusCode': 301,
        'multiValueHeaders': {
            'Set-Cookie': [
                f"access_token={token}; Secure; HttpOnly",
                f"membership_id={membership_id}; Secure; HttpOnly"
            ]
        },
        'headers': {
            'Location': f"https://{event['requestContext']['domainName']}/",
        }
    }
