import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import { Code, ILayerVersion } from "@aws-cdk/aws-lambda";

export default function(stack: cdk.Stack, layers: ILayerVersion[]) {
    return new lambda.Function(stack, 'definitions-handler', {
        functionName: 'infra-mywarmind-definitions',
        code: Code.fromAsset('../services/definitions'),
        layers,
        runtime: lambda.Runtime.PYTHON_3_8,
        handler: 'lambda_function.lambda_handler'
    });
}
