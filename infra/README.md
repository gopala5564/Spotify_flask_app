# AWS CDK - Spotify ETL

This folder contains a Python AWS CDK app to provision the Spotify ETL infrastructure.

Prerequisites
- Python 3.11+
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- AWS credentials configured (`aws configure`)

Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Bootstrap and deploy

```bash
# Bootstrap your account (once)
cdk bootstrap aws://ACCOUNT_ID/us-east-1

# Deploy (you will be prompted for parameters)
cdk deploy
```

Notes
- The CDK stack uses the local `lambdas/` directory as Lambda code assets.
- Provide `DataLakeBucketName`, `SpotifyClientId`, and `SpotifyClientSecret` when deploying.
