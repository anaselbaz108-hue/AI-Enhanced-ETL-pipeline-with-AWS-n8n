#!/bin/bash

# AWS Glue ETL Pipeline Deployment Script
# This script automates the deployment of the entire ETL pipeline

set -e

echo "🚀 Starting AWS Glue ETL Pipeline Deployment"

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
GLUE_DATABASE="${GLUE_DATABASE:-retail_analytics_db}"
S3_BUCKET_PREFIX="${S3_BUCKET_PREFIX:-your-company-retail}"
IAM_ROLE_PREFIX="${IAM_ROLE_PREFIX:-RetailAnalytics}"

# Derived configuration
RAW_DATA_BUCKET="${S3_BUCKET_PREFIX}-raw-data"
PROCESSED_DATA_BUCKET="${S3_BUCKET_PREFIX}-processed-data"
GLUE_ASSETS_BUCKET="${S3_BUCKET_PREFIX}-glue-assets"
ATHENA_RESULTS_BUCKET="${S3_BUCKET_PREFIX}-athena-results"

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Glue Database: $GLUE_DATABASE"
echo "  Raw Data Bucket: $RAW_DATA_BUCKET"
echo "  Processed Data Bucket: $PROCESSED_DATA_BUCKET"
echo "  Glue Assets Bucket: $GLUE_ASSETS_BUCKET"
echo "  Athena Results Bucket: $ATHENA_RESULTS_BUCKET"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is configured"

# Step 1: Create S3 Buckets
echo "📦 Creating S3 buckets..."
for bucket in $RAW_DATA_BUCKET $PROCESSED_DATA_BUCKET $GLUE_ASSETS_BUCKET $ATHENA_RESULTS_BUCKET; do
    if aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
        echo "  ℹ️  Bucket $bucket already exists"
    else
        echo "  📦 Creating bucket: $bucket"
        aws s3 mb "s3://$bucket" --region "$AWS_REGION"
        
        # Enable versioning for data buckets
        if [[ "$bucket" == *"data"* ]]; then
            aws s3api put-bucket-versioning --bucket "$bucket" --versioning-configuration Status=Enabled
        fi
    fi
done

# Step 2: Create Glue Database
echo "🗄️  Creating Glue database..."
if aws glue get-database --name "$GLUE_DATABASE" 2>/dev/null; then
    echo "  ℹ️  Database $GLUE_DATABASE already exists"
else
    echo "  🗄️  Creating database: $GLUE_DATABASE"
    aws glue create-database --database-input "Name=$GLUE_DATABASE,Description=Retail analytics database"
fi

# Step 3: Upload Glue scripts
echo "📤 Uploading Glue ETL scripts..."
aws s3 cp etl/glue_jobs/retail_data_etl.py "s3://$GLUE_ASSETS_BUCKET/scripts/"
echo "  ✅ ETL script uploaded"

# Step 4: Create sample IAM policies (files only, manual attachment required)
echo "📝 Creating IAM policy templates..."
mkdir -p /tmp/iam-policies

cat > /tmp/iam-policies/glue-service-role-policy.json << EOF
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
        "arn:aws:s3:::${RAW_DATA_BUCKET}/*",
        "arn:aws:s3:::${RAW_DATA_BUCKET}",
        "arn:aws:s3:::${PROCESSED_DATA_BUCKET}/*",
        "arn:aws:s3:::${PROCESSED_DATA_BUCKET}",
        "arn:aws:s3:::${GLUE_ASSETS_BUCKET}/*",
        "arn:aws:s3:::${GLUE_ASSETS_BUCKET}"
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
        "glue:CreatePartition",
        "glue:BatchCreatePartition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

cat > /tmp/iam-policies/lambda-execution-role-policy.json << EOF
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
        "arn:aws:s3:::${ATHENA_RESULTS_BUCKET}/*",
        "arn:aws:s3:::${ATHENA_RESULTS_BUCKET}",
        "arn:aws:s3:::${PROCESSED_DATA_BUCKET}/*",
        "arn:aws:s3:::${PROCESSED_DATA_BUCKET}"
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
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

echo "  ✅ IAM policy templates created in /tmp/iam-policies/"

# Step 5: Create deployment configuration
cat > deployment-config.json << EOF
{
  "aws_region": "$AWS_REGION",
  "glue_database": "$GLUE_DATABASE",
  "s3_buckets": {
    "raw_data": "$RAW_DATA_BUCKET",
    "processed_data": "$PROCESSED_DATA_BUCKET",
    "glue_assets": "$GLUE_ASSETS_BUCKET",
    "athena_results": "$ATHENA_RESULTS_BUCKET"
  },
  "glue_job_config": {
    "name": "retail-data-etl-job",
    "script_location": "s3://$GLUE_ASSETS_BUCKET/scripts/retail_data_etl.py",
    "max_capacity": 10
  },
  "crawler_config": {
    "raw_crawler_name": "retail-raw-data-crawler",
    "parquet_crawler_name": "retail-parquet-data-crawler"
  },
  "lambda_config": {
    "athena_executor_name": "retail-athena-query-executor",
    "ai_processor_name": "retail-ai-query-processor"
  }
}
EOF

echo "  ✅ Deployment configuration saved to deployment-config.json"

echo ""
echo "🎉 Basic infrastructure setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Create IAM roles using the policy templates in /tmp/iam-policies/"
echo "2. Update deployment-config.json with your IAM role ARNs"
echo "3. Run the Python deployment scripts:"
echo "   cd etl/crawlers && python glue_crawler_manager.py"
echo "   cd etl/glue_jobs && python job_manager.py"
echo "   cd lambda && python deployment_manager.py"
echo "4. Deploy the n8n workflow using n8n_workflow/deploy_workflow.sh"
echo "5. Upload sample data to test the pipeline"
echo ""
echo "📖 See docs/configuration_guide.md for detailed configuration instructions"