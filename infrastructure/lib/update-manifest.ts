import * as cdk from "@aws-cdk/core";
import { LambdaIntegration, RestApi } from "@aws-cdk/aws-apigateway";
import * as lambda from '@aws-cdk/aws-lambda';
import { ILayerVersion, Code } from "@aws-cdk/aws-lambda";

export default function(stack: cdk.Stack, layers: ILayerVersion[]) {
    new lambda.Function(stack, 'update-manifest-handler', {
        functionName: 'UpdateManifest',
        code: Code.fromAsset('../services/update-manifest'),
        layers,
        runtime: lambda.Runtime.PYTHON_3_8,
        handler: 'lambda_function.lambda_handler'
    });
}
