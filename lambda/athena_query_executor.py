import json
import boto3
import time
import uuid
from typing import Dict, List, Any
from datetime import datetime, timedelta

class AthenaQueryExecutor:
    """
    Executes Athena queries and manages query results
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.athena_client = boto3.client('athena', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
    def execute_query(self, 
                     query: str, 
                     database: str, 
                     output_location: str,
                     work_group: str = 'primary') -> Dict[str, Any]:
        """
        Executes an Athena query and returns results
        """
        query_execution_id = str(uuid.uuid4())
        
        try:
            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={'OutputLocation': output_location},
                WorkGroup=work_group
            )
            
            execution_id = response['QueryExecutionId']
            
            # Wait for query to complete
            status = self._wait_for_query_completion(execution_id)
            
            if status == 'SUCCEEDED':
                # Get query results
                results = self._get_query_results(execution_id)
                return {
                    'execution_id': execution_id,
                    'status': 'SUCCEEDED',
                    'results': results
                }
            else:
                return {
                    'execution_id': execution_id,
                    'status': status,
                    'error': self._get_query_error(execution_id)
                }
                
        except Exception as e:
            return {
                'execution_id': query_execution_id,
                'status': 'FAILED',
                'error': str(e)
            }
    
    def _wait_for_query_completion(self, execution_id: str, max_wait_time: int = 300) -> str:
        """
        Waits for query to complete with timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = self.athena_client.get_query_execution(QueryExecutionId=execution_id)
            status = response['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                return status
                
            time.sleep(5)
        
        return 'TIMEOUT'
    
    def _get_query_results(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves query results
        """
        results = []
        next_token = None
        
        while True:
            params = {'QueryExecutionId': execution_id}
            if next_token:
                params['NextToken'] = next_token
                
            response = self.athena_client.get_query_results(**params)
            
            # Extract column names from first row
            if not results and response['ResultSet']['Rows']:
                columns = [col['VarCharValue'] for col in response['ResultSet']['Rows'][0]['Data']]
                
                # Process data rows (skip header)
                for row in response['ResultSet']['Rows'][1:]:
                    row_data = {}
                    for i, cell in enumerate(row['Data']):
                        row_data[columns[i]] = cell.get('VarCharValue', '')
                    results.append(row_data)
            elif results:  # Subsequent pages
                for row in response['ResultSet']['Rows']:
                    row_data = {}
                    for i, cell in enumerate(row['Data']):
                        row_data[columns[i]] = cell.get('VarCharValue', '')
                    results.append(row_data)
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return results
    
    def _get_query_error(self, execution_id: str) -> str:
        """
        Gets error message for failed query
        """
        try:
            response = self.athena_client.get_query_execution(QueryExecutionId=execution_id)
            return response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        except:
            return 'Unable to retrieve error details'

def lambda_handler(event, context):
    """
    AWS Lambda handler for Athena query execution
    """
    try:
        # Parse input parameters
        query_type = event.get('query_type')
        custom_query = event.get('custom_query')
        date_range = event.get('date_range', {})
        filters = event.get('filters', {})
        
        # Configuration
        DATABASE = 'retail_analytics_db'
        OUTPUT_LOCATION = 's3://your-athena-results-bucket/query-results/'
        
        # Initialize Athena executor
        executor = AthenaQueryExecutor()
        
        # Generate query based on type
        if query_type == 'daily_sales_summary':
            query = generate_daily_sales_query(date_range, filters)
        elif query_type == 'top_products':
            query = generate_top_products_query(date_range, filters)
        elif query_type == 'customer_analytics':
            query = generate_customer_analytics_query(date_range, filters)
        elif query_type == 'revenue_trends':
            query = generate_revenue_trends_query(date_range, filters)
        elif query_type == 'custom':
            query = custom_query
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid query type'})
            }
        
        # Execute query
        result = executor.execute_query(query, DATABASE, OUTPUT_LOCATION)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'execution_id': result['execution_id'],
                'status': result['status'],
                'results': result.get('results', []),
                'error': result.get('error'),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def generate_daily_sales_query(date_range: Dict, filters: Dict) -> str:
    """
    Generates daily sales summary query
    """
    base_query = """
    SELECT 
        DATE(transaction_timestamp) as sale_date,
        category,
        COUNT(*) as transaction_count,
        SUM(total_amount) as total_revenue,
        AVG(total_amount) as avg_transaction_value,
        SUM(quantity) as total_items_sold
    FROM cleaned_sales_data
    WHERE 1=1
    """
    
    # Add date filter
    if date_range.get('start_date'):
        base_query += f" AND DATE(transaction_timestamp) >= '{date_range['start_date']}'"
    if date_range.get('end_date'):
        base_query += f" AND DATE(transaction_timestamp) <= '{date_range['end_date']}'"
    
    # Add category filter
    if filters.get('category'):
        base_query += f" AND category = '{filters['category']}'"
    
    # Add store filter
    if filters.get('store_id'):
        base_query += f" AND store_id = '{filters['store_id']}'"
    
    base_query += " GROUP BY DATE(transaction_timestamp), category ORDER BY sale_date DESC, total_revenue DESC"
    
    return base_query

def generate_top_products_query(date_range: Dict, filters: Dict) -> str:
    """
    Generates top products query
    """
    limit = filters.get('limit', 10)
    
    base_query = f"""
    SELECT 
        product_id,
        product_name,
        category,
        COUNT(*) as transaction_count,
        SUM(quantity) as total_quantity_sold,
        SUM(total_amount) as total_revenue,
        AVG(unit_price) as avg_unit_price
    FROM cleaned_sales_data
    WHERE 1=1
    """
    
    # Add date filter
    if date_range.get('start_date'):
        base_query += f" AND DATE(transaction_timestamp) >= '{date_range['start_date']}'"
    if date_range.get('end_date'):
        base_query += f" AND DATE(transaction_timestamp) <= '{date_range['end_date']}'"
    
    # Add category filter
    if filters.get('category'):
        base_query += f" AND category = '{filters['category']}'"
    
    base_query += f" GROUP BY product_id, product_name, category ORDER BY total_revenue DESC LIMIT {limit}"
    
    return base_query

def generate_customer_analytics_query(date_range: Dict, filters: Dict) -> str:
    """
    Generates customer analytics query
    """
    base_query = """
    SELECT 
        customer_id,
        COUNT(*) as transaction_count,
        SUM(total_amount) as lifetime_value,
        AVG(total_amount) as avg_order_value,
        MAX(DATE(transaction_timestamp)) as last_purchase_date,
        COUNT(DISTINCT product_id) as unique_products_purchased
    FROM cleaned_sales_data
    WHERE 1=1
    """
    
    # Add date filter
    if date_range.get('start_date'):
        base_query += f" AND DATE(transaction_timestamp) >= '{date_range['start_date']}'"
    if date_range.get('end_date'):
        base_query += f" AND DATE(transaction_timestamp) <= '{date_range['end_date']}'"
    
    base_query += " GROUP BY customer_id ORDER BY lifetime_value DESC LIMIT 100"
    
    return base_query

def generate_revenue_trends_query(date_range: Dict, filters: Dict) -> str:
    """
    Generates revenue trends query
    """
    base_query = """
    SELECT 
        year,
        month,
        category,
        SUM(total_amount) as monthly_revenue,
        COUNT(*) as transaction_count,
        AVG(total_amount) as avg_transaction_value
    FROM cleaned_sales_data
    WHERE 1=1
    """
    
    # Add date filter
    if date_range.get('start_date'):
        base_query += f" AND DATE(transaction_timestamp) >= '{date_range['start_date']}'"
    if date_range.get('end_date'):
        base_query += f" AND DATE(transaction_timestamp) <= '{date_range['end_date']}'"
    
    # Add category filter
    if filters.get('category'):
        base_query += f" AND category = '{filters['category']}'"
    
    base_query += " GROUP BY year, month, category ORDER BY year DESC, month DESC, monthly_revenue DESC"
    
    return base_query