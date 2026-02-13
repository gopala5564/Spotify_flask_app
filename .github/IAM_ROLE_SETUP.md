# GitHub Actions AWS IAM Role Setup Guide

This guide shows you how to create the IAM roles that GitHub Actions needs to deploy your Spotify ETL pipeline to AWS.

## Prerequisites

- AWS Account with admin access
- GitHub repository set up
- Your GitHub organization/username
- Your repository name

## Method 1: Using AWS CLI (Recommended)

### Step 1: Create Trust Policy

Save this as `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO:ref:refs/heads/*"
        }
      }
    }
  ]
}
```

**Replace:**
- `123456789012` → Your AWS Account ID
- `YOUR_GITHUB_ORG` → Your GitHub username or organization (e.g., `octocat`)
- `YOUR_REPO` → Your repository name (e.g., `Spotify_flask_app`)

### Step 2: Find Your AWS Account ID

```powershell
aws sts get-caller-identity --query Account --output text
```

This will print your 12-digit account ID. Copy it and update the trust policy JSON.

### Step 3: Create OIDC Provider (One-time Setup)

**Check if OIDC provider already exists:**

```powershell
aws iam list-open-id-connect-providers
```

**If not present, create it:**

```powershell
aws iam create-open-id-connect-provider `
  --url https://token.actions.githubusercontent.com `
  --client-id-list sts.amazonaws.com `
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Step 4: Create Dev Role

```powershell
aws iam create-role `
  --role-name github-actions-spotify-etl-dev `
  --assume-role-policy-document file://trust-policy.json `
  --description "Role for GitHub Actions to deploy Spotify ETL Dev"
```

**Output will show:**
```
{
  "Role": {
    "Arn": "arn:aws:iam::123456789012:role/github-actions-spotify-etl-dev",
    ...
  }
}
```

**Copy the ARN** - this is your `AWS_ROLE_TO_ASSUME_DEV`

### Step 5: Create Prod Role

Update `trust-policy.json` if needed, then:

```powershell
aws iam create-role `
  --role-name github-actions-spotify-etl-prod `
  --assume-role-policy-document file://trust-policy.json `
  --description "Role for GitHub Actions to deploy Spotify ETL Prod"
```

**Copy the ARN** - this is your `AWS_ROLE_TO_ASSUME_PROD`

### Step 6: Create Staging Role (Optional)

```powershell
aws iam create-role `
  --role-name github-actions-spotify-etl-staging `
  --assume-role-policy-document file://trust-policy.json `
  --description "Role for GitHub Actions to deploy Spotify ETL Staging"
```

### Step 7: Attach Deployment Policy

Save this as `deployment-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "cdk:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "s3-object-lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "events:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Attach to Dev role:**

```powershell
aws iam put-role-policy `
  --role-name github-actions-spotify-etl-dev `
  --policy-name cdk-deploy-policy `
  --policy-document file://deployment-policy.json
```

**Attach to Prod role:**

```powershell
aws iam put-role-policy `
  --role-name github-actions-spotify-etl-prod `
  --policy-name cdk-deploy-policy `
  --policy-document file://deployment-policy.json
```

**Attach to Staging role (if created):**

```powershell
aws iam put-role-policy `
  --role-name github-actions-spotify-etl-staging `
  --policy-name cdk-deploy-policy `
  --policy-document file://deployment-policy.json
```

### Step 8: Get Role ARNs

```powershell
# Dev role
aws iam get-role `
  --role-name github-actions-spotify-etl-dev `
  --query 'Role.Arn' `
  --output text

# Prod role
aws iam get-role `
  --role-name github-actions-spotify-etl-prod `
  --query 'Role.Arn' `
  --output text

# Staging role (optional)
aws iam get-role `
  --role-name github-actions-spotify-etl-staging `
  --query 'Role.Arn' `
  --output text
```

**Copy these ARNs** - they're your GitHub secrets!

---

## Method 2: Using AWS Console (GUI)

### Step 1: Enable OIDC Provider

1. Go to AWS Console → **IAM** → **Identity providers**
2. Click **Add provider**
3. Select **OpenID Connect**
4. Provider URL: `https://token.actions.githubusercontent.com`
5. Audience: `sts.amazonaws.com`
6. Click **Add provider**

### Step 2: Create Dev Role

1. Go to **IAM** → **Roles**
2. Click **Create role**
3. Select **Web identity**
4. Choose:
   - **Identity provider**: `token.actions.githubusercontent.com`
   - **Audience**: `sts.amazonaws.com`
5. Click **Next**
6. Search for and attach: `PowerUserAccess` (or select specific permissions)
7. Click **Next**
8. Role name: `github-actions-spotify-etl-dev`
9. Click **Create role**

### Step 3: Edit Trust Relationship

1. Find the role you just created
2. Click it to open details
3. Go to **Trust relationships** tab
4. Click **Edit trust relationship**
5. Replace with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO:ref:refs/heads/*"
        }
      }
    }
  ]
}
```

6. Replace `123456789012`, `YOUR_GITHUB_ORG`, `YOUR_REPO`
7. Click **Update trust policy**

### Step 4: Copy Role ARN

1. On the role page, copy the **ARN** (top of the page)
2. Format: `arn:aws:iam::123456789012:role/github-actions-spotify-etl-dev`
3. Save this - it's your GitHub secret!

### Step 5: Repeat for Prod

Repeat Steps 2-4 with:
- Role name: `github-actions-spotify-etl-prod`
- Same trust policy (update the repo reference if needed)

---

## Verify Setup

### Test Role Assumption

```powershell
# Get a token from GitHub (you'll need to do this in GitHub Actions context)
# For now, just verify the role exists:

aws iam get-role --role-name github-actions-spotify-etl-dev
aws iam get-role --role-name github-actions-spotify-etl-prod
```

### Check Permissions

```powershell
aws iam get-role-policy `
  --role-name github-actions-spotify-etl-dev `
  --policy-name cdk-deploy-policy
```

---

## Add Secrets to GitHub

Now that you have the role ARNs, add them as GitHub secrets:

1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these:

| Secret Name | Value |
|------------|-------|
| `AWS_ACCOUNT_ID` | `123456789012` (your account ID) |
| `AWS_ROLE_TO_ASSUME_DEV` | `arn:aws:iam::123456789012:role/github-actions-spotify-etl-dev` |
| `AWS_ROLE_TO_ASSUME_PROD` | `arn:aws:iam::123456789012:role/github-actions-spotify-etl-prod` |
| `AWS_ROLE_TO_ASSUME_STAGING` | `arn:aws:iam::123456789012:role/github-actions-spotify-etl-staging` (optional) |

---

## Complete CLI Script

Here's a complete script to set up everything at once:

Save as `setup-github-actions-roles.ps1`:

```powershell
#!/usr/bin/env pwsh

# Configuration
$GITHUB_ORG = "YOUR_GITHUB_ORG"
$GITHUB_REPO = "YOUR_REPO"
$AWS_REGION = "us-east-1"

# Get AWS Account ID
Write-Host "Getting AWS Account ID..."
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
Write-Host "Account ID: $ACCOUNT_ID"

# Create trust policy
Write-Host "Creating trust policy JSON..."
$trustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Federated = "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
            }
            Action = "sts:AssumeRoleWithWebIdentity"
            Condition = @{
                StringEquals = @{
                    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
                }
                StringLike = @{
                    "token.actions.githubusercontent.com:sub" = "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/*"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

$trustPolicy | Out-File -FilePath trust-policy.json -Encoding utf8

# Create OIDC provider if it doesn't exist
Write-Host "Checking OIDC provider..."
$providers = aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[*].Arn' --output text

if ($providers -notlike "*token.actions.githubusercontent.com*") {
    Write-Host "Creating OIDC provider..."
    aws iam create-open-id-connect-provider `
      --url https://token.actions.githubusercontent.com `
      --client-id-list sts.amazonaws.com `
      --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
} else {
    Write-Host "OIDC provider already exists"
}

# Create roles
Write-Host "Creating dev role..."
aws iam create-role `
  --role-name github-actions-spotify-etl-dev `
  --assume-role-policy-document file://trust-policy.json `
  --description "Role for GitHub Actions to deploy Spotify ETL Dev"

Write-Host "Creating prod role..."
aws iam create-role `
  --role-name github-actions-spotify-etl-prod `
  --assume-role-policy-document file://trust-policy.json `
  --description "Role for GitHub Actions to deploy Spotify ETL Prod"

# Create deployment policy
Write-Host "Creating deployment policy..."
$deployPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "cloudformation:*",
                "cdk:*",
                "s3:*",
                "s3-object-lambda:*",
                "lambda:*",
                "iam:*",
                "events:*",
                "logs:*",
                "ec2:*",
                "cloudwatch:*"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10

$deployPolicy | Out-File -FilePath deployment-policy.json -Encoding utf8

# Attach policies
Write-Host "Attaching policies to dev role..."
aws iam put-role-policy `
  --role-name github-actions-spotify-etl-dev `
  --policy-name cdk-deploy-policy `
  --policy-document file://deployment-policy.json

Write-Host "Attaching policies to prod role..."
aws iam put-role-policy `
  --role-name github-actions-spotify-etl-prod `
  --policy-name cdk-deploy-policy `
  --policy-document file://deployment-policy.json

# Get and display ARNs
Write-Host "`nRole ARNs created successfully!`n"

$devArn = aws iam get-role `
  --role-name github-actions-spotify-etl-dev `
  --query 'Role.Arn' `
  --output text

$prodArn = aws iam get-role `
  --role-name github-actions-spotify-etl-prod `
  --query 'Role.Arn' `
  --output text

Write-Host "AWS_ACCOUNT_ID = $ACCOUNT_ID"
Write-Host "AWS_ROLE_TO_ASSUME_DEV = $devArn"
Write-Host "AWS_ROLE_TO_ASSUME_PROD = $prodArn"

Write-Host "`nAdd these to GitHub Secrets in your repository!"
Write-Host "Settings > Secrets and variables > Actions > New repository secret"

# Cleanup
Remove-Item trust-policy.json
Remove-Item deployment-policy.json
```

Run it:

```powershell
.\setup-github-actions-roles.ps1
```

---

## Troubleshooting

### Error: "Role already exists"

The role was already created. Get the ARN:

```powershell
aws iam get-role --role-name github-actions-spotify-etl-dev --query 'Role.Arn' --output text
```

### Error: "OIDC provider already exists"

That's fine - it means it was already set up. Continue to role creation.

### Error: "Access denied"

Make sure your AWS credentials have IAM permissions:
```powershell
aws sts get-caller-identity
```

### Role not assuming successfully

Check the trust policy has your correct:
- Account ID
- GitHub org/username
- Repository name

---

## Summary

After completing this, you'll have:

✅ OIDC provider configured  
✅ Dev role created with proper permissions  
✅ Prod role created with proper permissions  
✅ Role ARNs ready for GitHub secrets  

Next step: Add the ARNs to GitHub secrets and deploy!
