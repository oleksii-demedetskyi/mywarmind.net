import { countResources, countResourcesLike, expect, haveResource, SynthUtils } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import Infrastructure = require('../lib/infrastructure-stack');

const stack = new Infrastructure.InfrastructureStack(new cdk.App(), 'MyTestStack');

describe('My Warmind stack', () => {
    // WTF - this is not working!!!
    // @ts-ignore
    // expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot()

    test('have rest api', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::RestApi', {
            Name: 'infra-mywarmind'
        }))
        expect(stack).to(countResources('AWS::ApiGateway::RestApi', 1))
    })

    test('have deployment', () => {
        expect(stack).to(countResources('AWS::ApiGateway::Deployment', 1))
    })

    test('have stage', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Stage', {
            StageName: 'prod'
        }))
        expect(stack).to(countResources('AWS::ApiGateway::Stage', 1))
    })

    test('have auth resource', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Resource', 1, { PathPart: 'auth' }))
    })

    test('have auth \'GET\' method', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Method', 1, {
            HttpMethod: 'GET',
            ResourceId: { Ref: 'warmindgatewayauth3C800945' }
        }))
    })

    test('have gear resource', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Resource', 1, { PathPart: 'gear' }))
    })

    test('have gear \'GET\' method', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Method', 1, {
            HttpMethod: 'GET',
            ResourceId: { Ref: 'warmindgatewaygear62B3BCF2' }
        }))
    })

    test('have transfer resource', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Resource', 1,  { PathPart: 'transfer' }))
    })

    test('have transfer \'GET\' method', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Method', 1,{
            HttpMethod: 'GET',
            ResourceId: { Ref: 'warmindgatewaytransfer4F283CFB' }
        }))
    })

    test('have weapons resource', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Resource', 1, { PathPart: 'weapons' }))
    })

    test('have weapons \'GET\' method', () => {
        expect(stack).to(countResourcesLike('AWS::ApiGateway::Method', 1, {
            HttpMethod: 'GET',
            ResourceId: { Ref: 'warmindgatewayweapons4ADADDFD' }
        }))
    })

    const lambdaEnvironment = {
        Handler: 'lambda_function.lambda_handler',
        Runtime: 'python3.8',
        Layers: [
            "arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-requests:2",
            "arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-aws-xray-sdk:14"
        ]
    }

    test('have gear lambda', () => {
        expect(stack).to(countResourcesLike('AWS::Lambda::Function',1,{
            FunctionName: 'infra-mywarmind-gear',
            ...lambdaEnvironment,
        }))
    })

    test('have auth lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            FunctionName: 'infra-mywarmind-auth',
            ...lambdaEnvironment
        }))
    })

    test('have transfer lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            FunctionName: 'infra-mywarmind-transfer',
            ...lambdaEnvironment
        }))
    })

    test('have weapons lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            FunctionName: 'infra-mywarmind-weapons',
            ...lambdaEnvironment
        }))
    })

    test('have update manifest lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            FunctionName: 'infra-mywarmind-update-manifest',
            ...lambdaEnvironment
        }))
    })
})
