# Local Development Guide - Running Without AWS

You can run and test this data engineering project locally without deploying to AWS. This guide covers multiple approaches.

## Option 1: Run Lambda Handlers as Python Scripts (Easiest)

### Setup

```bash
# Install required packages
pip install -r requirements.txt

# Set environment variables
set DATA_LAKE_BUCKET=local-bucket
set SPOTIFY_CLIENT_ID=your_spotify_id
set SPOTIFY_CLIENT_SECRET=your_spotify_secret
set AWS_REGION=us-east-1
```

### Test Extract Handler

```python
# test_local.py
import sys
import json
import os
from pathlib import Path

# Add lambdas directory to path
sys.path.insert(0, str(Path(__file__).parent / 'app' / 'lambdas'))

# Set environment variables
os.environ['DATA_LAKE_BUCKET'] = 'local-bucket'

from extract_handler import lambda_handler

# Test event
event = {
    'action': 'playlists'
}

# Call handler
response = lambda_handler(event, None)
print(json.dumps(json.loads(response['body']), indent=2))
```

Run it:
```bash
python test_local.py
```

### Create Local S3 Simulation

```python
# local_storage.py
import json
import os
from datetime import datetime
from pathlib import Path

class LocalStorage:
    """Simulate S3 storage on local filesystem"""
    
    def __init__(self, base_path='./local_data_lake'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    def put_object(self, key, data):
        """Write data to local file"""
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(data, (dict, list)):
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            with open(file_path, 'wb') as f:
                f.write(data)
        
        print(f"Saved to: {file_path}")
        return file_path
    
    def get_object(self, key):
        """Read data from local file"""
        file_path = self.base_path / key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def list_objects(self, prefix=''):
        """List files in directory"""
        base = self.base_path / prefix if prefix else self.base_path
        if not base.exists():
            return []
        
        return [str(p.relative_to(self.base_path)) for p in base.rglob('*') if p.is_file()]
```

Use it:
```python
# test_with_local_storage.py
from local_storage import LocalStorage

storage = LocalStorage('./local_data_lake')

# Simulate extract
data = {
    'playlists': [
        {'id': '1', 'name': 'Playlist 1'},
        {'id': '2', 'name': 'Playlist 2'}
    ],
    'timestamp': '2026-02-14T12:00:00Z'
}

storage.put_object('raw/playlists/2026/02/14/120000/playlists.json', data)

# List files
files = storage.list_objects('raw/')
print(f"Created {len(files)} files")
```

---

## Option 2: AWS SAM (Serverless Application Model)

AWS SAM allows you to run Lambda locally with Docker.

### Install SAM

```bash
# On Windows, using Chocolatey
choco install aws-sam-cli

# Or download from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
```

### Create SAM Template

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Spotify ETL Pipeline

Globals:
  Function:
    Timeout: 300
    MemorySize: 3008
    Runtime: python3.11
    Environment:
      Variables:
        DATA_LAKE_BUCKET: local-bucket
        SPOTIFY_CLIENT_ID: your_id
        SPOTIFY_CLIENT_SECRET: your_secret
        AWS_REGION: us-east-1

Resources:
  ExtractFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: spotify-etl-extract
      CodeUri: app/lambdas/
      Handler: extract_handler.lambda_handler

  TransformFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: spotify-etl-transform
      CodeUri: app/lambdas/
      Handler: transform_handler.lambda_handler

  LoadFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: spotify-etl-load
      CodeUri: app/lambdas/
      Handler: load_handler.lambda_handler

  OrchestratorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: spotify-etl-orchestrator
      CodeUri: app/lambdas/
      Handler: orchestrator.lambda_handler
```

### Run with SAM

```bash
# Start local API
sam local start-api

# Or invoke function directly
sam local invoke ExtractFunction -e events/extract_event.json
```

Create test event file `events/extract_event.json`:

```json
{
  "action": "playlists"
}
```

---

## Option 3: Docker Containers

### Create Dockerfile for Lambda

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy function code
COPY app/lambdas/ ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Set the CMD to your handler
CMD ["extract_handler.lambda_handler"]
```

### Run Docker Container

```bash
# Build image
docker build -t spotify-etl-extract:latest .

# Run container
docker run -p 9000:8080 \
  -e DATA_LAKE_BUCKET=local-bucket \
  -e SPOTIFY_CLIENT_ID=your_id \
  -e SPOTIFY_CLIENT_SECRET=your_secret \
  spotify-etl-extract:latest

# In another terminal, invoke function
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"action":"playlists"}'
```

---

## Option 4: LocalStack (Full AWS Simulation)

LocalStack simulates AWS services locally.

### Install LocalStack

```bash
pip install localstack
```

### Start LocalStack

```bash
# Start all AWS services
localstack start

# Or just S3 and Lambda
localstack start -s s3,lambda
```

### Use with Python

```python
import boto3
from localstack_utils.aws_stack import aws_stack

# Use local S3
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Create bucket
s3_client.create_bucket(Bucket='local-bucket')

# List buckets
buckets = s3_client.list_buckets()
print(buckets)
```

---

## Option 5: Unit Tests (Recommended for Development)

### Create Test Suite

```python
# tests/test_handlers.py
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add lambdas to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app' / 'lambdas'))


class TestExtractHandler:
    """Test extract Lambda handler"""
    
    @patch.dict('os.environ', {
        'DATA_LAKE_BUCKET': 'test-bucket'
    })
    def test_extract_playlists(self):
        """Test extracting playlists"""
        from extract_handler import lambda_handler
        
        event = {
            'action': 'playlists'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert body['action'] == 'playlists'
    
    @patch.dict('os.environ', {
        'DATA_LAKE_BUCKET': 'test-bucket'
    })
    def test_extract_missing_bucket(self):
        """Test error when bucket not set"""
        import os
        del os.environ['DATA_LAKE_BUCKET']
        
        from extract_handler import lambda_handler
        
        event = {'action': 'playlists'}
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 500


class TestTransformHandler:
    """Test transform Lambda handler"""
    
    @patch.dict('os.environ', {
        'DATA_LAKE_BUCKET': 'test-bucket'
    })
    def test_transform_playlists(self):
        """Test transforming playlist data"""
        from transform_handler import lambda_handler
        
        event = {
            'raw_key': 'raw/playlists/2026/02/14/120000/playlists.json',
            'data_type': 'playlists'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] in [200, 500]  # Either success or expected error


class TestOrchestratorHandler:
    """Test orchestrator Lambda handler"""
    
    @patch.dict('os.environ', {
        'DATA_LAKE_BUCKET': 'test-bucket'
    })
    @patch('orchestrator.lambda_client')
    def test_orchestrator_pipeline(self, mock_lambda):
        """Test full pipeline orchestration"""
        from orchestrator import lambda_handler
        
        # Mock Lambda invocations
        mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'status': 'success'})
            }))
        }
        
        event = {
            'pipeline_type': 'full',
            'data_types': ['playlists']
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['pipeline_type'] == 'full'
```

### Run Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app/lambdas --cov-report=html

# Run specific test
pytest tests/test_handlers.py::TestExtractHandler::test_extract_playlists -v
```

---

## Option 6: Mock Development Environment

Complete mock setup for local development:

```python
# dev_environment.py
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class MockSpotifyAPI:
    """Mock Spotify API client"""
    
    def __init__(self):
        self.playlists = [
            {'id': 'p1', 'name': 'Chill Mix', 'owner': 'spotify', 'total_tracks': 50},
            {'id': 'p2', 'name': 'Party Mix', 'owner': 'spotify', 'total_tracks': 75},
            {'id': 'p3', 'name': 'Focus Music', 'owner': 'spotify', 'total_tracks': 100},
        ]
        self.tracks = [
            {'id': 't1', 'name': 'Song 1', 'artist': 'Artist 1'},
            {'id': 't2', 'name': 'Song 2', 'artist': 'Artist 2'},
        ]
        self.features = [
            {'id': 't1', 'danceability': 0.7, 'energy': 0.8},
            {'id': 't2', 'danceability': 0.6, 'energy': 0.9},
        ]
    
    def get_playlists(self):
        return self.playlists
    
    def get_tracks(self, playlist_id):
        return self.tracks
    
    def get_audio_features(self, track_ids):
        return [f for f in self.features if f['id'] in track_ids]


class MockS3:
    """Mock S3 storage"""
    
    def __init__(self, base_path='./local_data_lake'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.objects = {}
    
    def put_object(self, Bucket, Key, Body, ContentType='application/json'):
        """Store object"""
        file_path = self.base_path / Key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(Body, (dict, list)):
            with open(file_path, 'w') as f:
                json.dump(Body, f, indent=2)
        else:
            with open(file_path, 'wb') as f:
                f.write(Body if isinstance(Body, bytes) else Body.encode())
        
        self.objects[Key] = {
            'path': str(file_path),
            'created': datetime.utcnow().isoformat()
        }
        return {'ETag': f'"{hash(Key)}"'}
    
    def get_object(self, Bucket, Key):
        """Retrieve object"""
        file_path = self.base_path / Key
        
        if not file_path.exists():
            raise FileNotFoundError(f"Key not found: {Key}")
        
        with open(file_path, 'r') as f:
            return {'Body': f.read()}
    
    def list_objects_v2(self, Bucket, Prefix='', **kwargs):
        """List objects"""
        matching = [
            {'Key': k} for k in self.objects.keys() 
            if k.startswith(Prefix)
        ]
        return {'Contents': matching}


# Test with mock environment
if __name__ == '__main__':
    print("Mock Spotify API:")
    api = MockSpotifyAPI()
    print(json.dumps(api.get_playlists(), indent=2))
    
    print("\nMock S3 Storage:")
    s3 = MockS3()
    s3.put_object(
        Bucket='test',
        Key='raw/playlists/2026/02/14/playlists.json',
        Body={'playlists': api.get_playlists()}
    )
    
    objects = s3.list_objects_v2(Bucket='test', Prefix='raw/')
    print(f"Created {len(objects['Contents'])} objects")
```

---

## Running Full Local Pipeline

### Complete Local Test Script

```python
# run_local_pipeline.py
import sys
import json
from pathlib import Path
from dev_environment import MockS3, MockSpotifyAPI

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / 'app' / 'lambdas'))

# Mock environment
import os
os.environ['DATA_LAKE_BUCKET'] = 'local-bucket'
os.environ['SPOTIFY_CLIENT_ID'] = 'test-id'
os.environ['SPOTIFY_CLIENT_SECRET'] = 'test-secret'

# Import handlers
from extract_handler import lambda_handler as extract_handler
from transform_handler import lambda_handler as transform_handler
from load_handler import lambda_handler as load_handler


def run_local_pipeline():
    """Run complete pipeline locally"""
    
    print("=" * 60)
    print("STAGE 1: EXTRACT")
    print("=" * 60)
    
    extract_event = {'action': 'playlists'}
    extract_response = extract_handler(extract_event, None)
    extract_body = json.loads(extract_response['body'])
    
    print(f"Status: {extract_body['status']}")
    print(f"S3 Location: {extract_body['results'].get('s3_location')}")
    print()
    
    print("=" * 60)
    print("STAGE 2: TRANSFORM")
    print("=" * 60)
    
    transform_event = {
        'raw_key': extract_body['results'].get('s3_location', '').split('://')[-1],
        'data_type': 'playlists'
    }
    transform_response = transform_handler(transform_event, None)
    transform_body = json.loads(transform_response['body'])
    
    print(f"Status: {transform_body['status']}")
    print(f"Records Processed: {transform_body.get('records_processed')}")
    print()
    
    print("=" * 60)
    print("STAGE 3: LOAD")
    print("=" * 60)
    
    load_event = {
        'processed_key': transform_body.get('destination', '').split('://')[-1],
        'data_type': 'playlists'
    }
    load_response = load_handler(load_event, None)
    load_body = json.loads(load_response['body'])
    
    print(f"Status: {load_body['status']}")
    print(f"Records Loaded: {load_body.get('records_loaded')}")
    print()
    
    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    run_local_pipeline()
```

Run it:
```bash
python run_local_pipeline.py
```

---

## Comparison: Local vs AWS

| Feature | Local | AWS |
|---------|-------|-----|
| **Cost** | Free | ~$1/month |
| **Setup Time** | 5 minutes | 15 minutes |
| **Testing** | Fast iteration | Deploy time |
| **Data Persistence** | Filesystem | S3 (unlimited) |
| **Scheduling** | Manual or cron | EventBridge |
| **Monitoring** | print() / logs | CloudWatch |
| **Scalability** | Limited | Automatic |
| **Production Ready** | No | Yes |

---

## Recommended Setup

### For Development:
1. Use **Option 1** (Python scripts) for quick testing
2. Use **Option 5** (Unit tests) for regression testing
3. Use **Option 6** (Mock environment) for integration testing

### For Production:
1. Deploy to AWS using CDK
2. Test in staging environment
3. Deploy to production

### Hybrid Approach:
1. Develop locally with mocks
2. Run unit tests
3. Deploy to AWS dev environment
4. Test with real Spotify API
5. Deploy to production

---

## Tips for Local Development

### 1. Use Environment Variables
```bash
# Create .env file
DATA_LAKE_BUCKET=local-bucket
SPOTIFY_CLIENT_ID=your_id
SPOTIFY_CLIENT_SECRET=your_secret

# Load in Python
from dotenv import load_dotenv
load_dotenv()
```

### 2. Mock AWS Services
```python
from moto import mock_s3
import boto3

@mock_s3
def test_s3_operations():
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='test')
    # Your test here
```

### 3. Debug Lambda Code
```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.debug(f"Event: {event}")
logger.info(f"Processing: {key}")
logger.warning(f"Potential issue: {msg}")
logger.error(f"Error: {error}")
```

### 4. Profile Performance
```python
import time
import cProfile

start = time.time()
# Your code here
elapsed = time.time() - start
print(f"Took {elapsed:.2f}s")
```

---

## Summary

**Yes, you can run this locally!** Choose your approach:

- 🚀 **Quick Test**: Option 1 (Python scripts)
- 🧪 **Testing**: Option 5 (Unit tests)
- 🎯 **Development**: Option 6 (Mock environment)
- 🐳 **Docker**: Option 3 (Containers)
- ☁️ **AWS Simulation**: Option 4 (LocalStack)
- 📦 **SAM**: Option 2 (AWS Serverless)

Start with Option 1 for quick testing, then move to AWS for production deployment.
