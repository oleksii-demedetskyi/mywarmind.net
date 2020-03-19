import json
import requests

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()


def lambda_handler(event, context):
    print(json.dumps(event))

    def execute(request):
        print(json.dumps(request))
        response = requests.post("https://www.bungie.net/Platform/Destiny2/Actions/Items/TransferItem/", json = request, headers = {
            "Authorization": f"Bearer {event['token']}",
            "X-API-Key": "bd3737a7d95844128b10bb59a8f25d91"
        })

        print(response.text)
        return response.status_code == 200

    location = None
    if 'from' in event:
        print("moving to vault")
        location = event['from']

        success = execute({
            "characterId": event['from'],
            "itemId": event['instance'],
            "itemReferenceHash": event['hash'],
            "membershipType": 2,
            "stackSize": 1,
            "transferToVault": True
        })

        if success: location = 'vault'
        else: return { "location": location, "success": False }

    if 'to' in event:
        print("moving from vault")
        location = 'vault'

        success = execute({
            "characterId": event['to'],
            "itemId": event['instance'],
            "itemReferenceHash": event['hash'],
            "membershipType": 2,
            "stackSize": 1,
            "transferToVault": False
        })

        if success: location = event['to']
        else: return { "location": location, "success": False }

    return { "location": location, "success": True }
