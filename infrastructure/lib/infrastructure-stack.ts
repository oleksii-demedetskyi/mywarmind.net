import * as cdk from '@aws-cdk/core';
import auth from './auth'
import * as apiGateway from "@aws-cdk/aws-apigateway";
import {
    AwsIntegration,
    ContentHandling,
    EmptyModel,
    EndpointType, Model,
    PassthroughBehavior
} from "@aws-cdk/aws-apigateway";
import gear from "./gear";
import { LayerVersion } from "@aws-cdk/aws-lambda";
import transfer from "./transfer";
import weapons from "./weapons";
import updateManifest from "./update-manifest"
import * as iam from '@aws-cdk/aws-iam'
import { ServicePrincipal } from '@aws-cdk/aws-iam'
import { Bucket } from "@aws-cdk/aws-s3";
import * as s3Deploy from '@aws-cdk/aws-s3-deployment'
import { definitions, general } from "./mywarmind-table";
import * as sns from '@aws-cdk/aws-sns'
import * as subs from '@aws-cdk/aws-sns-subscriptions'
import warmindDefinitions from './definitions'

export class InfrastructureStack extends cdk.Stack {
    constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        const api = new apiGateway.RestApi(this, 'warmind-gateway', {
            restApiName: 'infra-mywarmind',
            endpointConfiguration: {types: [EndpointType.REGIONAL]},
            deployOptions: {
                loggingLevel: apiGateway.MethodLoggingLevel.ERROR,
                dataTraceEnabled: true,
                tracingEnabled: true,
                metricsEnabled: true
            }
        });

        const bucket = new Bucket(this, 'infra-mywarmind')
        new s3Deploy.BucketDeployment(this, 'infra-mywarmind-bucket-deploy', {
            sources: [s3Deploy.Source.asset('../public')],
            destinationBucket: bucket
        })

        const role = new iam.Role(this, 'infra-mywarmind-read-s3', { assumedBy: new ServicePrincipal('apigateway') })
        bucket.grantRead(role)

        const s3Integration = new AwsIntegration({
            integrationHttpMethod: "GET",
            service: 's3',
            path: 'mywarmind.net/index.html',
            options: {
                credentialsRole: role,
                requestParameters: {
                    "integration.request.header.Content-Type": "method.request.header.Content-Type",
                    "integration.request.header.Content-Disposition": "method.request.header.Content-Disposition"
                },
                passthroughBehavior: PassthroughBehavior.WHEN_NO_MATCH,
                integrationResponses: [{
                    statusCode: "200",
                    selectionPattern: "200",
                    responseParameters: {
                        "method.response.header.Content-Type": "integration.response.header.Content-Type",
                        "method.response.header.Content-Disposition": "integration.response.header.Content-Disposition"
                    }
                }]
            },
        })

        api.root.addMethod('GET', s3Integration, {
            requestParameters: {
                "method.request.header.Content-Type": false,
                "method.request.header.Content-Disposition": false
            },
            methodResponses: [{
                statusCode: "200",
                responseParameters: {
                    "method.response.header.Content-Type": false,
                    "method.response.header.Content-Disposition": false
                },
            }]
        })

        const requests = LayerVersion.fromLayerVersionArn(this, 'requests', 'arn:aws:lambda:us-east-2:956931160472:layer:requests:1');
        const xRay = LayerVersion.fromLayerVersionArn(this, 'x-ray', 'arn:aws:lambda:us-east-2:956931160472:layer:aws-xray-sdk:1');
        const layers = [requests, xRay]

        auth(this, api, layers)
        gear(this, api, layers)
        transfer(this, api, layers)
        weapons(this, api, layers)
        updateManifest(this, layers)
        general(this)
        definitions(this)

        const dynamoDbTopic = new sns.Topic(this, 'infra-mywarmind-definitions-import', {
            displayName: 'mywarmind definitions import topic'
        })
        const warmindDefFn = warmindDefinitions(this, layers)
        dynamoDbTopic.addSubscription(new subs.LambdaSubscription(warmindDefFn))
    }
}
