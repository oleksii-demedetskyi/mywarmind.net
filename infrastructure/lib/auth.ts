import * as cdk from '@aws-cdk/core';
import * as lambda from '@aws-cdk/aws-lambda';
import { Code, ILayerVersion } from "@aws-cdk/aws-lambda";
import { AwsIntegration, LambdaIntegration, RestApi } from "@aws-cdk/aws-apigateway";

export default function(stack: cdk.Stack, api: RestApi, layers: ILayerVersion[]) {
    const handler = new lambda.Function(stack, 'auth-handler', {
        functionName: 'infra-mywarmind-auth',
        code: Code.fromAsset('../services/auth'),
        layers,
        runtime: lambda.Runtime.PYTHON_3_8,
        handler: 'lambda_function.lambda_handler'
    });

    // WTF - this isn't working - gives error - "The REST API doesn't contain any methods"
    // const method = api.root.addMethod('GET', new AwsIntegration( { service: 's3' } ))

    const auth = api.root.addResource('auth')
    auth.addMethod('GET', new LambdaIntegration(handler))
}
