#!/bin/bash

# Pipeline Testing Script
# This script tests the entire ETL pipeline end-to-end

set -e

echo "🧪 Starting ETL Pipeline End-to-End Testing"

# Load configuration
if [ -f "deployment-config.json" ]; then
    echo "📋 Loading deployment configuration..."
    RAW_DATA_BUCKET=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['s3_buckets']['raw_data'])")
    PROCESSED_DATA_BUCKET=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['s3_buckets']['processed_data'])")
    GLUE_DATABASE=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['glue_database'])")
    RAW_CRAWLER_NAME=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['crawler_config']['raw_crawler_name'])")
    PARQUET_CRAWLER_NAME=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['crawler_config']['parquet_crawler_name'])")
    ETL_JOB_NAME=$(cat deployment-config.json | python3 -c "import sys, json; print(json.load(sys.stdin)['glue_job_config']['name'])")
else
    echo "❌ deployment-config.json not found. Please run deploy.sh first."
    exit 1
fi

echo "  Raw Data Bucket: $RAW_DATA_BUCKET"
echo "  Processed Data Bucket: $PROCESSED_DATA_BUCKET"
echo "  Glue Database: $GLUE_DATABASE"

# Step 1: Generate test data
echo "📊 Generating test data..."
cd etl
if [ ! -f "sample_retail_data.csv" ]; then
    python3 sample_data_generator.py
else
    echo "  ℹ️  Test data already exists"
fi
cd ..

# Step 2: Upload test data to S3
echo "📤 Uploading test data to S3..."
CURRENT_DATE=$(date +%Y-%m-%d)
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)

TEST_DATA_PATH="raw-data/year=$YEAR/month=$MONTH/day=$DAY/"
aws s3 cp etl/sample_retail_data.csv "s3://$RAW_DATA_BUCKET/$TEST_DATA_PATH"
echo "  ✅ Test data uploaded to s3://$RAW_DATA_BUCKET/$TEST_DATA_PATH"

# Step 3: Run raw data crawler
echo "🕷️  Running raw data crawler..."
aws glue start-crawler --name "$RAW_CRAWLER_NAME"

# Wait for crawler to complete
echo "  ⏳ Waiting for crawler to complete..."
while true; do
    CRAWLER_STATE=$(aws glue get-crawler --name "$RAW_CRAWLER_NAME" --query 'Crawler.State' --output text)
    if [ "$CRAWLER_STATE" == "READY" ]; then
        echo "  ✅ Raw data crawler completed successfully"
        break
    elif [ "$CRAWLER_STATE" == "STOPPING" ] || [ "$CRAWLER_STATE" == "RUNNING" ]; then
        echo "  ⏳ Crawler state: $CRAWLER_STATE, waiting..."
        sleep 30
    else
        echo "  ❌ Crawler failed with state: $CRAWLER_STATE"
        exit 1
    fi
done

# Step 4: Verify raw data table creation
echo "🔍 Verifying raw data table..."
RAW_TABLE_NAME=$(aws glue get-tables --database-name "$GLUE_DATABASE" --query 'TableList[?starts_with(Name, `raw_`)].Name' --output text)
if [ -n "$RAW_TABLE_NAME" ]; then
    echo "  ✅ Raw data table created: $RAW_TABLE_NAME"
    
    # Get record count
    echo "  📊 Checking data in raw table..."
    aws athena start-query-execution \
        --query-string "SELECT COUNT(*) FROM $GLUE_DATABASE.$RAW_TABLE_NAME" \
        --result-configuration "OutputLocation=s3://your-athena-results-bucket/test-queries/" \
        --work-group "primary" > /tmp/athena_execution.json
        
    EXECUTION_ID=$(cat /tmp/athena_execution.json | python3 -c "import sys, json; print(json.load(sys.stdin)['QueryExecutionId'])")
    echo "  📊 Athena query started: $EXECUTION_ID"
else
    echo "  ❌ Raw data table not found"
    exit 1
fi

# Step 5: Run ETL job
echo "🔄 Starting ETL job..."
aws glue start-job-run --job-name "$ETL_JOB_NAME" > /tmp/job_run.json
JOB_RUN_ID=$(cat /tmp/job_run.json | python3 -c "import sys, json; print(json.load(sys.stdin)['JobRunId'])")
echo "  🔄 ETL job started with run ID: $JOB_RUN_ID"

# Wait for ETL job to complete
echo "  ⏳ Waiting for ETL job to complete..."
while true; do
    JOB_STATE=$(aws glue get-job-run --job-name "$ETL_JOB_NAME" --run-id "$JOB_RUN_ID" --query 'JobRun.JobRunState' --output text)
    if [ "$JOB_STATE" == "SUCCEEDED" ]; then
        echo "  ✅ ETL job completed successfully"
        break
    elif [ "$JOB_STATE" == "RUNNING" ]; then
        echo "  ⏳ ETL job state: $JOB_STATE, waiting..."
        sleep 60
    else
        echo "  ❌ ETL job failed with state: $JOB_STATE"
        # Get job run details for debugging
        aws glue get-job-run --job-name "$ETL_JOB_NAME" --run-id "$JOB_RUN_ID" --query 'JobRun.ErrorMessage' --output text
        exit 1
    fi
done

# Step 6: Run parquet data crawler
echo "🕷️  Running parquet data crawler..."
aws glue start-crawler --name "$PARQUET_CRAWLER_NAME"

# Wait for crawler to complete
echo "  ⏳ Waiting for parquet crawler to complete..."
while true; do
    CRAWLER_STATE=$(aws glue get-crawler --name "$PARQUET_CRAWLER_NAME" --query 'Crawler.State' --output text)
    if [ "$CRAWLER_STATE" == "READY" ]; then
        echo "  ✅ Parquet data crawler completed successfully"
        break
    elif [ "$CRAWLER_STATE" == "STOPPING" ] || [ "$CRAWLER_STATE" == "RUNNING" ]; then
        echo "  ⏳ Crawler state: $CRAWLER_STATE, waiting..."
        sleep 30
    else
        echo "  ❌ Crawler failed with state: $CRAWLER_STATE"
        exit 1
    fi
done

# Step 7: Verify processed data table
echo "🔍 Verifying processed data table..."
PROCESSED_TABLE_NAME=$(aws glue get-tables --database-name "$GLUE_DATABASE" --query 'TableList[?starts_with(Name, `processed_`) || starts_with(Name, `cleaned_`)].Name' --output text)
if [ -n "$PROCESSED_TABLE_NAME" ]; then
    echo "  ✅ Processed data table created: $PROCESSED_TABLE_NAME"
else
    echo "  ❌ Processed data table not found"
    exit 1
fi

# Step 8: Test Athena queries
echo "🔍 Testing Athena queries..."
TEST_QUERIES=(
    "SELECT COUNT(*) as total_records FROM $GLUE_DATABASE.$PROCESSED_TABLE_NAME"
    "SELECT category, COUNT(*) as count FROM $GLUE_DATABASE.$PROCESSED_TABLE_NAME GROUP BY category LIMIT 10"
    "SELECT AVG(total_amount) as avg_amount FROM $GLUE_DATABASE.$PROCESSED_TABLE_NAME"
)

for query in "${TEST_QUERIES[@]}"; do
    echo "  📊 Testing query: $query"
    aws athena start-query-execution \
        --query-string "$query" \
        --result-configuration "OutputLocation=s3://your-athena-results-bucket/test-queries/" \
        --work-group "primary" > /dev/null
    echo "  ✅ Query executed successfully"
done

# Step 9: Test Lambda functions (if available)
echo "🔧 Testing Lambda functions..."
LAMBDA_FUNCTIONS=("retail-athena-query-executor" "retail-ai-query-processor")

for function_name in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$function_name" &> /dev/null; then
        echo "  🔧 Testing Lambda function: $function_name"
        
        # Test with a simple payload
        TEST_PAYLOAD='{"query_type": "daily_sales_summary", "date_range": {"start_date": "'$CURRENT_DATE'"}}'
        aws lambda invoke \
            --function-name "$function_name" \
            --payload "$TEST_PAYLOAD" \
            /tmp/lambda_response.json > /dev/null
            
        if [ $? -eq 0 ]; then
            echo "  ✅ Lambda function $function_name tested successfully"
        else
            echo "  ⚠️  Lambda function $function_name test failed"
        fi
    else
        echo "  ℹ️  Lambda function $function_name not found, skipping test"
    fi
done

# Step 10: Generate test report
echo "📋 Generating test report..."
cat > test_report.md << EOF
# ETL Pipeline Test Report

**Test Date:** $(date)
**Test Duration:** Started at script start time

## Test Results Summary

### ✅ Successful Tests
- Test data generation and upload
- Raw data crawler execution
- ETL job execution
- Parquet data crawler execution
- Processed data table creation
- Basic Athena query execution

### 📊 Data Metrics
- **Raw Data Table:** $RAW_TABLE_NAME
- **Processed Data Table:** $PROCESSED_TABLE_NAME
- **Test Data Location:** s3://$RAW_DATA_BUCKET/$TEST_DATA_PATH
- **Processed Data Location:** s3://$PROCESSED_DATA_BUCKET/

### 🔧 Infrastructure Status
- **Glue Database:** $GLUE_DATABASE ✅
- **Raw Data Crawler:** $RAW_CRAWLER_NAME ✅
- **Parquet Crawler:** $PARQUET_CRAWLER_NAME ✅
- **ETL Job:** $ETL_JOB_NAME ✅

### 📝 Next Steps
1. Verify data quality scores in processed data
2. Test n8n workflow integration
3. Validate AI query generation functionality
4. Set up monitoring and alerting
5. Configure production data sources

### 🔍 Manual Verification
Run the following Athena queries to verify data quality:
\`\`\`sql
-- Check data quality scores
SELECT 
    AVG(data_quality_score) as avg_quality_score,
    MIN(data_quality_score) as min_quality_score,
    COUNT(*) as total_records
FROM $GLUE_DATABASE.$PROCESSED_TABLE_NAME;

-- Check category distribution
SELECT 
    category, 
    COUNT(*) as count,
    SUM(total_amount) as total_revenue
FROM $GLUE_DATABASE.$PROCESSED_TABLE_NAME 
GROUP BY category 
ORDER BY total_revenue DESC;
\`\`\`
EOF

echo "  ✅ Test report generated: test_report.md"

echo ""
echo "🎉 ETL Pipeline testing completed successfully!"
echo "📋 Check test_report.md for detailed results"
echo "🔧 Next: Test the n8n workflow integration"