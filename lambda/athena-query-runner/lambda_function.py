"""
AWS Lambda function for running Athena queries
Receives SQL query, database, and output location, runs Athena query, and returns result metadata.
"""

import json
import boto3
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
athena_client = boto3.client('athena')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for executing Athena queries
    
    Expected event structure:
    {
        "sql_query": "SELECT * FROM table",
        "database": "database_name",
        "output_location": "s3://bucket/path/",
        "workgroup": "primary"  # optional
    }
    """
    try:
        # Extract parameters from event
        sql_query = event.get('sql_query')
        database = event.get('database')
        output_location = event.get('output_location')
        workgroup = event.get('workgroup', 'primary')
        
        # Validate required parameters
        if not all([sql_query, database, output_location]):
            raise ValueError("Missing required parameters: sql_query, database, output_location")
        
        logger.info(f"Executing query in database: {database}")
        logger.info(f"Query: {sql_query}")
        
        # Start Athena query execution
        response = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': output_location},
            WorkGroup=workgroup
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Query execution started with ID: {query_execution_id}")
        
        # Wait for query completion
        max_wait_time = 300  # 5 minutes
        wait_interval = 5    # 5 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            query_status = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            status = query_status['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED']:
                logger.info(f"Query completed successfully")
                
                # Get query results metadata
                result_metadata = {
                    'query_execution_id': query_execution_id,
                    'status': status,
                    'data_scanned_mb': query_status['QueryExecution']['Statistics'].get('DataScannedInBytes', 0) / (1024 * 1024),
                    'execution_time_ms': query_status['QueryExecution']['Statistics'].get('TotalExecutionTimeInMillis', 0),
                    'output_location': query_status['QueryExecution']['ResultConfiguration']['OutputLocation']
                }
                
                # Get query results
                results = get_query_results(query_execution_id)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'metadata': result_metadata,
                        'results': results
                    })
                }
                
            elif status in ['FAILED', 'CANCELLED']:
                error_reason = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                logger.error(f"Query failed: {error_reason}")
                
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': f"Query failed: {error_reason}",
                        'query_execution_id': query_execution_id
                    })
                }
            
            # Wait before checking again
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # Query timed out
        return {
            'statusCode': 408,
            'body': json.dumps({
                'success': False,
                'error': 'Query execution timed out',
                'query_execution_id': query_execution_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error executing Athena query: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def get_query_results(query_execution_id: str, max_rows: int = 100) -> Dict[str, Any]:
    """
    Retrieve query results from Athena
    """
    try:
        paginator = athena_client.get_paginator('get_query_results')
        page_iterator = paginator.paginate(
            QueryExecutionId=query_execution_id,
            MaxItems=max_rows
        )
        
        results = {
            'columns': [],
            'rows': [],
            'row_count': 0
        }
        
        first_page = True
        for page in page_iterator:
            if first_page:
                # Extract column names from first row
                if page['ResultSet']['Rows']:
                    header_row = page['ResultSet']['Rows'][0]
                    results['columns'] = [col.get('VarCharValue', '') for col in header_row['Data']]
                    
                    # Process data rows (skip header)
                    for row in page['ResultSet']['Rows'][1:]:
                        row_data = [col.get('VarCharValue', '') for col in row['Data']]
                        results['rows'].append(row_data)
                        results['row_count'] += 1
                        
                first_page = False
            else:
                # Process all rows in subsequent pages
                for row in page['ResultSet']['Rows']:
                    row_data = [col.get('VarCharValue', '') for col in row['Data']]
                    results['rows'].append(row_data)
                    results['row_count'] += 1
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving query results: {str(e)}")
        return {
            'columns': [],
            'rows': [],
            'row_count': 0,
            'error': str(e)
        }