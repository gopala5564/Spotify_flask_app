# Quick Start Guide - AWS Spotify Data Engineering Pipeline

## In 5 Minutes

### 1. Install Tools
```bash
pip install -r infra/requirements.txt
npm install -g aws-cdk
```

### 2. Get Spotify Credentials
Visit: https://developer.spotify.com/dashboard
- Create an app
- Copy Client ID and Client Secret

### 3. Deploy
```bash
cdk deploy \
  --parameters DataLakeBucketName=spotify-data-lake-$(date +%s) \
  --parameters SpotifyClientId=YOUR_CLIENT_ID \
  --parameters SpotifyClientSecret=YOUR_CLIENT_SECRET
```

### 4. Verify
```bash
aws s3 ls
aws lambda list-functions
```

**Done!** Your pipeline is now running. Check back at 2 AM UTC tomorrow for first execution.

---

## Manual Testing

### Trigger Extract
```bash
aws lambda invoke \
  --function-name spotify-etl-extract \
  --payload '{"action": "playlists"}' \
  response.json
```

### Trigger Full Pipeline
```bash
aws lambda invoke \
  --function-name spotify-etl-orchestrator \
  --payload '{"pipeline_type": "full", "data_types": ["playlists"]}' \
  response.json
```

### View Logs
```bash
aws logs tail /aws/lambda/spotify-etl-orchestrator --follow
```

---

## Architecture at a Glance

```
EventBridge (Daily 2 AM UTC)
         ↓
    Orchestrator
    ├── Extract  → S3 raw/
    ├── Transform → S3 processed/
    └── Load     → S3 final/ + manifests/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `infra/spotify_etl_stack.py` | CDK infrastructure definition |
| `app/lambdas/extract_handler.py` | Spotify API extraction |
| `app/lambdas/transform_handler.py` | Data transformation |
| `app/lambdas/load_handler.py` | Data loading |
| `app/lambdas/orchestrator.py` | Pipeline orchestration |

---

## Common Commands

```bash
# Check deployment status
cdk deploy

# View what will change
cdk diff

# Destroy everything (WARNING!)
cdk destroy

# Get stack outputs
aws cloudformation describe-stacks --stack-name SpotifyEtlStack

# Check Lambda function
aws lambda get-function --function-name spotify-etl-extract

# List S3 objects
aws s3 ls spotify-data-lake/ --recursive
```

---

## Monitoring

```bash
# View logs in real-time
aws logs tail /aws/lambda/spotify-etl-orchestrator --follow

# Get error metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=spotify-etl-extract \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S)Z \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
  --period 3600 \
  --statistics Sum
```

---

## Troubleshooting

**Pipeline not running?**
- Check: `aws events describe-rule --name DailyETLRule`
- View logs: `aws logs tail /aws/lambda/spotify-etl-orchestrator`

**S3 access errors?**
- Verify bucket exists: `aws s3 ls`
- Check role permissions: `aws iam get-role --role-name SpotifyEtlStack-LambdaExecutionRole-xxx`

**Lambda timeouts?**
- Increase timeout in `infra/spotify_etl_stack.py`
- Redeploy: `cdk deploy`

---

## Cost Estimate

| Usage | Monthly Cost |
|-------|--------------|
| 1 pipeline run/day (Lambda) | $0.45 |
| 1GB data storage (S3) | $0.023 |
| CloudWatch logs | $0.50 |
| **Total** | **~$1.00** |

---

## Next Steps

1. ✅ Deploy the stack
2. ✅ Test with manual invocation
3. ⬜ Implement real Spotify API calls
4. ⬜ Add custom transformations
5. ⬜ Set up Athena for SQL queries
6. ⬜ Build QuickSight dashboards

---

## Documentation

- **Deployment**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Project Docs**: [AWS_DATA_ENGINEERING_README.md](AWS_DATA_ENGINEERING_README.md)
- **Conversion Details**: [DATA_ENGINEERING_CONVERSION.md](DATA_ENGINEERING_CONVERSION.md)

---

**Questions?** Check the comprehensive guides above for more details.
