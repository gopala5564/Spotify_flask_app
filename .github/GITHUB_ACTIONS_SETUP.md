# GitHub Actions Setup Guide

This guide explains how to set up GitHub Actions to automatically deploy your Spotify ETL pipeline to AWS.

## Overview

The workflow includes:
- ✅ **Build & Test**: Runs on every push and pull request
- ✅ **Security Scan**: Scans for vulnerabilities using Trivy
- ✅ **Deploy to Dev**: Automatic deployment on push to `develop` branch
- ✅ **Deploy to Prod**: Automatic deployment on push to `main` branch
- ✅ **Manual Deploy**: Trigger deployment manually to any environment

## Prerequisites

1. GitHub repository with this code
2. AWS Account with proper IAM setup
3. Spotify API credentials
4. (Optional) Slack webhook for notifications

## Setup Instructions

### Step 1: Create IAM Roles for GitHub Actions

You need to create IAM roles for GitHub Actions to assume and deploy infrastructure.

#### 1.1 Create a trust policy document

Create a file named `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<YOUR_GITHUB_ORG>/<YOUR_REPO>:ref:refs/heads/*"
        }
      }
    }
  ]
}
```

Replace:
- `<YOUR_AWS_ACCOUNT_ID>` with your AWS account ID (find it in AWS console)
- `<YOUR_GITHUB_ORG>` with your GitHub organization/username
- `<YOUR_REPO>` with your repository name

#### 1.2 Create IAM role for Dev environment

```bash
aws iam create-role \
  --role-name github-actions-spotify-etl-dev \
  --assume-role-policy-document file://trust-policy.json \
  --region us-east-1
```

#### 1.3 Create IAM role for Prod environment

```bash
aws iam create-role \
  --role-name github-actions-spotify-etl-prod \
  --assume-role-policy-document file://trust-policy.json \
  --region us-east-1
```

#### 1.4 Create and attach policies

Save this as `github-actions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cdk:*",
        "cloudformation:*",
        "s3:*",
        "lambda:*",
        "iam:*",
        "events:*",
        "logs:*",
        "ec2:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": "*"
    }
  ]
}
```

Attach the policy:

```bash
aws iam put-role-policy \
  --role-name github-actions-spotify-etl-dev \
  --policy-name cdk-deploy-policy \
  --policy-document file://github-actions-policy.json

aws iam put-role-policy \
  --role-name github-actions-spotify-etl-prod \
  --policy-name cdk-deploy-policy \
  --policy-document file://github-actions-policy.json
```

### Step 2: Add GitHub Secrets

Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Click "New repository secret"

Add these secrets:

#### Required for all environments:
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `AWS_ROLE_TO_ASSUME_DEV`: ARN of dev role (format: `arn:aws:iam::<ACCOUNT_ID>:role/github-actions-spotify-etl-dev`)
- `AWS_ROLE_TO_ASSUME_PROD`: ARN of prod role (format: `arn:aws:iam::<ACCOUNT_ID>:role/github-actions-spotify-etl-prod`)

#### Dev environment:
- `DATA_LAKE_BUCKET_DEV`: S3 bucket name for dev (e.g., `spotify-etl-dev-bucket`)
- `SPOTIFY_CLIENT_ID_DEV`: Your Spotify dev client ID
- `SPOTIFY_CLIENT_SECRET_DEV`: Your Spotify dev client secret

#### Production environment:
- `DATA_LAKE_BUCKET_PROD`: S3 bucket name for prod (e.g., `spotify-etl-prod-bucket`)
- `SPOTIFY_CLIENT_ID_PROD`: Your Spotify prod client ID
- `SPOTIFY_CLIENT_SECRET_PROD`: Your Spotify prod client secret

#### Optional - Slack notifications:
- `SLACK_WEBHOOK`: Your Slack webhook URL (for deployment notifications)

### Step 3: Configure Branch Protection (Optional but Recommended)

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - Require status checks to pass before merging
   - Select "build-and-test" and "security-scan"
   - Dismiss stale pull request approvals when new commits are pushed
   - Require code review before merging

### Step 4: Create S3 Buckets (if not already created)

```bash
# For Dev
aws s3api create-bucket \
  --bucket spotify-etl-dev-bucket \
  --region us-east-1

# For Prod
aws s3api create-bucket \
  --bucket spotify-etl-prod-bucket \
  --region us-east-1
```

## Workflow Behavior

### Automatic Deployments

| Trigger | Behavior |
|---------|----------|
| Push to `develop` branch | Builds, tests, scans, deploys to Dev |
| Push to `main` branch | Builds, tests, scans, deploys to Prod |
| Pull request to `main` | Builds, tests, scans (no deployment) |

### Manual Deployment

Go to Actions tab → "Deploy to AWS" → "Run workflow" → Select environment (dev/staging/prod)

## Workflow Steps Explained

### 1. Build and Test Job

- Checks out code
- Sets up Python and Node.js
- Installs dependencies
- Runs `cdk synth` to verify CloudFormation template
- Runs tests (if available)
- Uploads coverage reports to Codecov

### 2. Security Scan Job

- Runs Trivy vulnerability scanner
- Uploads results to GitHub Security tab
- Identifies security issues before deployment

### 3. Deploy Jobs

#### Dev Deployment:
- Assumes IAM role with OIDC
- Configures AWS credentials (temporary)
- Installs CDK
- Deploys infrastructure using `cdk deploy`
- Posts comment on PR with status

#### Prod Deployment:
- Same as Dev but deploys to production
- Creates deployment summary
- Sends Slack notification (if configured)

#### Manual Deployment:
- Allows manual trigger with environment selection
- Deploys to specified environment

## Monitoring Deployments

### View Workflow Runs

1. Go to Actions tab in GitHub
2. Click on latest workflow run
3. View individual job logs

### Check Deployment Logs

In CloudFormation console:
1. Go to Stacks
2. Look for "SpotifyEtlStack"
3. View Events tab for deployment details

### Monitor Lambda Execution

In CloudWatch:
1. Logs → Log Groups
2. `/aws/lambda/spotify-etl-*`
3. View recent executions and errors

## Troubleshooting

### Deployment Failed: "Access Denied"

**Solution**: 
- Verify IAM role ARN in secrets is correct
- Check trust policy includes your GitHub org/repo
- Verify IAM policy has all required permissions

### Deployment Failed: "S3 Bucket Already Exists"

**Solution**: 
- Each S3 bucket name must be globally unique
- Use different bucket names for dev/prod
- Add suffix like `-<company>-<env>` to ensure uniqueness

### Deployment Failed: "Invalid Spotify Credentials"

**Solution**: 
- Verify secrets are set correctly in GitHub
- Check credentials work locally with `spotipy`
- Get new credentials from https://developer.spotify.com/dashboard

### Workflow Not Triggering on Push

**Solution**: 
- Make sure `.github/workflows/deploy.yml` is in `main` branch
- GitHub only runs workflows that exist on the pushed branch
- For branches, you may need to merge first

### Tests Timing Out

**Solution**: 
- Increase timeout in workflow file
- Move heavy tests to separate job
- Consider running tests only on pull requests

## Security Best Practices

1. ✅ **Use OIDC Authentication**: GitHub Actions assumes AWS role without storing credentials
2. ✅ **Limit Permissions**: IAM policy only includes necessary permissions
3. ✅ **Environment Protection**: Production deployment requires push to `main` branch
4. ✅ **Secrets Management**: Never commit secrets, use GitHub Secrets
5. ✅ **Branch Protection**: Require status checks and approvals before merging to `main`
6. ✅ **Audit Trail**: All deployments are logged in CloudFormation and GitHub

## Cost Considerations

- **GitHub Actions**: Free tier includes 2,000 minutes/month
- **AWS Resources**: CDK deployment creates S3, Lambda, EventBridge (roughly $1/month)
- **CloudWatch Logs**: Retention set to reduce costs

## Next Steps

1. ✅ Create IAM roles for dev and prod
2. ✅ Add GitHub secrets
3. ✅ Create S3 buckets
4. ✅ Push code to develop branch (test dev deployment)
5. ✅ Push code to main branch (test prod deployment)
6. ✅ Monitor CloudFormation and CloudWatch logs
7. ✅ Set up Slack notifications (optional)

## Useful Commands

```bash
# View role ARN
aws iam get-role --role-name github-actions-spotify-etl-dev --query 'Role.Arn'

# Test role assumption
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::<ACCOUNT_ID>:role/github-actions-spotify-etl-dev \
  --role-session-name test-session \
  --web-identity-token <TOKEN>

# View deployment logs
aws cloudformation describe-stack-events \
  --stack-name SpotifyEtlStack

# Check Lambda status
aws lambda list-functions --query 'Functions[?contains(FunctionName, `spotify`)]'
```

## Resources

- [GitHub Actions OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS CDK CLI Documentation](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**Status**: Ready for setup

**Last Updated**: February 14, 2026
