# AI-Enhanced ETL Pipeline with AWS & n8n

End-to-end Retail Data Pipeline on AWS: ETL with Glue + Spark, Data Quality Layer, Parquet storage, Athena analytics, and AI-powered insights orchestrated with n8n.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Data      │    │   AWS Glue ETL   │    │  Processed Data │
│   Sources       │───▶│   + Spark        │───▶│   (Parquet)     │
│   (CSV/JSON)    │    │   Data Quality   │    │   Partitioned   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Raw Crawler    │    │   ETL Job        │    │ Parquet Crawler │
│  (Discovery)    │    │  (Transform)     │    │  (Catalog)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 │
                                 ▼
                    ┌──────────────────┐
                    │   Glue Catalog   │
                    │   (Metadata)     │
                    └──────────────────┘
                                 │
                                 ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    n8n          │    │   Lambda         │    │   Amazon        │
│  Orchestration  │───▶│   Functions      │───▶│   Athena        │
│   AI Workflow   │    │   (Query Exec)   │    │  (Analytics)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Query      │    │   Result         │    │   Email         │
│  Generation     │    │  Summarization   │    │  Notifications  │
│  (OpenAI/Bedrock)│    │   (AI Insights)  │    │   (Reports)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
├── etl/                        # AWS Glue ETL components
│   ├── crawlers/              # Glue crawler configurations
│   │   └── glue_crawler_manager.py
│   └── glue_jobs/             # ETL job scripts
│       ├── retail_data_etl.py
│       └── job_manager.py
├── lambda/                     # AWS Lambda functions
│   ├── athena_query_executor.py
│   ├── ai_query_processor.py
│   └── deployment_manager.py
├── n8n_workflow/              # n8n workflow configurations
│   ├── retail_analytics_workflow.json
│   └── deploy_workflow.sh
├── schema/                     # Database schema definitions
│   └── retail_data_schema.json
├── docs/                       # Documentation
│   └── configuration_guide.md
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- n8n instance (self-hosted or cloud)
- Python 3.9+ for local development
- AWS CLI configured
- Optional: OpenAI API key for enhanced AI features

### Step 1: AWS Infrastructure Setup

1. **Create S3 Buckets**
   ```bash
   aws s3 mb s3://your-retail-data-bucket
   aws s3 mb s3://your-athena-results-bucket
   aws s3 mb s3://your-glue-assets-bucket
   ```

2. **Create Glue Database**
   ```bash
   aws glue create-database --database-input Name=retail_analytics_db
   ```

3. **Deploy IAM Roles**
   - Create Glue service role with S3 and Glue permissions
   - Create Lambda execution role with Athena, S3, and Glue permissions
   - See [Configuration Guide](docs/configuration_guide.md) for detailed policies

### Step 2: ETL Pipeline Deployment

1. **Upload Glue Scripts**
   ```bash
   aws s3 cp etl/glue_jobs/retail_data_etl.py s3://your-glue-assets-bucket/scripts/
   ```

2. **Create Crawlers**
   ```bash
   cd etl/crawlers
   python glue_crawler_manager.py
   ```

3. **Create ETL Job**
   ```bash
   cd etl/glue_jobs
   python job_manager.py
   ```

### Step 3: Lambda Functions Deployment

1. **Deploy Lambda Functions**
   ```bash
   cd lambda
   python deployment_manager.py
   ```

2. **Set Environment Variables**
   - Configure AWS credentials
   - Set database and S3 paths
   - Add OpenAI API key (optional)

### Step 4: n8n Workflow Setup

1. **Import Workflow**
   ```bash
   cd n8n_workflow
   ./deploy_workflow.sh
   ```

2. **Configure Credentials**
   - AWS credentials in n8n
   - Email SMTP settings
   - Webhook authentication (optional)

### Step 5: Upload Sample Data

1. **Prepare Sample Data**
   ```csv
   transaction_id,customer_id,product_id,product_name,category,quantity,unit_price,total_amount,transaction_date,store_id,sales_rep_id,payment_method
   TXN001,CUST001,PROD001,Laptop Computer,Electronics,1,999.99,999.99,2023-01-15 10:30:00,STORE001,REP001,Credit Card
   ```

2. **Upload to S3**
   ```bash
   aws s3 cp sample_data.csv s3://your-retail-data-bucket/raw-data/year=2023/month=01/
   ```

3. **Run Initial Crawlers**
   ```bash
   aws glue start-crawler --name retail-raw-data-crawler
   ```

## 🎯 Usage Examples

### Basic Analytics Query
```bash
curl -X POST http://your-n8n-host:5678/webhook/retail-analytics-webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "user_request": "Show me top 10 products by revenue this month",
    "query_type": "custom",
    "recipient_email": "analyst@yourcompany.com"
  }'
```

### Predefined Reports
```bash
# Daily sales summary
curl -X POST http://your-n8n-host:5678/webhook/retail-analytics-webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "query_type": "daily_sales_summary",
    "date_range": {
      "start_date": "2023-01-01",
      "end_date": "2023-01-31"
    },
    "recipient_email": "manager@yourcompany.com"
  }'
```

### AI-Powered Natural Language Queries
```bash
curl -X POST http://your-n8n-host:5678/webhook/retail-analytics-webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "user_request": "Which customers spent more than $1000 in electronics last quarter?",
    "query_type": "custom",
    "recipient_email": "sales@yourcompany.com"
  }'
```

## 🔧 Key Features

### ETL Pipeline
- **Raw Data Ingestion**: Automated discovery of new data files
- **Data Quality Checks**: Comprehensive validation and scoring
- **Data Cleaning**: Standardization and enrichment
- **Partitioned Storage**: Efficient Parquet format with partitioning
- **Incremental Processing**: Job bookmarks for efficient re-runs

### AI-Powered Analytics
- **Natural Language to SQL**: Convert plain English to SQL queries
- **Intelligent Summarization**: AI-generated insights from query results
- **Automated Reporting**: Email reports with executive summaries
- **Flexible Query Types**: Support for both predefined and custom queries

### Monitoring & Observability
- **Data Quality Metrics**: Track data quality scores over time
- **Pipeline Monitoring**: CloudWatch integration for all components
- **Error Handling**: Comprehensive error tracking and notifications
- **Performance Optimization**: Automated query optimization suggestions

## 📊 Sample Queries Supported

1. **Sales Performance**
   - "Show me daily sales by category for the last 30 days"
   - "Which products have the highest profit margins?"
   - "Compare this month's revenue to last month"

2. **Customer Analytics**
   - "Who are our top 10 customers by lifetime value?"
   - "Show customer purchase frequency by region"
   - "Identify customers at risk of churning"

3. **Product Insights**
   - "What are the trending products this quarter?"
   - "Show inventory turnover rates by category"
   - "Which products are frequently bought together?"

4. **Operational Metrics**
   - "Show sales performance by store location"
   - "Which sales reps are exceeding their targets?"
   - "Analyze payment method preferences by demographics"

## 🛡️ Security & Compliance

- **Data Encryption**: At-rest and in-transit encryption
- **IAM Integration**: Fine-grained access controls
- **VPC Deployment**: Network isolation options
- **Audit Logging**: Comprehensive CloudTrail integration
- **Data Privacy**: PII detection and masking capabilities

## 📈 Performance & Scaling

- **Auto-scaling**: DPU-based scaling for Glue jobs
- **Query Optimization**: Automatic partitioning and indexing
- **Caching**: Result caching for frequently accessed data
- **Cost Optimization**: S3 intelligent tiering and lifecycle policies

## 🔍 Troubleshooting

### Common Issues

1. **ETL Job Failures**
   - Check CloudWatch logs for detailed error messages
   - Verify IAM permissions for S3 and Glue
   - Ensure data format matches expected schema

2. **Lambda Timeouts**
   - Increase timeout settings for complex queries
   - Optimize Athena queries with proper WHERE clauses
   - Consider using Step Functions for long-running processes

3. **n8n Workflow Errors**
   - Verify AWS credentials configuration
   - Check webhook endpoint accessibility
   - Validate JSON payload format

### Monitoring Dashboards

Set up CloudWatch dashboards to monitor:
- ETL job success rates and duration
- Lambda function performance metrics
- Athena query costs and performance
- Data quality trends over time

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support:
- Create an issue in the GitHub repository
- Check the [Configuration Guide](docs/configuration_guide.md) for detailed setup instructions
- Review AWS documentation for service-specific guidance

## 🎉 Acknowledgments

- AWS Glue and Athena teams for excellent documentation
- n8n community for workflow orchestration insights
- OpenAI for AI integration capabilities
