import json
import boto3
import openai
import os
from typing import Dict, List, Any
from datetime import datetime

class AIQueryProcessor:
    """
    AI-powered query generation and result summarization
    """
    
    def __init__(self):
        # Initialize OpenAI client (could be replaced with AWS Bedrock)
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize AWS Bedrock client as alternative
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
    def natural_language_to_sql(self, user_request: str, schema_info: Dict) -> str:
        """
        Converts natural language request to SQL query
        """
        system_prompt = f"""
        You are an expert SQL query generator for a retail analytics database.
        
        Database Schema:
        Table: cleaned_sales_data
        Columns: {', '.join(schema_info.get('columns', []))}
        Partitions: year, month, category
        
        Convert the following natural language request into a valid SQL query for Amazon Athena.
        Use only the columns and table mentioned above.
        Always include appropriate WHERE clauses and LIMIT results to reasonable numbers.
        
        User Request: {user_request}
        
        Return only the SQL query without any explanations.
        """
        
        try:
            if self.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_request}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            else:
                # Use AWS Bedrock as fallback
                return self._generate_sql_with_bedrock(user_request, schema_info)
                
        except Exception as e:
            # Fallback to template-based query generation
            return self._template_based_query_generation(user_request, schema_info)
    
    def _generate_sql_with_bedrock(self, user_request: str, schema_info: Dict) -> str:
        """
        Generate SQL using AWS Bedrock
        """
        prompt = f"""
        Generate a SQL query for the following request based on the retail sales database:
        
        Request: {user_request}
        
        Available columns: {', '.join(schema_info.get('columns', []))}
        Table: cleaned_sales_data
        
        SQL Query:
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            return self._template_based_query_generation(user_request, schema_info)
    
    def _template_based_query_generation(self, user_request: str, schema_info: Dict) -> str:
        """
        Fallback template-based query generation
        """
        user_request_lower = user_request.lower()
        
        if 'sales' in user_request_lower and 'by category' in user_request_lower:
            return """
            SELECT category, 
                   SUM(total_amount) as total_sales,
                   COUNT(*) as transaction_count
            FROM cleaned_sales_data 
            GROUP BY category 
            ORDER BY total_sales DESC
            LIMIT 10
            """
        elif 'top products' in user_request_lower:
            return """
            SELECT product_name, 
                   SUM(total_amount) as total_revenue,
                   SUM(quantity) as total_sold
            FROM cleaned_sales_data 
            GROUP BY product_name 
            ORDER BY total_revenue DESC
            LIMIT 10
            """
        elif 'monthly revenue' in user_request_lower:
            return """
            SELECT year, month, 
                   SUM(total_amount) as monthly_revenue
            FROM cleaned_sales_data 
            GROUP BY year, month 
            ORDER BY year DESC, month DESC
            LIMIT 12
            """
        else:
            return """
            SELECT COUNT(*) as total_transactions,
                   SUM(total_amount) as total_revenue,
                   AVG(total_amount) as avg_transaction_value
            FROM cleaned_sales_data
            """
    
    def summarize_query_results(self, query_results: List[Dict], user_request: str) -> str:
        """
        Generates AI-powered summary of query results
        """
        if not query_results:
            return "No data found for the specified criteria."
        
        # Prepare data summary
        data_summary = self._prepare_data_summary(query_results)
        
        system_prompt = f"""
        You are a retail analytics expert. Summarize the following query results in a clear, 
        business-friendly format. Focus on key insights, trends, and actionable recommendations.
        
        Original Request: {user_request}
        
        Data Summary:
        - Number of records: {len(query_results)}
        - Sample data: {json.dumps(query_results[:3], indent=2)}
        
        Provide a concise summary with:
        1. Key findings
        2. Notable trends or patterns
        3. Business recommendations (if applicable)
        
        Keep the summary under 200 words and make it actionable for business stakeholders.
        """
        
        try:
            if self.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": data_summary}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            else:
                return self._generate_summary_with_bedrock(data_summary, user_request)
                
        except Exception as e:
            return self._template_based_summary(query_results, user_request)
    
    def _generate_summary_with_bedrock(self, data_summary: str, user_request: str) -> str:
        """
        Generate summary using AWS Bedrock
        """
        prompt = f"""
        Analyze the following retail data results and provide a business summary:
        
        Original Request: {user_request}
        Data: {data_summary}
        
        Provide key insights and recommendations in a concise format.
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            return self._template_based_summary(query_results, user_request)
    
    def _prepare_data_summary(self, query_results: List[Dict]) -> str:
        """
        Prepares a structured summary of the data for AI processing
        """
        if not query_results:
            return "No data available"
        
        # Get column names and sample values
        columns = list(query_results[0].keys())
        sample_data = query_results[:5]
        
        summary = f"""
        Data Overview:
        - Total records: {len(query_results)}
        - Columns: {', '.join(columns)}
        - Sample records: {json.dumps(sample_data, indent=2)}
        """
        
        return summary
    
    def _template_based_summary(self, query_results: List[Dict], user_request: str) -> str:
        """
        Fallback template-based summary generation
        """
        record_count = len(query_results)
        
        if record_count == 0:
            return "No data found matching your criteria."
        
        # Basic summary based on common patterns
        if 'category' in str(query_results[0]).lower():
            return f"""
            Analysis Summary:
            - Found {record_count} categories in the results
            - Data includes sales performance across different product categories
            - Consider focusing on top-performing categories for business growth
            """
        elif 'product' in str(query_results[0]).lower():
            return f"""
            Product Analysis Summary:
            - Analyzed {record_count} products
            - Results show product performance metrics
            - Recommend focusing on high-revenue products for inventory optimization
            """
        else:
            return f"""
            Data Analysis Summary:
            - Retrieved {record_count} records
            - Analysis completed successfully
            - Review the detailed results for specific insights
            """

def lambda_handler(event, context):
    """
    AWS Lambda handler for AI query processing
    """
    try:
        operation = event.get('operation')
        
        ai_processor = AIQueryProcessor()
        
        if operation == 'generate_sql':
            user_request = event.get('user_request')
            schema_info = event.get('schema_info', {
                'columns': [
                    'transaction_id', 'customer_id', 'product_id', 'product_name',
                    'category', 'quantity', 'unit_price', 'total_amount',
                    'transaction_timestamp', 'store_id', 'sales_rep_id',
                    'payment_method', 'revenue_category', 'data_quality_score'
                ]
            })
            
            sql_query = ai_processor.natural_language_to_sql(user_request, schema_info)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'sql_query': sql_query,
                    'user_request': user_request,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
        elif operation == 'summarize_results':
            query_results = event.get('query_results', [])
            user_request = event.get('user_request', '')
            
            summary = ai_processor.summarize_query_results(query_results, user_request)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'summary': summary,
                    'user_request': user_request,
                    'record_count': len(query_results),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }