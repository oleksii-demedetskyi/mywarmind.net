import * as cdk from "@aws-cdk/core";
import * as dynamodb from "@aws-cdk/aws-dynamodb";
import { AttributeType, BillingMode } from "@aws-cdk/aws-dynamodb";

export function general(stack: cdk.Stack) {
    new dynamodb.Table(stack, 'mywarmind-table', {
        partitionKey: { name: 'partition', type: AttributeType.STRING },
        sortKey: { name: 'sort', type: AttributeType.STRING },
        billingMode: BillingMode.PAY_PER_REQUEST,
    })
}

export function definitions(stack: cdk.Stack) {
    new dynamodb.Table(stack, 'definitions-table', {
        partitionKey: { name: 'partition', type: AttributeType.STRING },
        sortKey: { name: 'sort', type: AttributeType.STRING },
        billingMode: BillingMode.PAY_PER_REQUEST,
    })
}
