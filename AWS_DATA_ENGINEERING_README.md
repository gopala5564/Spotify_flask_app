# Spotify Data Engineering Project - AWS CDK

A production-ready AWS data engineering solution for extracting Spotify data into a scalable, serverless data lake using Infrastructure as Code.

## Features

✅ **Serverless Architecture**
- AWS Lambda functions for extract, transform, and load operations
- EventBridge for scheduled daily pipeline execution
- No servers to manage or maintain

✅ **Data Lake Design**
- Multi-layered architecture (raw, processed, final)
- S3 for scalable, cost-effective storage
- Automatic lifecycle management and tiering

✅ **Infrastructure as Code**
- AWS CDK for declarative infrastructure management
- Version-controlled infrastructure
- Easy deployment and rollback

✅ **Production-Ready**
- Comprehensive error handling and logging
- CloudWatch monitoring and metrics
- Data validation and quality checks
- Manifest files for data lineage

✅ **Spotify API Integration**
- Extract playlists, tracks, and audio features
- Handles API authentication
- Supports batch operations

## Quick Start

### Prerequisites
- AWS Account
- Python 3.11+
- Node.js 18+
- AWS CLI configured

### Installation

```bash
# 1. Clone and navigate to project
cd d:\Python_projects\Spotify_flask_app

# 2. Activate virtual environment
env\Scripts\activate

# 3. Install dependencies
pip install -r infra/requirements.txt
npm install -g aws-cdk

# 4. Get Spotify credentials from https://developer.spotify.com/dashboard

# 5. Deploy
cdk deploy \
  --parameters DataLakeBucketName=my-unique-bucket \
  --parameters SpotifyClientId=your_client_id \
  --parameters SpotifyClientSecret=your_client_secret
```

## Architecture

### Components

```
EventBridge (Scheduled)
    ↓
Orchestrator Lambda (spotify-etl-orchestrator)
    ├── Extract Lambda (spotify-etl-extract)
    │   └── → S3 Raw Layer
    ├── Transform Lambda (spotify-etl-transform)
    │   └── → S3 Processed Layer
    └── Load Lambda (spotify-etl-load)
        └── → S3 Final Layer
```

### Data Flow

```
Spotify API
    ↓
Extract Lambda
    └─→ raw/playlists/YYYY/MM/DD/HHMMSS/
    └─→ raw/tracks/YYYY/MM/DD/HHMMSS/
    └─→ raw/audio_features/YYYY/MM/DD/HHMMSS/
    ↓
Transform Lambda
    └─→ processed/playlists/YYYY/MM/DD/HHMMSS/
    └─→ processed/tracks/YYYY/MM/DD/HHMMSS/
    └─→ processed/audio_features/YYYY/MM/DD/HHMMSS/
    ↓
Load Lambda
    └─→ final/playlists/YYYY/MM/DD/
    └─→ final/tracks/YYYY/MM/DD/
    └─→ final/audio_features/YYYY/MM/DD/
```

## Project Structure

```
.
├── infra/
│   ├── spotify_etl_stack.py        # CDK Stack definition
│   ├── requirements.txt             # CDK dependencies
│   └── README.md
├── app/
│   ├── lambdas/
│   │   ├── extract_handler.py       # Extraction logic
│   │   ├── transform_handler.py     # Transformation logic
│   │   ├── load_handler.py          # Loading logic
│   │   ├── orchestrator.py          # Pipeline orchestration
│   │   └── __init__.py
│   └── src/
│       ├── etl/
│       │   ├── extractors/
│       │   │   ├── spotify_extractor.py
│       │   │   └── __init__.py
│       │   ├── transformers/
│       │   │   ├── data_transformer.py
│       │   │   └── __init__.py
│       │   ├── loaders/
│       │   │   ├── s3_loader.py
│       │   │   └── __init__.py
│       │   └── __init__.py
│       └── spotify_scraper/         # Spotify API client
├── app.py                           # CDK app entry point
├── requirements.txt                 # Project dependencies
├── DEPLOYMENT_GUIDE.md              # Detailed deployment instructions
└── README.md                        # This file
```

## Lambda Functions

### Extract Lambda (`spotify-etl-extract`)
- **Purpose**: Fetch data from Spotify API
- **Triggers**: Orchestrator, manual invocation
- **Outputs**: Raw layer JSON files in S3
- **Timeout**: 5 minutes
- **Memory**: 3008 MB

**Event Format:**
```json
{
  "action": "playlists" | "tracks" | "audio_features",
  "playlist_ids": ["optional", "list"]
}
```

### Transform Lambda (`spotify-etl-transform`)
- **Purpose**: Clean and deduplicate raw data
- **Triggers**: Orchestrator
- **Outputs**: Processed layer JSON files in S3
- **Timeout**: 5 minutes
- **Memory**: 3008 MB

**Event Format:**
```json
{
  "raw_key": "raw/playlists/2026/02/14/120000/playlists.json",
  "data_type": "playlists"
}
```

### Load Lambda (`spotify-etl-load`)
- **Purpose**: Move processed data to final layer
- **Triggers**: Orchestrator
- **Outputs**: Final layer files + manifest files
- **Timeout**: 5 minutes
- **Memory**: 3008 MB

**Event Format:**
```json
{
  "processed_key": "processed/playlists/2026/02/14/120000/playlists_processed.json",
  "data_type": "playlists"
}
```

### Orchestrator Lambda (`spotify-etl-orchestrator`)
- **Purpose**: Coordinate the entire ETL pipeline
- **Triggers**: EventBridge (daily 2 AM UTC), manual invocation
- **Timeout**: 15 minutes
- **Memory**: 3008 MB

**Event Format:**
```json
{
  "pipeline_type": "full" | "extract_only",
  "data_types": ["playlists", "tracks", "audio_features"],
  "retry_on_error": false
}
```

## Data Lake Layers

### Raw Layer (`raw/`)
- **Purpose**: Store original data from Spotify API
- **Organization**: `raw/{data_type}/YYYY/MM/DD/HHMMSS/`
- **Format**: JSON
- **Retention**: 60 days (transitioned to Glacier)
- **Use Case**: Data lineage, debugging, reprocessing

### Processed Layer (`processed/`)
- **Purpose**: Cleaned, deduplicated data
- **Organization**: `processed/{data_type}/YYYY/MM/DD/HHMMSS/`
- **Format**: JSON with standardized schema
- **Retention**: 30 days
- **Use Case**: Intermediate transformations, validation

### Final Layer (`final/`)
- **Purpose**: Ready-to-analyze data
- **Organization**: `final/{data_type}/YYYY/MM/DD/`
- **Format**: JSON, can be exported to Parquet
- **Retention**: Unlimited (RETAIN policy)
- **Use Case**: Analytics, dashboards, exports

### Manifests (`manifests/`)
- **Purpose**: Metadata and data lineage tracking
- **Organization**: `manifests/{data_type}/YYYY/MM/DD/`
- **Contents**: Load history, record counts, timestamps
- **Use Case**: Audit trails, recovery, reconciliation

## Monitoring & Logging

### CloudWatch Logs
- **Extract Lambda**: `/aws/lambda/spotify-etl-extract` (2 weeks retention)
- **Transform Lambda**: `/aws/lambda/spotify-etl-transform` (2 weeks retention)
- **Load Lambda**: `/aws/lambda/spotify-etl-load` (2 weeks retention)
- **Orchestrator Lambda**: `/aws/lambda/spotify-etl-orchestrator` (1 month retention)

### CloudWatch Metrics
Automatic metrics for:
- Function execution duration
- Error counts
- Invocation counts
- Memory utilization

### Manual Invocation

```bash
# Test extract
aws lambda invoke \
  --function-name spotify-etl-extract \
  --payload '{"action": "playlists"}' \
  response.json

# Test full pipeline
aws lambda invoke \
  --function-name spotify-etl-orchestrator \
  --payload '{"pipeline_type": "full", "data_types": ["playlists"]}' \
  response.json
```

## Configuration

### Environment Variables

Set in CDK stack:
- `DATA_LAKE_BUCKET`: S3 bucket name
- `SPOTIFY_CLIENT_ID`: Spotify API client ID
- `SPOTIFY_CLIENT_SECRET`: Spotify API client secret
- `AWS_REGION`: AWS region (default: us-east-1)

### Scheduled Execution

Default: **2:00 AM UTC** every day

To modify:
1. Edit `infra/spotify_etl_stack.py`
2. Update `schedule=events.Schedule.cron(minute="0", hour="2")`
3. Redeploy: `cdk deploy`

## Cost Estimation

**Monthly Costs (Approximate)**

| Service | Cost | Notes |
|---------|------|-------|
| Lambda | $0.50 | 1GB × 300 sec × 30 invocations |
| S3 Storage | $0.50 | ~1GB raw data + lifecycle to Glacier |
| CloudWatch Logs | $0.30 | 2-4 weeks retention |
| Data Transfer | $0.00 | No inter-region transfer |
| **Total** | **~$1.30/month** | Very cost-effective |

## Troubleshooting

### Lambda Function Not Executing

```bash
# Check function logs
aws logs tail /aws/lambda/spotify-etl-orchestrator --follow

# Check EventBridge rule
aws events describe-rule --name DailyETLRule
```

### S3 Access Errors

Verify IAM role has S3 permissions:
```bash
aws iam get-role-policy \
  --role-name SpotifyEtlStack-LambdaExecutionRole-xxx \
  --policy-name ...
```

### Spotify API Errors

1. Verify credentials in CloudWatch Logs
2. Check Spotify API rate limits
3. Ensure app is active in Spotify dashboard

## Development

### Local Testing

```bash
# Install dev dependencies
pip install pytest moto boto3-stubs

# Run tests
pytest tests/

# Test Lambda locally
sam local invoke ExtractFunction -e event.json
```

### Adding New Data Types

1. Update `extract_handler.py` with new extraction logic
2. Update `transform_handler.py` with transformation logic
3. Update `load_handler.py` with loading logic
4. Redeploy: `cdk deploy`

### Custom Transformations

Edit `src/etl/transformers/data_transformer.py` to add custom transformation logic.

## Security

- ✅ **Encryption**: S3 SSE-S3 enabled
- ✅ **Access Control**: Public access blocked
- ✅ **IAM Roles**: Least privilege principle
- ✅ **Secrets**: Use AWS Secrets Manager for credentials
- ✅ **Versioning**: S3 versioning enabled
- ✅ **Logging**: CloudWatch Logs for audit trail

## Best Practices

1. **Always test changes** in development before production
2. **Monitor CloudWatch Logs** for errors
3. **Use AWS Secrets Manager** for credentials
4. **Set CloudWatch Alarms** for Lambda errors
5. **Archive old data** to Glacier for cost savings
6. **Document changes** in git commits
7. **Rotate credentials** regularly

## Future Enhancements

- [ ] Add AWS Glue for complex transformations
- [ ] Implement Athena for SQL queries on S3 data
- [ ] Create QuickSight dashboards
- [ ] Add Amazon MWAA for complex workflows
- [ ] Implement cost optimization with Spot Instances
- [ ] Add multi-region support
- [ ] Implement CI/CD pipeline

## Contributing

To contribute to this project:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
- Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
- Review CloudWatch Logs in AWS Console
- Check Spotify API documentation
- Review AWS CDK best practices

## Related Documentation

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Guide](https://docs.aws.amazon.com/lambda/)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)

---

**Project Status**: Production Ready ✅

Last Updated: February 14, 2026
