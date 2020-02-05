import requests
import boto3

dynamoDB = boto3.resource('dynamodb')
table = dynamoDB.Table("MyWarmind-Definitions")

manifests = requests.get("https://www.bungie.net/Platform/Destiny2/Manifest/")

print(manifests)

worldPath = manifests.json()['Response']['jsonWorldContentPaths']['en']
world = requests.get(f"https://www.bungie.net{worldPath}").json()
counter = 0

with table.batch_writer() as batch:
    for component in world:
        print(component)
        for hash in world[component]:
            counter += 1
            if counter % 100 == 0: print(counter)
            
            item = world[component][hash]
            item["component"] = component
            
            batch.put_item(Item = dict_to_dynamo(item))

print(counter)