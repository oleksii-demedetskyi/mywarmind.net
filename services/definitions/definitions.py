import json
import requests
import boto3
import copy
from collections import OrderedDict
from decimal import Decimal

def dynamify(raw):
    if isinstance(raw, dict):
        for key in raw.copy():
            raw[key] = dynamify(raw[key])
            if raw[key] == None: del raw[key]
        if len(raw) == 0: return None

    elif isinstance(raw, list):
        for i in range(len(raw)): raw[i] = dynamify(raw[i])
        raw = list(filter(None, raw))
        if len(raw) == 0: return None

    elif isinstance(raw, float):
        return Decimal(str(raw))
    elif raw == "":
        return None
    return raw

componentsWhitelist = [
    'DestinyInventoryItemDefinition',
    'DestinyItemCategoryDefinition',
    'DestinyStatDefinition',
    'DestinyEnergyTypeDefinition'
]

def lambda_handler(event, context):
    print(json.dumps(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    print(json.dumps(message))

    sns = boto3.client('sns')

    if message['action'] == "refresh":
        manifests = requests.get("https://www.bungie.net/Platform/Destiny2/Manifest/").json()
        version = manifests['Response']['version']

        l18ns = manifests['Response']['jsonWorldComponentContentPaths']
        for l18n in l18ns:
            manifest = manifests['Response']['jsonWorldComponentContentPaths'][l18n]
            for component in componentsWhitelist:
                if not component in manifest: continue
                path = f"https://www.bungie.net{manifest[component]}"

                action = {
                    "action": "load_component",
                    "component": component,
                    "language": l18n,
                    "start": 0,
                    "path": path,
                    "version": version
                }

                print(json.dumps(action))

                sns.publish(
                  TopicArn='arn:aws:sns:us-east-2:956931160472:mywarmind-definitions-import',
                    Message=json.dumps(action),
                )

    if message['action'] == "load_component":
        response = requests.get(message['path'], headers = {
            "Accept-Encoding": "gzip, deflate"
        })

        component = response.json(object_pairs_hook=OrderedDict)

        size = len(component)
        start = message['start']
        end = min(start + 1000, size)

        chunk = list(component.keys())[start:end]
        print(f"PROCESSING {message['component']}: {start} - {end}")

        dynamoDB = boto3.resource('dynamodb')
        table = dynamoDB.Table("infra-mywarmind")

        with table.batch_writer() as batch:
            for hash in chunk:
                item = component[hash]
                item['partition'] = f'{message["language"]}#{message["component"]}#{hash}'

                item['sort'] = 'version#current'
                batch.put_item(Item = dynamify(item))

                item = copy.deepcopy(item)

                item['sort'] = f"version#{message['version']}"
                batch.put_item(Item = dynamify(item))

        if end < size:
            action = message
            action['start'] = end

            sns.publish(
                TopicArn='arn:aws:sns:us-east-2:956931160472:mywarmind-definitions-import',
                Message=json.dumps(action),
            )
