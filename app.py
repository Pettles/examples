#!/usr/bin/env python3
import aws_cdk as cdk

from settings import Settings
from test.test_stack import TestStack

app = cdk.App()

# Instantiate the settings object that we will use to configure the stack(s)
# This uses context arguments and environment variables to populate the required attributes
settings = Settings(app=app)

TestStack(app, "TestStack")

app.synth()
