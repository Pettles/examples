#!/usr/bin/env python3
import aws_cdk as cdk

from settings import settings
from test.test_stack import TestStack

app = cdk.App()

# Update settings with context information supplied to CLI or in context files
settings.update_from_context(app)

TestStack(app, "TestStack")

app.synth()
