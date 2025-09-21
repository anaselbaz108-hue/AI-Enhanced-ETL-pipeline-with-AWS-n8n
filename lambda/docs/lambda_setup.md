# Lambda Setup Guide

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS Lambda execution role with required permissions
- S3 bucket for Athena query results

## IAM Role Configuration

### Required Policies

The Lambda execution role needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-athena-results-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-athena-results-bucket"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetDatabase",
                "glue:GetTable",
                "glue:GetPartitions"
            ],
            "Resource": "*"
        }
    ]
}
```

## Deployment Steps

### 1. Create Lambda Function

```bash
# Create deployment package
cd lambda/athena-query-runner
zip -r athena-query-runner.zip lambda_function.py

# Create Lambda function
aws lambda create-function \
    --function-name athena-query-runner \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-athena-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://athena-query-runner.zip \
    --timeout 300 \
    --memory-size 512
```

### 2. Configure Environment Variables

```bash
aws lambda update-function-configuration \
    --function-name athena-query-runner \
    --environment Variables='{
        "ATHENA_WORKGROUP":"primary",
        "DEFAULT_DATABASE":"insights_db",
        "RESULTS_BUCKET":"your-athena-results-bucket"
    }'
```

### 3. Test Lambda Function

Create a test event:

```json
{
    "sql_query": "SELECT COUNT(*) as total_records FROM sales_data WHERE year = 2024",
    "database": "insights_db",
    "output_location": "s3://your-athena-results-bucket/test-queries/"
}
```

### 4. Update Function Code

To update the function after making changes:

```bash
# Update deployment package
cd lambda/athena-query-runner
zip -r athena-query-runner.zip lambda_function.py

# Update function code
aws lambda update-function-code \
    --function-name athena-query-runner \
    --zip-file fileb://athena-query-runner.zip
```

## Configuration Parameters

### Required Parameters

- `sql_query`: The SQL query to execute
- `database`: Target database name
- `output_location`: S3 location for query results

### Optional Parameters

- `workgroup`: Athena workgroup (default: "primary")

## Error Handling

The Lambda function handles the following error scenarios:

1. **Invalid SQL syntax**: Returns 400 with error details
2. **Permission denied**: Returns 403 with IAM guidance
3. **Query timeout**: Returns 408 after 5 minutes
4. **Service errors**: Returns 500 with error message

## Monitoring and Logging

### CloudWatch Logs

Lambda automatically creates log groups:
- `/aws/lambda/athena-query-runner`

### CloudWatch Metrics

Monitor these key metrics:
- Duration
- Error count
- Invocation count
- Throttles

### Custom Metrics

The function logs:
- Query execution time
- Data scanned (MB)
- Number of rows returned

## Security Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Network Security**: Deploy in VPC if accessing private resources
3. **Environment Variables**: Use AWS Systems Manager Parameter Store for sensitive data
4. **Query Validation**: Implement additional SQL validation if needed
5. **Resource Limits**: Set appropriate timeout and memory limits

## Troubleshooting

### Common Issues

1. **IAM Permission Errors**
   - Verify Lambda execution role has required permissions
   - Check S3 bucket policies

2. **Athena Query Failures**
   - Validate SQL syntax
   - Ensure database and table exist
   - Check data format compatibility

3. **Timeout Issues**
   - Increase Lambda timeout (max 15 minutes)
   - Optimize queries for better performance
   - Consider query result pagination

### Debug Steps

1. Check CloudWatch logs for detailed error messages
2. Test queries directly in Athena console
3. Verify IAM permissions using AWS policy simulator
4. Test with simple queries first

## Integration with n8n

The Lambda function is designed to work seamlessly with n8n workflows:

1. **Input Format**: JSON payload with query parameters
2. **Output Format**: Structured response with metadata and results
3. **Error Handling**: HTTP status codes for workflow decision making
4. **Result Pagination**: Configurable row limits for large datasets