# AWS Data Engineering Project - Deployment & Setup Guide

## Project Overview

This is a comprehensive AWS data engineering project for extracting Spotify data into a serverless data lake using AWS CDK. The architecture consists of:

- **AWS CDK** for Infrastructure as Code
- **AWS Lambda** for ETL operations (Extract, Transform, Load)
- **Amazon S3** for data lake storage (raw, processed, final layers)
- **EventBridge** for scheduling and orchestration
- **CloudWatch** for logging and monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EventBridge (Daily 2 AM UTC)                             │
│         │                                                  │
│         ▼                                                  │
│  ┌─────────────────────────────────────┐                 │
│  │  Orchestrator Lambda                │                 │
│  │  (Coordinates ETL Pipeline)         │                 │
│  └────────┬──────────┬──────────┬──────┘                 │
│           │          │          │                        │
│      ┌────▼──┐  ┌────▼──┐  ┌───▼───┐                    │
│      │Extract│  │Transform│  │ Load │                    │
│      │ Lambda│  │ Lambda │  │Lambda │                    │
│      └────┬──┘  └────┬──┘  └───┬───┘                    │
│           │          │          │                        │
│           ▼          ▼          ▼                        │
│  ┌─────────────────────────────────┐                     │
│  │     Amazon S3 Data Lake         │                     │
│  ├─────────────────────────────────┤                     │
│  │ ├─ raw/          (API data)    │                     │
│  │ ├─ processed/    (cleaned)     │                     │
│  │ ├─ final/        (ready to use)│                     │
│  │ └─ manifests/    (metadata)    │                     │
│  └─────────────────────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Python 3.11+** installed
4. **Node.js 18+** (for AWS CDK)
5. **Git** for version control

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to project directory
cd d:\Python_projects\Spotify_flask_app

# Activate virtual environment
env\Scripts\activate

# Install Python packages
pip install -r infra/requirements.txt

# Install AWS CDK (global)
npm install -g aws-cdk

# Verify CDK installation
cdk --version
```

### 2. Configure AWS Credentials

```bash
# Option 1: Using AWS CLI
aws configure

# Option 2: Using environment variables
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_DEFAULT_REGION=us-east-1
```

### 3. Prepare Spotify Credentials

Get your Spotify API credentials:

1. Go to https://developer.spotify.com/dashboard
2. Create an application
3. Get your **Client ID** and **Client Secret**

### 4. Deploy Infrastructure with CDK

```bash
# Navigate to project root
cd d:\Python_projects\Spotify_flask_app

# Synthesize CloudFormation template
cdk synth

# Review changes (optional)
cdk diff

# Deploy the stack
cdk deploy \
  --parameters DataLakeBucketName=my-unique-bucket-name \
  --parameters SpotifyClientId=your_spotify_client_id \
  --parameters SpotifyClientSecret=your_spotify_client_secret

# Confirm deployment by typing 'y' when prompted
```

### 5. Verify Deployment

```bash
# Check CloudFormation stacks
aws cloudformation list-stacks --region us-east-1

# List Lambda functions
aws lambda list-functions --region us-east-1

# Verify S3 bucket creation
aws s3 ls

# Check bucket contents
aws s3 ls my-unique-bucket-name/ --recursive
```

## File Structure

```
project-root/
├── infra/
│   ├── spotify_etl_stack.py      # CDK Stack definition
│   ├── requirements.txt           # CDK dependencies
│   └── README.md
├── app/
│   ├── lambdas/
│   │   ├── extract_handler.py     # Extract Lambda function
│   │   ├── transform_handler.py   # Transform Lambda function
│   │   ├── load_handler.py        # Load Lambda function
│   │   ├── orchestrator.py        # Orchestrator Lambda function
│   │   └── __init__.py
│   └── src/
│       ├── etl/
│       │   ├── extractors/        # Extraction modules
│       │   ├── transformers/      # Transformation modules
│       │   ├── loaders/           # Loading modules
│       │   └── __init__.py
│       └── spotify_scraper/       # Spotify API client
├── tests/                          # Unit tests
├── app.py                         # CDK app entry point
├── requirements.txt               # Project requirements
└── DEPLOYMENT_GUIDE.md            # This file
```

## Running the ETL Pipeline

### Manual Trigger

```bash
# Trigger pipeline via AWS Lambda console
# or use AWS CLI

# Full pipeline (Extract -> Transform -> Load)
aws lambda invoke \
  --function-name spotify-etl-orchestrator \
  --payload '{"pipeline_type": "full", "data_types": ["playlists"]}' \
  response.json
  
# View response
cat response.json
```

### Scheduled Execution

The pipeline runs automatically every day at **2:00 AM UTC** via EventBridge.

To modify the schedule:
1. Edit `infra/spotify_etl_stack.py`
2. Change the cron expression in the `DailyETLRule`
3. Redeploy: `cdk deploy`

## Monitoring & Logs

### CloudWatch Logs

```bash
# View orchestrator logs
aws logs tail /aws/lambda/spotify-etl-orchestrator --follow

# View extract logs
aws logs tail /aws/lambda/spotify-etl-extract --follow

# View transform logs
aws logs tail /aws/lambda/spotify-etl-transform --follow

# View load logs
aws logs tail /aws/lambda/spotify-etl-load --follow
```

### CloudWatch Metrics

Check Lambda function metrics:

```bash
# Get error count for extract Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=spotify-etl-extract \
  --start-time 2026-02-14T00:00:00Z \
  --end-time 2026-02-15T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Data Lake Structure

### Layer Descriptions

1. **Raw Layer** (`raw/`)
   - Stores unmodified data from Spotify API
   - Organized by data type and timestamp
   - Format: JSON
   - Example: `raw/playlists/2026/02/14/120000/playlists.json`

2. **Processed Layer** (`processed/`)
   - Cleaned and deduplicated data
   - Standardized format
   - Removed sensitive information
   - Example: `processed/playlists/2026/02/14/120000/playlists_processed.json`

3. **Final Layer** (`final/`)
   - Ready-for-analysis data
   - Merged and enriched
   - Manifests for data lineage
   - Example: `final/playlists/2026/02/14/playlists_final.json`

4. **Manifests** (`manifests/`)
   - Metadata about data loads
   - Data quality checks
   - Load history and timestamps

## Troubleshooting

### Issue: Lambda execution fails with timeout

**Solution:** Increase timeout in `spotify_etl_stack.py`
```python
timeout=Duration.seconds(900)  # Increase from default
```

### Issue: S3 access denied errors

**Solution:** Verify IAM permissions in the role policy

```bash
# Check role policies
aws iam get-role-policy \
  --role-name SpotifyEtlStack-LambdaExecutionRole-xxx \
  --policy-name inline-policy
```

### Issue: Spotify API authentication fails

**Solution:** 
1. Verify credentials are correct
2. Check environment variables are set
3. Ensure Spotify app is active in dashboard

```bash
# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name spotify-etl-extract
```

### Issue: EventBridge rule not triggering

**Solution:**
1. Verify rule is enabled
2. Check rule schedule syntax
3. Ensure Lambda has permission to be invoked

```bash
# List EventBridge rules
aws events list-rules --region us-east-1

# Check rule details
aws events describe-rule --name DailyETLRule
```

## Cost Optimization

1. **Lambda Optimization**
   - Reduce memory allocation for Load Lambda (currently 3GB)
   - Use Lambda Layers for shared code
   - Implement reserved capacity for scheduled runs

2. **S3 Optimization**
   - Use S3 Intelligent-Tiering for automatic cost optimization
   - Enable S3 bucket versioning only on active folders
   - Set lifecycle policies to archive old data

3. **Monitoring Optimization**
   - Set log retention to 2 weeks (raw data)
   - Compress old logs
   - Use CloudWatch Insights for ad-hoc queries

## Security Best Practices

1. **Credentials Management**
   - Use AWS Secrets Manager for sensitive credentials
   - Rotate Spotify credentials regularly
   - Never commit credentials to version control

2. **S3 Security**
   - Enable bucket encryption (enabled by default)
   - Block public access (enabled by default)
   - Enable versioning for audit trails

3. **IAM Security**
   - Follow least privilege principle
   - Use separate roles for each Lambda
   - Regularly audit IAM permissions

4. **Networking**
   - Use VPC endpoints for private S3 access (optional)
   - Implement network ACLs

## Cleanup

To remove all infrastructure and avoid charges:

```bash
# Delete CDK stack
cdk destroy

# Or use AWS CloudFormation
aws cloudformation delete-stack --stack-name SpotifyEtlStack
```

## Next Steps

1. **Integrate Real Spotify API**
   - Implement spotipy client in extract handlers
   - Handle API rate limiting
   - Add error retry logic

2. **Add Data Validation**
   - Implement data quality checks
   - Add schema validation
   - Monitor data completeness

3. **Expand to AWS Glue**
   - Use Glue for more complex transformations
   - Add Glue Catalog for data discovery
   - Implement automated crawlers

4. **Implement Analytics**
   - Connect to Amazon Athena for SQL queries
   - Build QuickSight dashboards
   - Export to data warehouse (Redshift)

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Amazon S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/BestPractices.html)
- [EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [Spotify API Documentation](https://developer.spotify.com/documentation/web-api)

## Support

For issues or questions:
1. Check CloudWatch Logs for error details
2. Review AWS CDK documentation
3. Check Spotify API rate limits and status
4. Verify AWS credentials and permissions
