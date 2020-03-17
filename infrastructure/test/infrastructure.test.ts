import { expect, haveResource } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import Infrastructure = require('../lib/infrastructure-stack');

const stack = new Infrastructure.InfrastructureStack(new cdk.App(), 'MyTestStack');

describe('My Warmind stack', () => {
    // WTF - this is not working!!!
    // expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot()

    test('have rest api', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::RestApi', {
            Name: 'mywarmind'
        }))
    })

    test('have deployment', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Deployment'))
    })

    test('have stage', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Stage', {
            StageName: 'prod'
        }))
    })

    test('have auth resource', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Resource', {
            PathPart: 'auth'
        }))
    })

    test('have auth \'GET\' method', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Method', {
            HttpMethod: 'GET',
        }))
    })

    test('have gear resource', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Resource', {
            PathPart: 'gear'
        }))
    })

    test('have gear \'GET\' method', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Method', {
            HttpMethod: 'GET'
        }))
    })

    test('have transfer resource', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Resource', {
            PathPart: 'transfer'
        }))
    })

    test('have transfer \'GET\' method', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Method', {
            HttpMethod: 'GET'
        }))
    })

    test('have weapons resource', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Resource', {
            PathPart: 'weapons'
        }))
    })

    test('have weapons \'GET\' method', () => {
        expect(stack).to(haveResource('AWS::ApiGateway::Method', {
            HttpMethod: 'GET'
        }))
    })

    test('have gear lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            Handler: 'lambda_function.lambda_handler',
            Runtime: 'python3.8',
            Layers: [
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-requests:8",
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-aws-xray-sdk:15"
            ]
        }))
    })

    test('have auth lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            Handler: 'lambda_function.lambda_handler',
            Runtime: 'python3.8',
            Layers: [
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-requests:8",
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-aws-xray-sdk:15"
            ]
        }))
    })

    test('have transfer lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            Handler: 'lambda_function.lambda_handler',
            Runtime: 'python3.8',
            Layers: [
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-requests:8",
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-aws-xray-sdk:15"
            ]
        }))
    })

    test('have weapons lambda', () => {
        expect(stack).to(haveResource('AWS::Lambda::Function', {
            Handler: 'lambda_function.lambda_handler',
            Runtime: 'python3.8',
            Layers: [
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-requests:8",
                "arn:aws:lambda:us-east-2:113088814899:layer:Klayers-python37-aws-xray-sdk:15"
            ]
        }))
    })
})
