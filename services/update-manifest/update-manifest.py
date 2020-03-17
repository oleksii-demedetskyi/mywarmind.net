import json
import requests
import boto3

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

s3 = boto3.client('s3')
bucket = "manifests.mywarmind.net"

def lambda_handler(event, context):
    manifest = requests.get("https://www.bungie.net/Platform/Destiny2/Manifest/").json()['Response']
    version = manifest['version']

    print(f"Version: {version}")

    objects = s3.list_objects(
        Bucket = bucket,
        Prefix=version,
    ).get('Contents')

    if objects is not None:
        print("Aborting: Already downloaded")
        return

    s3.put_object(
        Bucket = bucket,
        Body = json.dumps(manifest, sort_keys=True, indent=4),
        Key = f"{version}/manifest.json"
    )

    definitions = manifest['jsonWorldContentPaths']
    for language, path in definitions.items():
        print(f"Getting {language} from {path}")
        response = requests.get(f"https://www.bungie.net{path}")
        print(f"Saving {language}")
        s3.put_object(
            Bucket = bucket,
            Body = response.content,
            Key = f"{version}/{language}.json"
        )

    # Store manifest as current manifest
    s3.put_object(
        Bucket = bucket,
        Body = json.dumps(manifest, sort_keys=True, indent=4),
        Key = "manifest.json"
    )
