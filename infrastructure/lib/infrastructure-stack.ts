import * as cdk from '@aws-cdk/core';
import auth from './auth'
import * as apiGateway from "@aws-cdk/aws-apigateway";
import gear from "./gear";
import { LayerVersion } from "@aws-cdk/aws-lambda";
import transfer from "./transfer";
import weapons from "./weapons";
import updateManifest from "./update-manifest"
import { AwsIntegration } from "@aws-cdk/aws-apigateway";
import * as iam from '@aws-cdk/aws-iam'
import { Bucket } from "@aws-cdk/aws-s3";
import * as s3Deploy from '@aws-cdk/aws-s3-deployment'
import { ServicePrincipal } from "@aws-cdk/aws-iam";

export class InfrastructureStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const kLayers = LayerVersion.fromLayerVersionArn(this, 'k-layers', 'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-requests:2');
    const xRay = LayerVersion.fromLayerVersionArn(this, 'x-ray', 'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-aws-xray-sdk:14');
    const layers = [kLayers, xRay]

    const api = new apiGateway.RestApi(this, 'warmind-gateway', { restApiName: 'infra-mywarmind' });

    const bucket = new Bucket(this, 'infra-mywarmind')
    new s3Deploy.BucketDeployment(this, 'infra-mywarmind-bucket-deploy', {
      sources: [s3Deploy.Source.asset('../public')],
      destinationBucket: bucket
    })

    const role = new iam.Role(this, 'infra-mywarmind-read-s3', { assumedBy: new ServicePrincipal('s3')})
    bucket.grantRead(role)

    const s3Integration = new AwsIntegration( { service: 's3', path: 'mywarmind.net/index.html', options: { credentialsRole: role }})
    api.root.addMethod('GET', s3Integration)

    auth(this, api, layers)
    gear(this, api, layers)
    transfer(this, api, layers)
    weapons(this, api, layers)
    updateManifest(this, layers)
  }
}
