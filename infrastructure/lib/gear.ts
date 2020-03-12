import * as cdk from "@aws-cdk/core";
import { LambdaIntegration, RestApi } from "@aws-cdk/aws-apigateway";
import * as lambda from "@aws-cdk/aws-lambda";
import { Code, ILayerVersion } from "@aws-cdk/aws-lambda";

export default function(stack: cdk.Stack, api: RestApi, layers: ILayerVersion[]) {
    const handler = new lambda.Function(stack, 'gear-handler', {
        code: Code.fromInline('../services/gear.py'),
        layers,
        runtime: lambda.Runtime.PYTHON_2_7,
        handler: 'lambda_function.lambda_handler'
    });

    const gear = api.root.addResource('gear')
    gear.addMethod('GET', new LambdaIntegration(handler))
}
