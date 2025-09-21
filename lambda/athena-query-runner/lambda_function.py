import boto3
import json
import time

def lambda_handler(event, context):
    # Input: {"query": "...", "db": "...", "output": "s3://your-bucket/query-results/"}
    query = event.get("query")
    db = event.get("db")
    output = event.get("output") # S3 bucket URI for query results

    client = boto3.client('athena')

    # Start Athena query execution
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': db},
        ResultConfiguration={'OutputLocation': output}
    )
    query_execution_id = response['QueryExecutionId']

    # Wait for completion (polling)
    while True:
        status = client.get_query_execution(QueryExecutionId=query_execution_id)
        state = status['QueryExecution']['Status']['State']
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(2)  # wait before polling again

    if state != 'SUCCEEDED':
        return {"error": f"Query failed: {state}"}

    result = client.get_query_results(QueryExecutionId=query_execution_id)
    # Convert Athena results to list of dicts
    rows = []
    columns = [col['Label'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]
    for row in result['ResultSet']['Rows'][1:]:  # skip header
        data = [field.get('VarCharValue', '') for field in row['Data']]
        rows.append(dict(zip(columns, data)))

    return {"rows": rows}
