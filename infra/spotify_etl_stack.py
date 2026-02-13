#!/usr/bin/env python3
"""
AWS CDK Stack for Spotify ETL Data Pipeline

This stack deploys a complete data engineering solution for extracting Spotify data
into a data lake with raw and processed layers, using Lambda for ETL operations.
"""

import os
from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    CfnParameter,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    CfnOutput,
)


class SpotifyEtlStack(Stack):
    """AWS CDK Stack for Spotify ETL Pipeline with raw and processed data layers"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ======================
        # Parameters
        # ======================
        bucket_name_param = CfnParameter(
            self,
            "DataLakeBucketName",
            type="String",
            description="S3 bucket name for data lake (must be globally unique)"
        )
        
        spotify_client_id = CfnParameter(
            self,
            "SpotifyClientId",
            type="String",
            no_echo=True,
            description="Spotify Client ID"
        )
        
        spotify_client_secret = CfnParameter(
            self,
            "SpotifyClientSecret",
            type="String",
            no_echo=True,
            description="Spotify Client Secret"
        )

        # ======================
        # S3 Data Lake Bucket
        # ======================
        data_lake_bucket = s3.Bucket(
            self,
            "DataLakeBucket",
            bucket_name=bucket_name_param.value_as_string,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                # Transition to IA after 30 days
                s3.LifecycleRule(
                    id="TransitionToIA",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                ),
                # Transition to Glacier after 60 days
                s3.LifecycleRule(
                    id="ArchiveToGlacier",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(60)
                        )
                    ]
                ),
                # Delete old versions after 90 days
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(90)
                )
            ]
        )

        # Create data lake folder structure
        data_lake_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                resources=[data_lake_bucket.bucket_arn, f"{data_lake_bucket.bucket_arn}/*"]
            )
        )

        # ======================
        # IAM Roles and Policies
        # ======================
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for Spotify ETL Lambda functions"
        )

        # Attach managed policies
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # S3 access policy
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket",
                    "s3:DeleteObject"
                ],
                resources=[data_lake_bucket.bucket_arn, f"{data_lake_bucket.bucket_arn}/*"]
            )
        )

        # Lambda invoke policy for orchestration
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:spotify-etl-*"
                ]
            )
        )

        # CloudWatch Logs policy
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[f"arn:aws:logs:{self.region}:{self.account}:*"]
            )
        )

        # ======================
        # Lambda Functions
        # ======================
        
        # Common environment variables
        common_env = {
            "DATA_LAKE_BUCKET": data_lake_bucket.bucket_name,
            "SPOTIFY_CLIENT_ID": spotify_client_id.value_as_string,
            "SPOTIFY_CLIENT_SECRET": spotify_client_secret.value_as_string,
        }

        # Lambda code path
        lambda_code_path = os.path.join(os.path.dirname(__file__), "..", "app", "lambdas")

        # Extract Lambda
        extract_fn = _lambda.Function(
            self,
            "ExtractFunction",
            function_name="spotify-etl-extract",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="extract_handler.lambda_handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=3008,
            ephemeral_storage_size=cdk.Size.gibibytes(10),
            environment=common_env,
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="Extracts Spotify data and writes to raw layer"
        )

        # Transform Lambda
        transform_fn = _lambda.Function(
            self,
            "TransformFunction",
            function_name="spotify-etl-transform",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="transform_handler.lambda_handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=3008,
            ephemeral_storage_size=cdk.Size.gibibytes(10),
            environment=common_env,
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="Transforms raw data into structured format"
        )

        # Load Lambda
        load_fn = _lambda.Function(
            self,
            "LoadFunction",
            function_name="spotify-etl-load",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="load_handler.lambda_handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=3008,
            environment=common_env,
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="Loads transformed data into processed layer"
        )

        # Orchestrator Lambda
        orchestrator_fn = _lambda.Function(
            self,
            "OrchestratorFunction",
            function_name="spotify-etl-orchestrator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="orchestrator.lambda_handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            role=lambda_role,
            timeout=Duration.seconds(900),
            memory_size=3008,
            environment=common_env,
            log_retention=logs.RetentionDays.ONE_MONTH,
            description="Orchestrates the complete ETL pipeline"
        )

        # ======================
        # CloudWatch Monitoring
        # ======================
        
        # Extract Lambda metrics
        extract_errors = cloudwatch.Metric(
            metric_name="Errors",
            namespace="AWS/Lambda",
            statistic="Sum",
            period=Duration.minutes(5),
            dimensions_map={"FunctionName": extract_fn.function_name}
        )

        # Transform Lambda metrics
        transform_errors = cloudwatch.Metric(
            metric_name="Errors",
            namespace="AWS/Lambda",
            statistic="Sum",
            period=Duration.minutes(5),
            dimensions_map={"FunctionName": transform_fn.function_name}
        )

        # Load Lambda metrics
        load_errors = cloudwatch.Metric(
            metric_name="Errors",
            namespace="AWS/Lambda",
            statistic="Sum",
            period=Duration.minutes(5),
            dimensions_map={"FunctionName": load_fn.function_name}
        )

        # Orchestrator Lambda metrics
        orchestrator_errors = cloudwatch.Metric(
            metric_name="Errors",
            namespace="AWS/Lambda",
            statistic="Sum",
            period=Duration.minutes(5),
            dimensions_map={"FunctionName": orchestrator_fn.function_name}
        )

        # ======================
        # EventBridge Scheduling
        # ======================
        
        # Daily ETL execution at 2 AM UTC
        etl_schedule = events.Rule(
            self,
            "DailyETLRule",
            schedule=events.Schedule.cron(minute="0", hour="2"),
            description="Daily Spotify ETL pipeline execution at 02:00 UTC"
        )

        etl_schedule.add_target(
            targets.LambdaFunction(orchestrator_fn)
        )

        # Optional: Manual trigger rule (comment in/out as needed)
        # You can invoke this rule via EventBridge console or AWS CLI for testing
        manual_trigger = events.Rule(
            self,
            "ManualETLTrigger",
            description="Manual trigger for ETL pipeline testing"
        )
        manual_trigger.add_target(
            targets.LambdaFunction(orchestrator_fn)
        )

        # ======================
        # Outputs
        # ======================
        CfnOutput(
            self,
            "DataLakeBucketName",
            value=data_lake_bucket.bucket_name,
            description="Name of the S3 data lake bucket"
        )

        CfnOutput(
            self,
            "DataLakeBucketArn",
            value=data_lake_bucket.bucket_arn,
            description="ARN of the S3 data lake bucket"
        )

        CfnOutput(
            self,
            "ExtractFunctionArn",
            value=extract_fn.function_arn,
            description="ARN of the Extract Lambda function"
        )

        CfnOutput(
            self,
            "TransformFunctionArn",
            value=transform_fn.function_arn,
            description="ARN of the Transform Lambda function"
        )

        CfnOutput(
            self,
            "LoadFunctionArn",
            value=load_fn.function_arn,
            description="ARN of the Load Lambda function"
        )

        CfnOutput(
            self,
            "OrchestratorFunctionArn",
            value=orchestrator_fn.function_arn,
            description="ARN of the Orchestrator Lambda function"
        )

        CfnOutput(
            self,
            "ETLScheduleRuleName",
            value=etl_schedule.rule_name,
            description="Name of the EventBridge rule for daily ETL execution"
        )

