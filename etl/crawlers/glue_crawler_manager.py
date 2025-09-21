import boto3
import json
import os
from typing import Dict, Any

class GlueCrawlerManager:
    """
    Manages AWS Glue crawlers for raw and processed data
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.glue_client = boto3.client('glue', region_name=region)
        
    def create_raw_data_crawler(self, 
                               crawler_name: str,
                               database_name: str,
                               s3_target_path: str,
                               iam_role_arn: str,
                               table_prefix: str = 'raw_') -> Dict[str, Any]:
        """
        Creates a crawler for raw data sources
        """
        crawler_config = {
            'Name': crawler_name,
            'Role': iam_role_arn,
            'DatabaseName': database_name,
            'Description': 'Crawler for raw retail sales data',
            'Targets': {
                'S3Targets': [
                    {
                        'Path': s3_target_path,
                        'Exclusions': []
                    }
                ]
            },
            'TablePrefix': table_prefix,
            'SchemaChangePolicy': {
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
            },
            'RecrawlPolicy': {
                'RecrawlBehavior': 'CRAWL_EVERYTHING'
            },
            'LineageConfiguration': {
                'CrawlerLineageSettings': 'ENABLE'
            },
            'Configuration': json.dumps({
                'Version': 1.0,
                'CrawlerOutput': {
                    'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'},
                    'Tables': {'AddOrUpdateBehavior': 'MergeNewColumns'}
                }
            })
        }
        
        try:
            response = self.glue_client.create_crawler(**crawler_config)
            print(f"Raw data crawler '{crawler_name}' created successfully")
            return response
        except Exception as e:
            print(f"Error creating raw data crawler: {str(e)}")
            return {}
    
    def create_parquet_data_crawler(self, 
                                   crawler_name: str,
                                   database_name: str,
                                   s3_target_path: str,
                                   iam_role_arn: str,
                                   table_prefix: str = 'processed_') -> Dict[str, Any]:
        """
        Creates a crawler for processed parquet data
        """
        crawler_config = {
            'Name': crawler_name,
            'Role': iam_role_arn,
            'DatabaseName': database_name,
            'Description': 'Crawler for processed parquet retail sales data',
            'Targets': {
                'S3Targets': [
                    {
                        'Path': s3_target_path,
                        'Exclusions': []
                    }
                ]
            },
            'TablePrefix': table_prefix,
            'SchemaChangePolicy': {
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
            },
            'RecrawlPolicy': {
                'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'
            },
            'LineageConfiguration': {
                'CrawlerLineageSettings': 'ENABLE'
            },
            'Configuration': json.dumps({
                'Version': 1.0,
                'Grouping': {
                    'TableGroupingPolicy': 'CombineCompatibleSchemas'
                },
                'CrawlerOutput': {
                    'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'},
                    'Tables': {'AddOrUpdateBehavior': 'MergeNewColumns'}
                }
            })
        }
        
        try:
            response = self.glue_client.create_crawler(**crawler_config)
            print(f"Parquet data crawler '{crawler_name}' created successfully")
            return response
        except Exception as e:
            print(f"Error creating parquet data crawler: {str(e)}")
            return {}
    
    def start_crawler(self, crawler_name: str) -> Dict[str, Any]:
        """
        Starts a Glue crawler
        """
        try:
            response = self.glue_client.start_crawler(Name=crawler_name)
            print(f"Crawler '{crawler_name}' started successfully")
            return response
        except Exception as e:
            print(f"Error starting crawler '{crawler_name}': {str(e)}")
            return {}
    
    def get_crawler_status(self, crawler_name: str) -> Dict[str, Any]:
        """
        Gets the status of a Glue crawler
        """
        try:
            response = self.glue_client.get_crawler(Name=crawler_name)
            return response.get('Crawler', {})
        except Exception as e:
            print(f"Error getting crawler status: {str(e)}")
            return {}

if __name__ == "__main__":
    # Example usage
    crawler_manager = GlueCrawlerManager()
    
    # Configuration parameters
    DATABASE_NAME = "retail_analytics_db"
    IAM_ROLE_ARN = "arn:aws:iam::ACCOUNT_ID:role/GlueServiceRole"
    RAW_DATA_S3_PATH = "s3://your-bucket-name/raw-data/"
    PROCESSED_DATA_S3_PATH = "s3://your-bucket-name/processed-data/"
    
    # Create crawlers
    raw_crawler_response = crawler_manager.create_raw_data_crawler(
        crawler_name="retail-raw-data-crawler",
        database_name=DATABASE_NAME,
        s3_target_path=RAW_DATA_S3_PATH,
        iam_role_arn=IAM_ROLE_ARN
    )
    
    parquet_crawler_response = crawler_manager.create_parquet_data_crawler(
        crawler_name="retail-parquet-data-crawler",
        database_name=DATABASE_NAME,
        s3_target_path=PROCESSED_DATA_S3_PATH,
        iam_role_arn=IAM_ROLE_ARN
    )