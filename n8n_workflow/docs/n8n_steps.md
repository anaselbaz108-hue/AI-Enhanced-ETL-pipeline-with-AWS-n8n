# n8n Workflow Setup Guide

## Overview

This guide walks through setting up the complete n8n workflow for automated stakeholder data insights using Athena and AI.

## Prerequisites

- n8n instance (cloud or self-hosted)
- AWS Lambda function deployed (`athena-query-runner`)
- OpenAI API access
- Gmail account for sending insights
- AWS Athena database with data

## Workflow Architecture

```
Form Trigger → AI SQL Generation → Lambda Athena Query → AI Insight Summary → Gmail Notification
```

## Node Configuration

### 1. Form Trigger Node

**Purpose**: Collect stakeholder data requests via web form

**Configuration**:
- Form Title: "Stakeholder Data Request"
- Form Description: "Submit your data request in natural language"

**Form Fields**:
- **Data Request** (Text, Required): Natural language description
- **Stakeholder Email** (Email, Required): Recipient for insights

**Example Requests**:
- "Show me sales by gender for this month"
- "What are our top 5 product categories by revenue this quarter?"
- "Average customer age by product category"

### 2. AI: Request → SQL Node

**Purpose**: Convert natural language to SQL using OpenAI

**Node Type**: OpenAI Chat
**Configuration**:

```
Prompt Template:
Convert this stakeholder request to a valid SQL query for Amazon Athena. Use the database schema provided and ensure the query is optimized for Parquet data.

Schema Context:
- Database: retail-sales-db
- Main table: processed_zone
- Columns: transaction_id, date, customer_id, gender, age, product_category, quantity, price_per_unit, total_amount
- Partitioned by: year, month, day

Stakeholder Request: {{$node['Stakeholder Request Form'].json['request_text']}}

Return only the SQL query without explanations.
```

**Required Credentials**: OpenAI API key

**Best Practices**:
- Include full schema context in prompt
- Specify optimization requirements
- Request clean SQL output only

### 3. Lambda: Execute Athena Query Node

**Purpose**: Execute SQL query via AWS Lambda

**Node Type**: AWS Lambda
**Configuration**:

```json
{
  "functionName": "athena-query-runner",
  "payload": {
    "sql_query": "={{$node['AI: Request → SQL'].json['choices'][0]['message']['content']}}",
    "database": "retail-sales-db",
    "output_location": "s3://retailsalespipelinebucket/athena-results/"
  }
}
```

**Required Credentials**: AWS Access Key and Secret

**Error Handling**:
- Set retry on failure
- Configure timeout (5 minutes)
- Handle query validation errors

### 4. AI: Summarize Results Node

**Purpose**: Generate business-friendly insights from query results

**Node Type**: OpenAI Chat
**Configuration**:

```
Prompt Template:
Analyze the following Athena query results and create a business-friendly summary with key insights. Format it as an executive summary suitable for email.

Original Request: {{$node['Stakeholder Request Form'].json['request_text']}}

Query Results:
{{JSON.stringify($node['Lambda: Execute Athena Query'].json['body']['results'], null, 2)}}

Provide:
1. Executive Summary
2. Key Findings
3. Actionable Insights
4. Data Quality Notes (if applicable)
```

### 5. Gmail: Send Insights Node

**Purpose**: Email insights to stakeholder

**Node Type**: Gmail
**Configuration**:

```
To: {{$node['Stakeholder Request Form'].json['stakeholder_email']}}
Subject: Data Insights: {{$node['Stakeholder Request Form'].json['request_text']}}
Format: HTML

Email Template:
<h2>Data Insights Report</h2>
<p><strong>Request:</strong> {{$node['Stakeholder Request Form'].json['request_text']}}</p>
<div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
{{$node['AI: Summarize Results'].json['choices'][0]['message']['content']}}
</div>
<hr>
<p><em>Generated automatically via Athena Insights Automation</em></p>
<p><em>Query executed on: {{new Date().toISOString()}}</em></p>
```

**Required Credentials**: Gmail OAuth2

## Credentials Setup

### OpenAI API

1. Create account at platform.openai.com
2. Generate API key
3. Add to n8n credentials as "OpenAI API"

### AWS Credentials

1. Create IAM user for n8n with Lambda invoke permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:athena-query-runner"
            ]
        }
    ]
}
```

2. Generate access key and secret for the n8n user
3. Add to n8n credentials as "AWS"

**Note**: The Lambda function itself has a separate execution role with S3, Athena, and Glue permissions. The n8n user only needs permission to invoke the Lambda function.

### Gmail OAuth2

1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth2 credentials
4. Configure in n8n with required scopes:
   - `https://www.googleapis.com/auth/gmail.send`

## Workflow Testing

### Test Scenarios

1. **Simple Query Test**
   - Request: "Total sales for this month"
   - Expected: SQL with current month filter using retail sales schema

2. **Complex Analysis Test**
   - Request: "Gender-based purchasing patterns by product category"
   - Expected: SQL with aggregations on gender and product_category

3. **Error Handling Test**
   - Request: Invalid/ambiguous request
   - Expected: Graceful error handling

### Manual Testing Steps

1. **Activate Workflow**: Enable the workflow in n8n
2. **Submit Test Request**: Use form URL to submit test data
3. **Monitor Execution**: Check workflow execution logs
4. **Verify Output**: Confirm email delivery and content
5. **Check AWS Logs**: Review Lambda CloudWatch logs

### Automated Testing

Create test webhook to simulate form submissions:

```json
{
  "request_text": "Show me sales by product category for last month",
  "stakeholder_email": "test@example.com"
}
```

## Production Deployment

### Performance Optimization

1. **Caching**: Implement query result caching for common requests
2. **Rate Limiting**: Add rate limits for AI API calls
3. **Query Optimization**: Monitor and optimize slow queries
4. **Error Retry**: Configure exponential backoff for retries

### Monitoring

1. **Workflow Metrics**: Track execution success rate
2. **Cost Monitoring**: Monitor AI API and AWS costs
3. **Query Performance**: Track Athena query execution times
4. **Email Delivery**: Monitor email delivery success

### Security

1. **Input Validation**: Sanitize user inputs
2. **SQL Injection Prevention**: Use parameterized queries
3. **Rate Limiting**: Prevent abuse
4. **Access Control**: Restrict form access if needed

## Troubleshooting

### Common Issues

1. **SQL Generation Errors**
   - Check OpenAI API quota
   - Verify prompt template accuracy
   - Review schema documentation

2. **Lambda Execution Errors**
   - Check AWS permissions
   - Verify Lambda function deployment
   - Review CloudWatch logs

3. **Email Delivery Issues**
   - Verify Gmail OAuth2 setup
   - Check email formatting
   - Review spam/delivery settings

### Debug Steps

1. **Check Node Outputs**: Review JSON output at each step
2. **Test Individual Nodes**: Execute nodes independently
3. **Review Logs**: Check n8n execution logs
4. **AWS CloudWatch**: Review Lambda and Athena logs
5. **API Limits**: Check OpenAI usage and limits

## Workflow Variations

### Advanced Features

1. **Multi-Database Support**: Query multiple databases
2. **Scheduled Reports**: Add cron trigger for regular reports
3. **Data Visualization**: Generate charts/graphs
4. **Approval Workflow**: Add human approval step
5. **Slack Integration**: Send insights to Slack channels

### Custom Extensions

1. **Query Validation**: Add SQL syntax validation
2. **Result Filtering**: Filter sensitive data from results
3. **Custom Formatting**: Create branded email templates
4. **Dashboard Integration**: Send data to BI tools