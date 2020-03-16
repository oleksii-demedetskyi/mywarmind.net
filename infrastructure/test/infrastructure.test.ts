import { expect, haveResource, SynthUtils } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import Infrastructure = require('../lib/infrastructure-stack');

test('MyWarmind Stack', () => {
    // WTF - this is not working!!!
    // expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot()
    const stack = new Infrastructure.InfrastructureStack(new cdk.App(), 'MyTestStack');
    expect(stack).to(haveResource('AWS::ApiGateway::RestApi', {
        Name: 'mywarmind'
    }))
    expect(stack).to(haveResource('AWS::ApiGateway::Deployment'))
    expect(stack).to(haveResource('AWS::ApiGateway::Stage', {
        StageName: 'prod'
    }))
    expect(stack).to(haveResource('AWS::ApiGateway::Resource', {
        PathPart: 'auth'
    }))
    expect(stack).to(haveResource('AWS::ApiGateway::Method', {
        HttpMethod: 'GET',
    }))
    expect(stack).to(haveResource('AWS::Lambda::Function', {
        Code: {
            ZipFile: '../services/auth.py'
        },
        Handler: 'lambda_function.lambda_handler',
        Runtime: 'python2.7',
        Layers: [
            "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-requests:8",
            "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-aws-xray-sdk:15"
        ]
    }))
});
