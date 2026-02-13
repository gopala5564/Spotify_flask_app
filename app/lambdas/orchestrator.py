"""AWS Lambda orchestrator for Spotify ETL pipeline"""

import json
import logging
import os
import boto3
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
DATA_LAKE_BUCKET = os.getenv('DATA_LAKE_BUCKET')


def lambda_handler(event, context):
    """
    Orchestrates the complete Spotify ETL pipeline (Extract -> Transform -> Load)
    
    Event format:
    {
        "pipeline_type": "full" | "extract_only",
        "data_types": ["playlists", "tracks", "audio_features"],
        "retry_on_error": true | false
    }
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        {
            "statusCode": 200 | 500,
            "body": JSON string with pipeline results
        }
    """
    try:
        logger.info(f"ETL Orchestrator invoked with event: {json.dumps(event)}")
        
        if not DATA_LAKE_BUCKET:
            raise ValueError("DATA_LAKE_BUCKET environment variable not set")
        
        pipeline_type = event.get('pipeline_type', 'full')
        data_types = event.get('data_types', ['playlists'])
        retry_on_error = event.get('retry_on_error', False)
        
        execution_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        results = {
            'execution_id': execution_id,
            'pipeline_type': pipeline_type,
            'steps': [],
            'summary': {
                'total_steps': 0,
                'successful_steps': 0,
                'failed_steps': 0
            },
            'started_at': datetime.utcnow().isoformat()
        }
        
        # ==================
        # EXTRACT STAGE
        # ==================
        logger.info("=" * 60)
        logger.info("STAGE 1: EXTRACTION")
        logger.info("=" * 60)
        
        extract_results = []
        for data_type in data_types:
            try:
                logger.info(f"Extracting {data_type}...")
                
                extract_result = invoke_lambda('spotify-etl-extract', {
                    'action': data_type
                })
                
                step_status = extract_result.get('statusCode') == 200
                extract_results.append({
                    'data_type': data_type,
                    'status': 'success' if step_status else 'failed',
                    'details': json.loads(extract_result.get('body', '{}'))
                })
                
                results['steps'].append({
                    'stage': 'extract',
                    'data_type': data_type,
                    'status': 'success' if step_status else 'failed',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                results['summary']['total_steps'] += 1
                if step_status:
                    results['summary']['successful_steps'] += 1
                else:
                    results['summary']['failed_steps'] += 1
                    
            except Exception as e:
                logger.error(f"Error extracting {data_type}: {str(e)}", exc_info=True)
                results['steps'].append({
                    'stage': 'extract',
                    'data_type': data_type,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                results['summary']['total_steps'] += 1
                results['summary']['failed_steps'] += 1
                
                if not retry_on_error:
                    raise
        
        # Check if we should continue
        if results['summary']['failed_steps'] > 0 and not retry_on_error:
            raise Exception(f"Extraction failed for {results['summary']['failed_steps']} data types")
        
        # ==================
        # TRANSFORM STAGE
        # ==================
        if pipeline_type == 'full':
            logger.info("=" * 60)
            logger.info("STAGE 2: TRANSFORMATION")
            logger.info("=" * 60)
            
            for extract_result in extract_results:
                try:
                    data_type = extract_result['data_type']
                    details = extract_result['details']
                    
                    if extract_result['status'] == 'failed':
                        logger.warning(f"Skipping transform for {data_type} due to extraction failure")
                        continue
                    
                    raw_key = details.get('results', {}).get('s3_location', '').replace(f"s3://{DATA_LAKE_BUCKET}/", "")
                    
                    if not raw_key:
                        logger.warning(f"No raw key found for {data_type}")
                        continue
                    
                    logger.info(f"Transforming {data_type}...")
                    
                    transform_result = invoke_lambda('spotify-etl-transform', {
                        'raw_key': raw_key,
                        'data_type': data_type
                    })
                    
                    step_status = transform_result.get('statusCode') == 200
                    results['steps'].append({
                        'stage': 'transform',
                        'data_type': data_type,
                        'status': 'success' if step_status else 'failed',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    results['summary']['total_steps'] += 1
                    if step_status:
                        results['summary']['successful_steps'] += 1
                    else:
                        results['summary']['failed_steps'] += 1
                        
                except Exception as e:
                    logger.error(f"Error transforming {data_type}: {str(e)}", exc_info=True)
                    results['steps'].append({
                        'stage': 'transform',
                        'data_type': data_type,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    results['summary']['total_steps'] += 1
                    results['summary']['failed_steps'] += 1
            
            # ==================
            # LOAD STAGE
            # ==================
            logger.info("=" * 60)
            logger.info("STAGE 3: LOADING")
            logger.info("=" * 60)
            
            for data_type in data_types:
                try:
                    logger.info(f"Loading {data_type}...")
                    
                    # Get the processed key from transform (in real scenario, would query manifest)
                    timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
                    processed_key = f"processed/{data_type}/{timestamp}/{data_type}_processed.json"
                    
                    load_result = invoke_lambda('spotify-etl-load', {
                        'processed_key': processed_key,
                        'data_type': data_type
                    })
                    
                    step_status = load_result.get('statusCode') == 200
                    results['steps'].append({
                        'stage': 'load',
                        'data_type': data_type,
                        'status': 'success' if step_status else 'failed',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    results['summary']['total_steps'] += 1
                    if step_status:
                        results['summary']['successful_steps'] += 1
                    else:
                        results['summary']['failed_steps'] += 1
                        
                except Exception as e:
                    logger.error(f"Error loading {data_type}: {str(e)}", exc_info=True)
                    results['steps'].append({
                        'stage': 'load',
                        'data_type': data_type,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    results['summary']['total_steps'] += 1
                    results['summary']['failed_steps'] += 1
        
        # Final summary
        results['completed_at'] = datetime.utcnow().isoformat()
        overall_success = results['summary']['failed_steps'] == 0
        
        logger.info("=" * 60)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Execution ID: {execution_id}")
        logger.info(f"Status: {'SUCCESS' if overall_success else 'FAILED'}")
        logger.info(f"Total Steps: {results['summary']['total_steps']}")
        logger.info(f"Successful: {results['summary']['successful_steps']}")
        logger.info(f"Failed: {results['summary']['failed_steps']}")
        
        return {
            'statusCode': 200 if overall_success else 500,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error in ETL orchestrator: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def invoke_lambda(function_name, payload):
    """
    Invoke another Lambda function synchronously
    
    Args:
        function_name: Full function name (e.g., 'spotify-etl-extract')
        payload: Event payload to send
    
    Returns:
        Lambda response
    """
    try:
        logger.info(f"Invoking Lambda function: {function_name}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response payload
        response_payload = json.loads(response['Payload'].read())
        logger.info(f"Lambda response: {json.dumps(response_payload)}")
        
        return response_payload
        
    except Exception as e:
        logger.error(f"Error invoking Lambda {function_name}: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
