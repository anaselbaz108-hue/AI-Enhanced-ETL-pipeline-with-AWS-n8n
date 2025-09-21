# Parquet Data Crawler Configuration

## Overview

This crawler scans the processed Parquet data in S3 and creates/updates the table in the Glue Data Catalog that will be used by Athena for queries.

## Crawler Configuration

### Basic Settings

- **Crawler Name**: `parquet-data-crawler`
- **Description**: Crawl processed Parquet data files for Athena queries
- **IAM Role**: `AWSGlueServiceRole-ParquetDataCrawler`

### Data Source

- **S3 Path**: `s3://retailsalespipelinebucket/processed-zone/`
- **Include Path**: Include all subdirectories
- **Exclude Patterns**: 
  - `*_metadata`
  - `*.crc`
  - `_SUCCESS`

### Crawler Output

- **Database**: `retail-sales-db`
- **Table Name**: `processed_zone` (automatically detected)
- **Configuration**: 
  - Update table schema: `Update the table definition in the data catalog`
  - Object deletion: `Delete tables and partitions from catalog`
  - Add new partitions: `Yes`

### Schedule

- **Frequency**: `Daily at 3:00 AM UTC` (after ETL job completion)
- **Dependency**: Runs after Glue ETL job completion

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

## Expected Parquet Data Structure

### File Organization

```
s3://retailsalespipelinebucket/processed-zone/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   ├── part-00000-<uuid>.snappy.parquet
│   │   │   └── part-00001-<uuid>.snappy.parquet
│   │   ├── day=02/
│   │   └── ...
│   ├── month=02/
│   └── ...
├── year=2023/
└── ...
```

### Partition Structure

The crawler will automatically detect partitions based on directory structure:
- **year**: Integer partition key
- **month**: Integer partition key  
- **day**: Integer partition key

### Schema Detection

The crawler will detect the following schema from Parquet metadata:

```sql
CREATE EXTERNAL TABLE `processed_zone`(
  `transaction_id` string,
  `date` date,
  `customer_id` string,
  `gender` string,
  `age` int,
  `product_category` string,
  `quantity` int,
  `price_per_unit` decimal(10,2),
  `total_amount` decimal(10,2)
) 
PARTITIONED BY (
  `year` int,
  `month` int,
  `day` int
)
STORED AS PARQUET
LOCATION 's3://retailsalespipelinebucket/processed-zone/'
```

## Crawler Execution

### AWS CLI Commands

```bash
# Create database first
aws glue create-database \
    --database-input Name=retail-sales-db,Description="Database for retail sales data"

# Create crawler
aws glue create-crawler \
    --name parquet-data-crawler \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/AWSGlueServiceRole-ParquetDataCrawler \
    --database-name retail-sales-db \
    --targets S3Targets=[{Path=s3://retailsalespipelinebucket/processed-zone/}] \
    --schedule ScheduleExpression="cron(0 3 * * ? *)"

# Start crawler
aws glue start-crawler --name parquet-data-crawler

# Check crawler status
aws glue get-crawler --name parquet-data-crawler

# Get table information
aws glue get-table --database-name retail-sales-db --name processed_zone
```

### Terraform Configuration

```hcl
resource "aws_glue_database" "retail_sales_db" {
  name        = "retail-sales-db"
  description = "Database for retail sales data"
}

resource "aws_glue_crawler" "parquet_data_crawler" {
  database_name = aws_glue_database.retail_sales_db.name
  name          = "parquet-data-crawler"
  role          = aws_iam_role.glue_crawler_role.arn

  s3_target {
    path = "s3://retailsalespipelinebucket/processed-zone/"
  }

  schedule = "cron(0 3 * * ? *)"

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
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
    }
    Version = 1
  })
}
```

## Partition Management

### Automatic Partition Discovery

The crawler automatically:
1. Detects new partitions in the S3 structure
2. Updates the table metadata
3. Removes partitions for deleted data

### Manual Partition Management

```bash
# Add specific partition
aws glue create-partition \
    --database-name retail-sales-db \
    --table-name processed_zone \
    --partition-input Values=["2024","01","15"],StorageDescriptor='{...}'

# Update partition
aws glue update-partition \
    --database-name retail-sales-db \
    --table-name processed_zone \
    --partition-value-list 2024 01 15 \
    --partition-input Values=["2024","01","15"],StorageDescriptor='{...}'
```

## Athena Integration

### Query Examples

After crawler execution, data is available in Athena:

```sql
-- Basic query
SELECT product_category, SUM(total_amount) as total_sales
FROM retail_sales_db.processed_zone
WHERE year = 2024 AND month = 1
GROUP BY product_category;

-- Gender-based analysis with partition pruning
SELECT gender, COUNT(*) as transactions, SUM(total_amount) as revenue
FROM retail_sales_db.processed_zone
WHERE year = 2024 AND month BETWEEN 1 AND 3
GROUP BY gender;

-- Show partitions
SHOW PARTITIONS retail_sales_db.processed_zone;
```

### Performance Optimization

1. **Partition Pruning**: Always include partition filters
2. **Columnar Queries**: Select only needed columns
3. **Compression**: Use Snappy compression for Parquet
4. **File Size**: Optimal file size 128MB-1GB

## Monitoring and Troubleshooting

### CloudWatch Metrics

Monitor:
- Crawler run duration
- Number of partitions added
- Schema changes detected
- Errors and warnings

### Common Issues

1. **Schema Evolution**
   - New columns in Parquet files
   - Data type changes
   - Solution: Configure schema update policies

2. **Partition Detection**
   - Missing partitions
   - Incorrect partition values
   - Solution: Check S3 directory structure

3. **Performance Issues**
   - Large number of small files
   - Excessive partitions
   - Solution: Optimize ETL job output

### Best Practices

1. **Regular Schedules**: Run crawler after ETL completion
2. **Schema Validation**: Monitor schema changes
3. **Partition Strategy**: Use appropriate partition granularity
4. **Cost Management**: Monitor crawler costs and optimize frequency
5. **Data Quality**: Validate Parquet file integrity

## Integration with Athena Workbooks

### Query Templates

Create saved queries in Athena for common patterns:

```sql
-- Monthly sales summary by demographics
SELECT 
    year,
    month,
    gender,
    product_category,
    SUM(total_amount) as revenue,
    COUNT(*) as transaction_count,
    AVG(age) as avg_customer_age
FROM retail_sales_db.processed_zone
WHERE year = ${year} AND month = ${month}
GROUP BY year, month, gender, product_category
ORDER BY revenue DESC;
```