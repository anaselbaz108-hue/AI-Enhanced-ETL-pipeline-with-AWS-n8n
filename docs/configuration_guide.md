# Configuration Guide for AI-Enhanced ETL Pipeline

## AWS Services Configuration

### 1. S3 Buckets Setup
Create the following S3 buckets:
- `your-retail-data-bucket` - For raw and processed data
- `your-athena-results-bucket` - For Athena query results
- `your-glue-assets-bucket` - For Glue scripts and temporary files

### 2. IAM Roles and Policies

#### Glue Service Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-retail-data-bucket/*",
        "arn:aws:s3:::your-retail-data-bucket",
        "arn:aws:s3:::your-glue-assets-bucket/*",
        "arn:aws:s3:::your-glue-assets-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartition",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:CreatePartition"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
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
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-athena-results-bucket/*",
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

### 3. Environment Variables

#### For Lambda Functions
- `ATHENA_DATABASE`: `retail_analytics_db`
- `ATHENA_OUTPUT_LOCATION`: `s3://your-athena-results-bucket/query-results/`
- `OPENAI_API_KEY`: Your OpenAI API key (optional)

#### For n8n
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: `us-east-1` (or your preferred region)
- `EMAIL_HOST`: Your SMTP server
- `EMAIL_PORT`: SMTP port (usually 587 or 465)
- `EMAIL_USER`: Email username
- `EMAIL_PASSWORD`: Email password

## Database Configuration

### Glue Catalog Database
Create a database named `retail_analytics_db` in the AWS Glue Catalog.

### Tables
The crawlers will automatically create tables, but you can pre-create them using the schema definitions in `/schema/retail_data_schema.json`.

## Sample Data Format

### Raw Data CSV Format
```csv
transaction_id,customer_id,product_id,product_name,category,quantity,unit_price,total_amount,transaction_date,store_id,sales_rep_id,payment_method
TXN001,CUST001,PROD001,Laptop Computer,Electronics,1,999.99,999.99,2023-01-15 10:30:00,STORE001,REP001,Credit Card
TXN002,CUST002,PROD002,Running Shoes,Sports,2,89.99,179.98,2023-01-15 11:45:00,STORE002,REP002,Cash
```

## API Endpoints

### n8n Webhook
- **URL**: `http://your-n8n-host:5678/webhook/retail-analytics-webhook`
- **Method**: POST
- **Content-Type**: application/json

#### Request Format
```json
{
  "user_request": "Show me top 10 products by revenue this month",
  "query_type": "custom",
  "date_range": {
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  },
  "filters": {
    "category": "Electronics",
    "store_id": "STORE001"
  },
  "recipient_email": "stakeholder@yourcompany.com"
}
```

#### Predefined Query Types
- `daily_sales_summary`
- `top_products`
- `customer_analytics`
- `revenue_trends`
- `custom`

## Security Considerations

1. **Network Security**
   - Use VPC endpoints for AWS services
   - Implement security groups and NACLs
   - Enable S3 bucket encryption

2. **IAM Security**
   - Follow principle of least privilege
   - Use IAM roles instead of access keys where possible
   - Enable CloudTrail for auditing

3. **Data Security**
   - Encrypt data at rest and in transit
   - Implement data classification
   - Use AWS KMS for key management

4. **API Security**
   - Implement API authentication
   - Use HTTPS for all communications
   - Implement rate limiting

## Monitoring and Alerting

### CloudWatch Metrics
- Glue job success/failure rates
- Lambda function duration and errors
- Athena query performance
- S3 bucket access patterns

### Recommended Alarms
- ETL job failures
- Lambda function errors
- High query execution times
- Data quality score drops

## Cost Optimization

1. **S3 Storage**
   - Use S3 Intelligent Tiering
   - Implement lifecycle policies
   - Use compression for data storage

2. **Athena**
   - Use partitioning effectively
   - Compress data in Parquet format
   - Limit query scope with WHERE clauses

3. **Lambda**
   - Optimize memory allocation
   - Use provisioned concurrency only when needed
   - Monitor and adjust timeout settings

4. **Glue**
   - Use appropriate worker types
   - Enable job bookmarks
   - Monitor DPU usage and optimize