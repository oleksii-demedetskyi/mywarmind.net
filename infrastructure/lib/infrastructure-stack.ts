import * as cdk from '@aws-cdk/core';
import auth from './auth'
import * as apiGateway from "@aws-cdk/aws-apigateway";
import gear from "./gear";
import { LayerVersion } from "@aws-cdk/aws-lambda";
import transfer from "./transfer";
import weapons from "./weapons";
import updateManifest from "./update-manifest"

export class InfrastructureStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const kLayers = LayerVersion.fromLayerVersionArn(this, 'k-layers', 'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-requests:2');
    const xRay = LayerVersion.fromLayerVersionArn(this, 'x-ray', 'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-aws-xray-sdk:14');
    const layers = [kLayers, xRay]

    const api = new apiGateway.RestApi(this, 'warmind-gateway', { restApiName: 'mywarmind' });

    auth(this, api, layers)
    gear(this, api, layers)
    transfer(this, api, layers)
    weapons(this, api, layers)
    updateManifest(this, layers)
  }
}
