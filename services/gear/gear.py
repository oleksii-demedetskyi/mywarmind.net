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
    print(json.dumps(profiles))
    primaryProfileMembershipId = profiles['Response']['profiles'][0]['membershipId']

    membershipType = profiles['Response']['profiles'][0]['membershipType']
    components = "Profiles,Characters,CharacterEquipment,CharacterInventories,ItemObjectives,ItemInstances,ItemPerks,ItemStats,ItemSockets,ItemPlugStates,ItemTalentGrids,ItemCommonData,ProfileInventories,ItemReusablePlugs,ItemPlugObjectives"
    profileResponse = requests.get(f"https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/{primaryProfileMembershipId}/?components={components}",
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

    allCharacters = profile['Response']['characterInventories']['data'].keys()
    print(allCharacters)

    items = profile['Response']['profileInventory']['data']['items']
    for item in items:
        item['source'] = 'vault'

        # Items from vault can be moved to 3 characters
        item['transfers'] = [c for c in allCharacters]

    print(f"Items in vault: {len(items)}")
    for character in profile['Response']['characterInventories']['data']:
        characterItems = profile['Response']['characterInventories']['data'][character]['items']

        for item in characterItems:
            item['source'] = character

            # Items on this character can be moved to vault and other characters
            item['transfers'] = [c for c in allCharacters if c != character] + ['vault']

        print(f"Items in character ({character}): {len(characterItems)}")
        items.extend(characterItems)

    for character in profile['Response']['characterEquipment']['data']:
        characterItems = profile['Response']['characterEquipment']['data'][character]['items']

        for item in characterItems:
            item['source'] = 'equipment'

        items.extend(characterItems)

    hashes = list(set(map(lambda item: item['itemHash'], items)))

    def fetchItems(hashes, projections, l18n = 'en'):
        projections.append("#h")
        print(projections)

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
                    'mywarmind-table': {
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

    itemsDefinitions = fetchItems({'DestinyInventoryItemDefinition': hashes}, [
        'displayProperties',
        'itemTypeAndTierDisplayName',
        'itemCategoryHashes',
    ])

    itemsCategoriesHashes = list(set([hash
        for item in itemsDefinitions.values()
        if 'itemCategoryHashes' in item
        for hash in item['itemCategoryHashes']
    ]))

    itemsCategories = fetchItems({'DestinyItemCategoryDefinition': itemsCategoriesHashes}, [
        'displayProperties'
    ])

    for definition in itemsDefinitions.values():
        if 'itemCategoryHashes' in definition:
            definition['itemCategoryHashes'] = [
                itemsCategories[hash] for hash in definition['itemCategoryHashes']
            ]

    for item in items:
        item['itemHash'] = itemsDefinitions.get(item['itemHash'], None)


    allStats = profile['Response']['itemComponents']['stats']['data']

    statHashes = list(set([stat['statHash']
        for item in allStats.values()
        for stat in item['stats'].values()
    ]))

    stats = fetchItems({'DestinyStatDefinition': statHashes}, [
        'displayProperties'
    ])

    for itemStats in allStats.values():
        for stat in itemStats['stats'].values():
            stat['statHash'] = stats[stat['statHash']]

    instances = profile['Response']['itemComponents']['instances']['data']

    armors = [item
        for item in items
        if item['itemHash'] != None #Filter for unknown armor. TODO: Remov
        if 'itemCategoryHashes' in item['itemHash']
        for category in item['itemHash']['itemCategoryHashes']
        if category['hash'] == 20 #Armor only
        if 'energy' in instances[item['itemInstanceId']]
    ]

    for armor in armors:
        if armor['itemInstanceId'] in allStats:
            armor['stats'] = allStats[armor['itemInstanceId']]


    statMap = {
        'mobility': 2996146975,
        'resilence': 392767087,
        'recovery': 1943323491,
        'discipline': 1735777505,
        'intellect': 144602215,
        'strength': 4244567218
    }

    classMap = {
        'warlock': 21,
        'titan': 22,
        'hunter': 23
    }

    slotMap = {
        'helmet': 45,
        'arms': 46,
        'chest': 47,
        'legs': 48,
        'class': 49
    }

    energyMap = {
        'arc': 728351493,
        'solar': 591714140,
        'void': 4069572561
    }

    itemStats = {
        item['itemInstanceId']: {
            stat: allStats[item['itemInstanceId']]['stats'][str(statMap[stat])]['value']
            for stat in statMap
        }
        for item in armors
        if item['itemInstanceId'] in allStats
    }

    baseStats = copy.deepcopy(itemStats)

    perksImpact = {
        # Stat mods
        1529760605: {
            'mobility': 10
        },
        3401516887: {
            'recovery': 10
        },
        1348768469: {
            'resilence': 10
        },
        3235178396: {
            'discipline': 10
        },
        2690172198: {
            'intellect': 10
        },
        1247690169: {
            'strength': 10
        },

        #Traction
        2993362303: {
            'mobility': 5
        }
    }

    # deduct stat giving perks
    allPerks = profile['Response']['itemComponents']['perks']['data']
    for item in armors:
        if not item['itemInstanceId'] in allPerks: continue
        if not item['itemInstanceId'] in baseStats: continue

        perks = allPerks[item['itemInstanceId']]['perks']
        for perk in perks:
            print
            if not perk['perkHash'] in perksImpact: continue

            impacts = perksImpact[perk['perkHash']]
            for impact in impacts:
                baseStats[item['itemInstanceId']][impact] -= impacts[impact]

    # deduct masterwork bonuses
    for item in armors:
        if instances[item['itemInstanceId']]['energy']['energyCapacity'] != 10: continue
        if not item['itemInstanceId'] in baseStats: continue

        for stat in baseStats[item['itemInstanceId']]:
            baseStats[item['itemInstanceId']][stat] -= 2

    # find trash

    def classOfItem(item):
        for category in item['itemCategoryHashes']:
            for clazz in classMap:
                if category['hash'] == classMap[clazz]:
                    return clazz
        return None

    def slotOfItem(item):
        for category in item['itemCategoryHashes']:
            for slot in slotMap:
                if category['hash'] == slotMap[slot]:
                    return slot
        return None

    def energyOfItem(item):
        for energy in energyMap:
            if item['energy']['energyTypeHash'] == energyMap[energy]:
                return energy
        return None

    totals = {
        item: sum(baseStats[item].values())
        for item in baseStats
    }

    groups = {
        clazz: {
            slot: {
                energy: [
                    item['itemInstanceId']
                    for item in armors
                    if energyOfItem(instances[item['itemInstanceId']]) == energy
                    if slotOfItem(itemsDefinitions[item['itemHash']['hash']]) == slot
                    if classOfItem(itemsDefinitions[item['itemHash']['hash']]) == clazz
                ]
                for energy in energyMap
            }
            for slot in slotMap
        }
        for clazz in classMap
    }

    trash = {}
    def checkForTrash(item, another):
        if not item in baseStats: return
        if not another in baseStats: return
        itemStats = baseStats[item]
        anotherStats = baseStats[another]

        if sum(itemStats.values()) > sum(anotherStats.values()):
            return

        for stat in itemStats:
            if itemStats[stat] - 2 > anotherStats.get(stat, 0): return

        if not item in trash:
            trash[item] = []

        trash[item].append(another)

    # search for trash rolls
    for clazz in classMap:
        for slot in slotMap:
            for energy in energyMap:
                for item in groups[clazz][slot][energy]:
                    for another in groups[clazz][slot][energy]:
                        if item == another: continue
                        checkForTrash(item, another)


    def formTransferAction(item, destination):
        instance = item['itemInstanceId']
        hash = item['itemHash']['hash']
        action = f"/transfer?instance={instance}&hash={hash}"

        if item['source'] != 'vault':
            action += f"&from={item['source']}"

        if destination != 'vault':
            action += f"&to={destination}"

        return {
            'action': action,
            'destination': destination
        }

    result = {
        "items": { item['itemInstanceId']: {
            'transfers': [
                formTransferAction(item, t)
                for t in item.get('transfers', [])
            ],
            'source': item.get('source', None),
            'hash': item['itemHash']['hash'],
            'total': totals.get(item['itemInstanceId'], 0),
            'stats': baseStats.get(item['itemInstanceId'], {}),
            'defence': instances[item['itemInstanceId']]['primaryStat']['value'],
            'energy': energyOfItem(instances[item['itemInstanceId']]),
            'capacity': instances[item['itemInstanceId']]['energy']['energyCapacity']
        } for item in armors },
        "displayProperties": {
            "defence": fetchItems({'DestinyStatDefinition': [3897883278]}, ['displayProperties'])[3897883278]['displayProperties'],
            "items": {
                hash: itemsDefinitions[hash]['displayProperties']
                for hash in set([int(item['itemHash']['hash']) for item in armors])
            },
            "stats": {
                stat: stats[statMap[stat]]['displayProperties'] for stat in statMap
            },
            "class": {
                clazz: itemsCategories[classMap[clazz]]['displayProperties']
                for clazz in classMap
                if classMap[clazz] in itemsCategories
            },
            "slots": {
                slot: itemsCategories[slotMap[slot]]['displayProperties']
                for slot in slotMap
                if slotMap[slot] in itemsCategories
            },
            "energy": {
                energy: fetchItems({'DestinyEnergyTypeDefinition': [energyMap[energy]]}, ['displayProperties'])[energyMap[energy]]['displayProperties']
                for energy in energyMap
            }
        },
        "groups": groups,
        "trash": trash
    }

    return {
        'statusCode': 200,
        'body': json.dumps(result, cls=DecimalEncoder)
    }
