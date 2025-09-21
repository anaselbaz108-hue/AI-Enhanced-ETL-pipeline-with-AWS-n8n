# Athena Insights Automation Project

This directory contains the complete folder structure for the **Athena Insights Automation** project that automates stakeholder data requests and business insights using AWS ETL (Glue, Crawlers, Athena, S3, Parquet) with n8n, Lambda, and AI-based query/insight generation.

## Project Structure

```
@athena_insights_auto/
├── etl/                                    # ETL Pipeline Components
│   ├── crawler_raw/                       # Raw data crawler configuration
│   │   └── README.md                      # Raw crawler setup guide
│   ├── glue_job/                          # Glue ETL job scripts
│   │   └── job_script.py                  # Main ETL transformation script
│   └── crawler_parquet/                   # Parquet data crawler configuration
│       └── README.md                      # Parquet crawler setup guide
│
├── lambda/                                 # AWS Lambda Functions
│   ├── athena-query-runner/               # Athena query execution function
│   │   ├── lambda_function.py             # Main Lambda handler
│   │   └── requirements.txt               # Python dependencies
│   └── docs/                              # Lambda documentation
│       └── lambda_setup.md                # Lambda deployment guide
│
├── n8n_workflow/                          # n8n Workflow Automation
│   ├── workflow.json                      # Complete n8n workflow definition
│   └── docs/                              # n8n documentation
│       └── n8n_steps.md                   # Workflow setup guide
│
├── schema/                                # Data Schema Documentation
│   └── dataset_schema.md                  # Database schema for AI SQL generation
│
└── README.md                              # Main project documentation
```

## Quick Start

1. **ETL Pipeline Setup**
   - Deploy Glue crawlers for raw and parquet data
   - Configure Glue ETL job for data transformation
   - Set up S3 buckets for raw and processed data

2. **Lambda Function Deployment**
   - Deploy `lambda/athena-query-runner/lambda_function.py`
   - Configure IAM roles and permissions
   - Test Athena query execution

3. **n8n Workflow Configuration**
   - Import `n8n_workflow/workflow.json`
   - Configure credentials (OpenAI, AWS, Gmail)
   - Test end-to-end workflow

4. **Schema Setup**
   - Review `schema/dataset_schema.md`
   - Validate Athena table structure
   - Test AI SQL generation

## Architecture Flow

```
Raw Data (S3) → Raw Crawler → Glue ETL Job → Parquet Data (S3) → Parquet Crawler → Athena Table
                                                                                          ↓
Gmail Insights ← AI Summary ← Lambda Query ← AI SQL Generation ← n8n Form ← Stakeholder Request
```

## Key Features

- **Automated ETL Pipeline**: Raw data processing to Parquet format
- **AI-Powered SQL Generation**: Natural language to SQL conversion
- **Serverless Query Execution**: AWS Lambda + Athena integration
- **Intelligent Insights**: AI-generated business summaries
- **Automated Notifications**: Email delivery of insights

## Prerequisites

- AWS Account with appropriate permissions
- n8n instance (cloud or self-hosted)
- OpenAI API access
- Gmail account for notifications

## Documentation

Each component includes detailed setup guides:

- **ETL Setup**: See `etl/crawler_*/README.md`
- **Lambda Deployment**: See `lambda/docs/lambda_setup.md`
- **n8n Configuration**: See `n8n_workflow/docs/n8n_steps.md`
- **Schema Reference**: See `schema/dataset_schema.md`

## Support

For detailed implementation steps, refer to the component-specific documentation files included in each directory.