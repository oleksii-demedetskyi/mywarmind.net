import json
import requests
import boto3
from boto3.dynamodb.types import TypeDeserializer
from boto3.dynamodb.types import TypeSerializer

import copy

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

import decimal

dynamodb = boto3.client('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 == 0: return int(o)
            else: return float(o)
        return super(DecimalEncoder, self).default(o)


def extractCookies(event):
    cookiesHeader = event["headers"]["cookie"]

    cookiesItems = cookiesHeader.split("; ")

    cookies = {}
    for item in cookiesItems:
        parts = item.split("=", 1)
        cookies[parts[0]] = parts[1]

    return cookies

def fetchItems(hashes, projections, l18n = 'en'):
    projections.append("#h")

    serializer = TypeSerializer()
    keys = [
        {
            'partition': serializer.serialize(f'{l18n}#{component}#{hash}'),
            'sort': serializer.serialize('version#current')
        }
        for component in hashes
        for hash in hashes[component]
    ]
    print(keys)

    result = []

    while len(keys) > 0:
        bulk = keys[:100]
        keys = keys[100:]

        # call bulk get
        response = dynamodb.batch_get_item(
            ReturnConsumedCapacity = 'TOTAL',
            RequestItems = {
                'mywarmind': {
                    'Keys': bulk,
                    'ProjectionExpression': ", ".join(projections),
                    'ExpressionAttributeNames': {
                        '#h': 'hash'
                    }
                }
            }
        )

        def deserializeItem(item):
            deserializer = TypeDeserializer()
            return {k: deserializer.deserialize(v) for k,v in item.items()}

        result.extend(list(map(deserializeItem, response['Responses']['mywarmind'])))
        del response['Responses']
        print(json.dumps(response, cls=DecimalEncoder))

    return dict((int(item['hash']), item) for item in result)


def lambda_handler(event, context):
    print(json.dumps(event))

    domain = event['requestContext']['domainName']

    if not 'cookie' in event['headers']:
        print("ABORT: Missing 'cookie' header")
        return {
            'statusCode': 301,
            'headers': {
                'Location': f"https://{domain}/auth"
            }
        }

    cookies = extractCookies(event)

    if not 'access_token' in cookies:
        print("ABORT: Missing 'access_token' cookie")
        return {
            'statusCode': 301,
            'headers': {
                'Location': f"https://{domain}/auth"
            }
        }

    if not 'membership_id' in cookies:
        print("ABORT: Missing 'membership_id' cookie")
        return {
            'statusCode': 301,
            'headers': {
                'Location': f"https://{domain}/auth"
            }
        }

    access_token = cookies["access_token"]
    membership_id = cookies["membership_id"]

    profilesResponse = requests.get(f"https://www.bungie.net/Platform/Destiny2/254/Profile/{membership_id}/LinkedProfiles/?getAllMemberships=true",
        headers = {
            "X-API-Key": "bd3737a7d95844128b10bb59a8f25d91",
            "Authorization": f"Bearer {access_token}"
        }
    )

    if profilesResponse.status_code == 401:
        print("ABORT: Profile stus code is 401")
        return {
            'statusCode': 301,
            'headers': {
                'Location': f"https://{domain}/auth"
            }
        }

    if profilesResponse.status_code != 200:
        print(profilesResponse.text)
        return {
            'statusCode': 500,
            'body': json.dumps(profilesResponse.json(), indent = 2)
        }

    profiles = profilesResponse.json()
    primaryProfileMembershipId = profiles['Response']['profiles'][0]['membershipId']

    components = "Profiles,Characters,CharacterEquipment,CharacterInventories,ItemObjectives,ItemInstances,ItemPerks,ItemStats,ItemSockets,ItemPlugStates,ItemTalentGrids,ItemCommonData,ProfileInventories,ItemReusablePlugs,ItemPlugObjectives"
    profileResponse = requests.get(f"https://www.bungie.net/Platform/Destiny2/2/Profile/{primaryProfileMembershipId}/?components={components}",
        headers = {
            "X-API-Key": "bd3737a7d95844128b10bb59a8f25d91",
            "Authorization": f"Bearer {access_token}"
        }
    )

    if profileResponse.status_code != 200: return {
        'statusCode': 500,
        'body': json.dumps(profileResponse.json(), indent = 2)
    }

    profile = profileResponse.json()

    allInstances = profile['Response']['itemComponents']['instances']['data']
    perks = profile['Response']['itemComponents']['perks']['data']
    stats = profile['Response']['itemComponents']['stats']['data']
    sockets = profile['Response']['itemComponents']['sockets']['data']
    plugs = profile['Response']['itemComponents']['reusablePlugs']['data']


    characterEquipment = profile['Response']['characterEquipment']['data']
    characterInventories = profile['Response']['characterInventories']['data']
    profileInventory = profile['Response']['profileInventory']['data']

    weapons = {}
    itemsHashes = set()
    plugHashes = set()

    def addWeapon(item):
        instance = item['itemInstanceId']
        item = {
            'hash': item['itemHash'],
            'damageType': allInstances[instance]['damageTypeHash'],
            'sockets': sockets[instance]['sockets'],
            'plugs': plugs.get(instance, {'plugs': {}})['plugs']
        }

        weapons[str(instance)] = item

        itemsHashes.add(item['hash'])

        for socket in item['sockets']:
            if not 'plugHash' in socket: continue
            plugHashes.add(socket['plugHash'])

        for socket in item['plugs']:
            for plug in item['plugs'][socket]:
                plugHashes.add(plug['plugItemHash'])


    for character in characterEquipment:
        for item in characterEquipment[character]['items']:
            if not 'itemInstanceId' in item: continue
            instanceID = item['itemInstanceId']
            if not 'primaryStat' in allInstances[instanceID]: continue
            if not allInstances[instanceID]['primaryStat']['statHash'] == 1480404414: continue

            item['$character'] = character
            item['$location'] = "equipment"
            addWeapon(item)

    for character in characterInventories:
        for item in characterInventories[character]['items']:
            if not 'itemInstanceId' in item: continue
            instanceID = item['itemInstanceId']
            if not 'primaryStat' in allInstances[instanceID]: continue
            if not allInstances[instanceID]['primaryStat']['statHash'] == 1480404414: continue

            item['$character'] = character
            item['$location'] = "inventory"
            addWeapon(item)

    for item in profileInventory['items']:
        if not 'itemInstanceId' in item: continue
        instanceID = item['itemInstanceId']
        if not 'primaryStat' in allInstances[instanceID]: continue
        if not allInstances[instanceID]['primaryStat']['statHash'] == 1480404414: continue

        item['$location'] = "vault"
        addWeapon(item)


    itemsDefinitions = fetchItems({'DestinyInventoryItemDefinition': itemsHashes}, [
        'displayProperties',
        'equippingBlock.ammoType',
        'itemCategoryHashes'
    ])

    plugDefinitions = fetchItems({'DestinyInventoryItemDefinition': plugHashes}, [
        'displayProperties',
        'itemCategoryHashes',
        'investmentStats',
        'perks'
    ])

    categoriesHashes = set()

    for hash in itemsDefinitions: categoriesHashes.update(itemsDefinitions[hash]['itemCategoryHashes'])
    for hash in plugDefinitions: categoriesHashes.update(plugDefinitions[hash]['itemCategoryHashes'])

    categoriesDefinitions = fetchItems({'DestinyItemCategoryDefinition': categoriesHashes}, [
        'displayProperties'
    ])

    instancesByCategories = {}

    for instance in weapons:
        hash = weapons[instance]['hash']
        categories = itemsDefinitions[hash]['itemCategoryHashes']

        for category in categories:
            category = int(category)

            if category == 1: continue # ignore general weapons category

            if not category in instancesByCategories: instancesByCategories[category] = []
            instancesByCategories[category].append(instance)

    result = {
        'items': weapons,
        'definitions': {
            'items': itemsDefinitions,
            'plugs': plugDefinitions,
            'categories': categoriesDefinitions
        },
        'instancesByCategories': instancesByCategories
    }

    return {
        'statusCode': 200,
        'body': json.dumps(result, cls=DecimalEncoder)
    }
