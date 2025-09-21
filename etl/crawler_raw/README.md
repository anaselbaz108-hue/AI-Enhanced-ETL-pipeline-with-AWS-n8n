# Raw Data Crawler Configuration

## Overview

This crawler is configured to scan the raw data S3 bucket and create a table in the Glue Data Catalog for the raw dataset before ETL processing.

## Crawler Configuration

### Basic Settings

- **Crawler Name**: `raw-data-crawler`
- **Description**: Crawl raw sales data files in S3 to create initial data catalog
- **IAM Role**: `AWSGlueServiceRole-RawDataCrawler`

### Data Source

- **S3 Path**: `s3://your-raw-data-bucket/sales/`
- **Include Path**: Include all subdirectories
- **Exclude Patterns**: 
  - `*.tmp`
  - `*_$folder$`
  - `*.log`

### Crawler Output

- **Database**: `raw_insights_db`
- **Table Prefix**: `raw_`
- **Configuration**: 
  - Update table schema: `Update the table definition in the data catalog`
  - Object deletion: `Delete tables and partitions from catalog`

### Schedule

- **Frequency**: `Daily at 2:00 AM UTC`
- **Start Date**: Based on data availability

## IAM Role Requirements

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
                "s3:ListAllMyBuckets",
                "s3:GetBucketAcl"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-raw-data-bucket/*"
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

## Expected Raw Data Format

### CSV Files

- **Delimiter**: Comma (`,`)
- **Header Row**: Yes
- **Encoding**: UTF-8
- **Date Format**: `YYYY-MM-DD`

### Sample Data Structure

```csv
order_id,customer_id,date,region,product_category,product_name,sales_amount,quantity,discount_percent,sales_rep_id
ORD-2024-001234,CUST-12345,2024-01-15,North America,Electronics,iPhone 15,1299.99,1,0.0,REP-789
ORD-2024-001235,CUST-67890,2024-01-15,Europe,Clothing,Nike Shoes,129.99,2,10.0,REP-456
```

### File Organization

```
s3://your-raw-data-bucket/sales/
├── 2024/
│   ├── 01/
│   │   ├── sales_20240101.csv
│   │   ├── sales_20240102.csv
│   │   └── ...
│   ├── 02/
│   └── ...
├── 2023/
└── ...
```

## Crawler Execution

### AWS CLI Commands

```bash
# Create crawler
aws glue create-crawler \
    --name raw-data-crawler \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/AWSGlueServiceRole-RawDataCrawler \
    --database-name raw_insights_db \
    --targets S3Targets=[{Path=s3://your-raw-data-bucket/sales/}] \
    --table-prefix raw_ \
    --schedule ScheduleExpression="cron(0 2 * * ? *)"

# Start crawler
aws glue start-crawler --name raw-data-crawler

# Check crawler status
aws glue get-crawler --name raw-data-crawler
```

### Terraform Configuration

```hcl
resource "aws_glue_crawler" "raw_data_crawler" {
  database_name = "raw_insights_db"
  name          = "raw-data-crawler"
  role          = aws_iam_role.glue_crawler_role.arn

  s3_target {
    path = "s3://your-raw-data-bucket/sales/"
  }

  schedule = "cron(0 2 * * ? *)"

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DELETE_FROM_DATABASE"
  }

  configuration = jsonencode({
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
    Version = 1
  })
}
```

## Monitoring and Troubleshooting

### CloudWatch Metrics

Monitor these metrics:
- `glue.driver.aggregate.numCompletedTasks`
- `glue.driver.aggregate.numFailedTasks`
- `glue.ALL.s3.filesystem.read_bytes`

### Common Issues

1. **Permission Denied**
   - Verify IAM role has S3 access
   - Check bucket policies

2. **Schema Detection Issues**
   - Ensure consistent file formats
   - Verify header row presence
   - Check data type consistency

3. **Large File Processing**
   - Consider file size limits
   - Use appropriate file formats
   - Monitor crawler timeouts

### Best Practices

1. **Data Quality**: Ensure consistent schema across files
2. **File Naming**: Use consistent naming conventions
3. **Partitioning**: Organize files by date/region for better performance
4. **Monitoring**: Set up CloudWatch alarms for crawler failures
5. **Cost Optimization**: Schedule crawlers during off-peak hours