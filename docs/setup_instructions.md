# Step-by-Step Setup Instructions

This guide provides detailed instructions for setting up the AI-Enhanced ETL Pipeline with AWS and n8n.

## Prerequisites

- AWS Account with administrative permissions
- AWS CLI installed and configured
- Python 3.9 or later
- n8n instance (self-hosted or cloud)
- Basic understanding of AWS services (S3, Glue, Lambda, Athena)

## Phase 1: Infrastructure Setup (30-45 minutes)

### 1.1 Clone and Prepare Repository
```bash
git clone <repository-url>
cd AI-Enhanced-ETL-pipeline-with-AWS-n8n
```

### 1.2 Configure AWS Environment
```bash
# Configure AWS CLI if not already done
aws configure

# Verify configuration
aws sts get-caller-identity
```

### 1.3 Run Infrastructure Deployment
```bash
# Make scripts executable
chmod +x deploy.sh
chmod +x test_pipeline.sh

# Run deployment script
./deploy.sh
```

### 1.4 Create IAM Roles
1. Go to AWS IAM Console
2. Create two roles using the policy templates in `/tmp/iam-policies/`:
   - **GlueServiceRole**: For AWS Glue crawlers and jobs
   - **LambdaExecutionRole**: For Lambda functions

3. Update `deployment-config.json` with the ARNs of created roles

## Phase 2: ETL Pipeline Setup (20-30 minutes)

### 2.1 Deploy Glue Crawlers
```bash
cd etl/crawlers
python glue_crawler_manager.py
```

### 2.2 Deploy Glue ETL Job
```bash
cd ../glue_jobs
python job_manager.py
```

### 2.3 Deploy Lambda Functions
```bash
cd ../../lambda
python deployment_manager.py
```

## Phase 3: n8n Workflow Setup (15-20 minutes)

### 3.1 Import Workflow
```bash
cd ../n8n_workflow
./deploy_workflow.sh
```

### 3.2 Configure n8n Credentials
1. Open n8n interface
2. Go to Settings > Credentials
3. Add AWS credentials:
   - Access Key ID
   - Secret Access Key
   - Region

4. Add Email credentials:
   - SMTP Host
   - Port
   - Username
   - Password

### 3.3 Set Environment Variables
In n8n, configure these environment variables:
- `OPENAI_API_KEY` (optional)
- `AWS_REGION`
- `ATHENA_DATABASE`

## Phase 4: Testing and Validation (20-30 minutes)

### 4.1 Generate and Upload Test Data
```bash
cd ../etl
python sample_data_generator.py

# Upload to S3 (replace bucket name)
aws s3 cp sample_retail_data.csv s3://your-retail-data-bucket/raw-data/year=2023/month=12/
```

### 4.2 Run End-to-End Pipeline Test
```bash
cd ..
./test_pipeline.sh
```

### 4.3 Test n8n Workflow
```bash
# Test webhook endpoint
curl -X POST http://your-n8n-host:5678/webhook/retail-analytics-webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "user_request": "Show me top 10 products by revenue",
    "query_type": "custom",
    "recipient_email": "test@example.com"
  }'
```

## Phase 5: Production Configuration (30-45 minutes)

### 5.1 Security Hardening
1. **Enable S3 bucket encryption**:
   ```bash
   aws s3api put-bucket-encryption \
     --bucket your-retail-data-bucket \
     --server-side-encryption-configuration '{
       "Rules": [{
         "ApplyServerSideEncryptionByDefault": {
           "SSEAlgorithm": "AES256"
         }
       }]
     }'
   ```

2. **Configure VPC endpoints** (if using VPC)
3. **Set up CloudTrail** for auditing
4. **Enable GuardDuty** for security monitoring

### 5.2 Monitoring and Alerting
1. **Create CloudWatch Dashboard**:
   - Glue job metrics
   - Lambda function metrics
   - Athena query metrics

2. **Set up CloudWatch Alarms**:
   ```bash
   # Example: ETL job failure alarm
   aws cloudwatch put-metric-alarm \
     --alarm-name "ETL-Job-Failures" \
     --alarm-description "Alert on ETL job failures" \
     --metric-name "glue.driver.aggregate.numFailedTasks" \
     --namespace "AWS/Glue" \
     --statistic "Sum" \
     --period 300 \
     --threshold 1 \
     --comparison-operator "GreaterThanOrEqualToThreshold"
   ```

### 5.3 Cost Optimization
1. **S3 Lifecycle Policies**:
   ```json
   {
     "Rules": [{
       "ID": "RetailDataLifecycle",
       "Status": "Enabled",
       "Transitions": [{
         "Days": 30,
         "StorageClass": "STANDARD_IA"
       }, {
         "Days": 90,
         "StorageClass": "GLACIER"
       }]
     }]
   }
   ```

2. **Glue Job Optimization**:
   - Enable job bookmarks
   - Use appropriate DPU settings
   - Implement partition pruning

## Phase 6: Data Integration (Ongoing)

### 6.1 Connect Real Data Sources
1. **Configure data ingestion**:
   - Set up S3 event notifications
   - Configure Lambda triggers for new files
   - Implement error handling and retry logic

2. **Schema evolution**:
   - Monitor schema changes
   - Update crawlers as needed
   - Implement backward compatibility

### 6.2 Scale for Production
1. **Horizontal scaling**:
   - Increase Glue job capacity
   - Configure Lambda concurrency
   - Optimize Athena query performance

2. **Data partitioning strategy**:
   - Implement date-based partitioning
   - Add business dimension partitioning
   - Optimize for query patterns

## Troubleshooting Guide

### Common Issues and Solutions

#### ETL Job Failures
```bash
# Check Glue job logs
aws logs describe-log-groups --log-group-name-prefix /aws-glue

# Get specific job run details
aws glue get-job-run --job-name retail-data-etl-job --run-id <run-id>
```

#### Lambda Function Errors
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda

# Get function details
aws lambda get-function --function-name retail-athena-query-executor
```

#### Athena Query Issues
- **Permission errors**: Check IAM roles and S3 bucket policies
- **Performance issues**: Review partitioning strategy and query optimization
- **Cost concerns**: Implement query result caching and data compression

#### n8n Workflow Problems
- **Connection errors**: Verify AWS credentials and network connectivity
- **Timeout issues**: Increase workflow timeouts for long-running queries
- **Authentication failures**: Check API keys and credentials configuration

### Performance Optimization Tips

1. **Data Format Optimization**:
   - Use Parquet format for columnar storage
   - Implement compression (GZIP, Snappy)
   - Optimize file sizes (128MB-1GB per file)

2. **Query Optimization**:
   - Use partitioning effectively
   - Implement predicate pushdown
   - Limit data scanned with WHERE clauses

3. **Resource Optimization**:
   - Right-size Glue DPUs based on data volume
   - Configure Lambda memory allocation
   - Use reserved capacity for predictable workloads

## Maintenance Checklist

### Daily
- [ ] Check ETL job execution status
- [ ] Monitor data quality scores
- [ ] Review error logs and alerts

### Weekly
- [ ] Analyze query performance metrics
- [ ] Review cost optimization opportunities
- [ ] Check data freshness and completeness

### Monthly
- [ ] Update security configurations
- [ ] Review and optimize partition strategy
- [ ] Assess capacity planning needs
- [ ] Update documentation and runbooks

## Next Steps

After successful setup, consider these enhancements:

1. **Advanced Analytics**:
   - Implement machine learning models
   - Add predictive analytics capabilities
   - Create real-time streaming pipelines

2. **Data Governance**:
   - Implement data catalog and lineage tracking
   - Add data quality monitoring
   - Establish data retention policies

3. **Integration Expansion**:
   - Connect additional data sources
   - Implement CDC (Change Data Capture)
   - Add data lake capabilities

4. **User Experience**:
   - Build business intelligence dashboards
   - Create self-service analytics tools
   - Implement role-based access controls

## Support and Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **n8n Documentation**: https://docs.n8n.io/
- **Project Issues**: Use GitHub issues for bug reports and feature requests
- **Community Support**: Join AWS and n8n communities for additional help