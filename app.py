#!/usr/bin/env python3
import aws_cdk as cdk

from test.test_stack import TestStack

app = cdk.App()

TestStack(app, "TestStack")

app.synth()
