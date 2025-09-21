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
| `source_bucket` | S3 bucket containing raw data | `my-raw-data-bucket` |
| `target_bucket` | S3 bucket for processed Parquet data | `my-processed-data-bucket` |
| `database_name` | Glue catalog database name | `raw_insights_db` |

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
                "arn:aws:s3:::my-raw-data-bucket",
                "arn:aws:s3:::my-raw-data-bucket/*",
                "arn:aws:s3:::my-processed-data-bucket",
                "arn:aws:s3:::my-processed-data-bucket/*"
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
   - Remove duplicate records
   - Filter out invalid/null values
   - Standardize data formats

2. **Data Enrichment**
   - Add processing timestamp
   - Extract date components for partitioning
   - Standardize categorical values

3. **Optimization**
   - Convert to Parquet format
   - Apply appropriate compression (Snappy)
   - Partition by year and month

## Deployment

### AWS CLI

```bash
# Create Glue job
aws glue create-job \
    --name sales-data-etl-job \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/GlueServiceRole \
    --command ScriptLocation=s3://your-scripts-bucket/job_script.py,Name=glueetl \
    --default-arguments '{
        "--source_bucket":"my-raw-data-bucket",
        "--target_bucket":"my-processed-data-bucket",
        "--database_name":"raw_insights_db"
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
    "--source_bucket"  = "my-raw-data-bucket"
    "--target_bucket"  = "my-processed-data-bucket"
    "--database_name"  = "raw_insights_db"
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