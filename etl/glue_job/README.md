# ETL Glue Job Configuration

## Overview

This directory contains the AWS Glue ETL job script that transforms raw data into optimized Parquet format for Athena queries.

## Job Configuration

### Basic Settings

- **Job Name**: `sales-data-etl-job`
- **Job Type**: `Python Shell` or `Spark`
- **Glue Version**: `4.0`
- **Python Version**: `3.9`
- **Worker Type**: `G.1X` (for small-medium datasets) or `G.2X` (for large datasets)
- **Number of Workers**: `2-10` (based on data volume)

### Job Parameters

The job accepts the following parameters:

| Parameter | Description | Example Value |
|-----------|-------------|---------------|
| `source_bucket` | S3 bucket containing raw data | `retailsalespipelinebucket` |
| `target_bucket` | S3 bucket for processed Parquet data | `retailsalespipelinebucket` |
| `database_name` | Glue catalog database name | `retail-sales-db` |

### IAM Role Requirements

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "glue:*",
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::retailsalespipelinebucket",
                "arn:aws:s3:::retailsalespipelinebucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

## Data Transformation Logic

The job performs the following transformations:

1. **Data Cleaning**
   - Remove duplicate records based on transaction_id
   - Filter out invalid/null values for key columns (transaction_id, date, customer_id, product_category, total_amount)
   - Clean negative or zero values for quantity, price_per_unit, and total_amount

2. **Data Enrichment**
   - Extract date components (year, month, day) for partitioning
   - Standardize column names (trim and lowercase)
   - Convert date column to proper date format

3. **Optimization**
   - Convert to Parquet format with Snappy compression
   - Partition by year, month, and day for optimal query performance
   - Write to processed-zone folder in S3

## Deployment

### AWS CLI

```bash
# Create Glue job
aws glue create-job \
    --name sales-data-etl-job \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/GlueServiceRole \
    --command ScriptLocation=s3://your-scripts-bucket/job_script.py,Name=glueetl \
    --default-arguments '{
        "--source_bucket":"retailsalespipelinebucket",
        "--target_bucket":"retailsalespipelinebucket",
        "--database_name":"retail-sales-db"
    }' \
    --glue-version 4.0 \
    --max-capacity 10
```

### Terraform

```hcl
resource "aws_glue_job" "sales_data_etl" {
  name         = "sales-data-etl-job"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"

  command {
    script_location = "s3://your-scripts-bucket/job_script.py"
    python_version  = "3"
  }

  default_arguments = {
    "--source_bucket"  = "retailsalespipelinebucket"
    "--target_bucket"  = "retailsalespipelinebucket"
    "--database_name"  = "retail-sales-db"
  }

  max_capacity = 10
}
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics:

- Job run duration
- Data processed (GB)
- Success/failure rates
- Cost per run

### Logging

Job logs are available in CloudWatch:
- `/aws-glue/jobs/logs-v2`
- `/aws-glue/jobs/error`
- `/aws-glue/jobs/output`

## Best Practices

1. **Performance**
   - Use appropriate worker types and counts
   - Optimize partition strategy
   - Monitor job metrics

2. **Cost Optimization**
   - Use bookmarks to process only new data
   - Right-size worker allocation
   - Schedule jobs during off-peak hours

3. **Data Quality**
   - Implement validation checks
   - Monitor schema changes
   - Handle error scenarios gracefully