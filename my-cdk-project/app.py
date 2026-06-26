#!/usr/bin/env python3
import os

import aws_cdk as cdk

from my_cdk_project.my_cdk_project_stack import CarbonMappingStack


app = cdk.App()
CarbonMappingStack(app, "MyCdkProjectStack",


    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION'),
    ),
    )

app.synth()
