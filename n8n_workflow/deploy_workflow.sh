#!/bin/bash

# n8n Workflow Deployment Script
# This script helps deploy the retail analytics workflow to n8n

echo "🚀 Deploying AI-Enhanced Retail Analytics Workflow to n8n"

# Configuration
N8N_HOST="${N8N_HOST:-http://localhost:5678}"
WORKFLOW_FILE="retail_analytics_workflow.json"

# Check if n8n is accessible
echo "📡 Checking n8n connectivity..."
if ! curl -f -s "$N8N_HOST/healthz" > /dev/null; then
    echo "❌ Error: n8n is not accessible at $N8N_HOST"
    echo "Please ensure n8n is running and accessible."
    exit 1
fi

echo "✅ n8n is accessible"

# Import workflow
echo "📦 Importing workflow..."
if [ -f "$WORKFLOW_FILE" ]; then
    # Import using n8n CLI if available
    if command -v n8n &> /dev/null; then
        echo "Using n8n CLI to import workflow..."
        n8n import:workflow --input="$WORKFLOW_FILE"
    else
        echo "⚠️  n8n CLI not found. Please manually import the workflow:"
        echo "   1. Open n8n at $N8N_HOST"
        echo "   2. Go to Workflows > Import from File"
        echo "   3. Select the file: $WORKFLOW_FILE"
        echo "   4. Configure the webhook URL and credentials"
    fi
else
    echo "❌ Error: Workflow file $WORKFLOW_FILE not found"
    exit 1
fi

echo "📋 Post-deployment configuration required:"
echo "   1. Configure AWS credentials in n8n"
echo "   2. Set up email sending credentials"
echo "   3. Configure OpenAI API key (if using OpenAI)"
echo "   4. Test the webhook endpoint"
echo "   5. Set up monitoring and alerting"

echo ""
echo "🔧 Environment Variables to Set in n8n:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION (default: us-east-1)"
echo "   - OPENAI_API_KEY (optional, for AI features)"
echo "   - EMAIL_HOST"
echo "   - EMAIL_PORT"
echo "   - EMAIL_USER"
echo "   - EMAIL_PASSWORD"

echo ""
echo "📝 Test the workflow with:"
echo "curl -X POST $N8N_HOST/webhook/retail-analytics-webhook \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"user_request\": \"Show me top 10 products by revenue\","
echo "    \"query_type\": \"custom\","
echo "    \"recipient_email\": \"your-email@example.com\""
echo "  }'"

echo ""
echo "✅ Workflow deployment completed!"