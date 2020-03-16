import { expect, SynthUtils } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import Infrastructure = require('../lib/infrastructure-stack');

test('MyWarmind Stack', () => {
    const stack = new Infrastructure.InfrastructureStack(new cdk.App(), 'MyTestStack');
    // @ts-ignore
    expect(SynthUtils.toCloudFormation(stack)).toMatchSnapshot()
});

// test('MyWarmind ApiGateway', () => {
//
// })

