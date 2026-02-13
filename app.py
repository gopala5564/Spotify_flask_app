#!/usr/bin/env python3
"""
AWS CDK App Entry Point for Spotify Data Engineering Pipeline

This is the main entry point for the AWS CDK application. It defines the stack
to be deployed to AWS CloudFormation.

Usage:
    cdk synth              # Generate CloudFormation template
    cdk deploy             # Deploy to AWS
    cdk destroy            # Remove from AWS
"""

import os
import aws_cdk as cdk
from infra.spotify_etl_stack import SpotifyEtlStack


def main():
    """Initialize and configure the CDK app"""
    app = cdk.App()
    
    # Create the Spotify ETL Stack
    SpotifyEtlStack(
        app,
        "SpotifyEtlStack",
        env=cdk.Environment(
            account=os.getenv("CDK_DEFAULT_ACCOUNT"),
            region=os.getenv("CDK_DEFAULT_REGION", "us-east-1")
        ),
        description="AWS CDK Stack for Spotify Data Engineering Pipeline with Lambda ETL and S3 Data Lake"
    )
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()
