import boto3
import json
from typing import Dict, Any

class GlueJobManager:
    """
    Manages AWS Glue ETL jobs
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.glue_client = boto3.client('glue', region_name=region)
        
    def create_etl_job(self, 
                       job_name: str,
                       iam_role_arn: str,
                       script_location: str,
                       source_database: str,
                       source_table: str,
                       target_s3_path: str,
                       max_capacity: int = 10) -> Dict[str, Any]:
        """
        Creates a Glue ETL job for retail data processing
        """
        job_config = {
            'Name': job_name,
            'Description': 'ETL job for cleaning and processing retail sales data',
            'Role': iam_role_arn,
            'Command': {
                'Name': 'glueetl',
                'ScriptLocation': script_location,
                'PythonVersion': '3'
            },
            'DefaultArguments': {
                '--job-language': 'python',
                '--job-bookmark-option': 'job-bookmark-enable',
                '--enable-metrics': '',
                '--enable-continuous-cloudwatch-log': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': 's3://aws-glue-assets-bucket/sparkHistoryLogs/',
                '--SOURCE_DATABASE': source_database,
                '--SOURCE_TABLE': source_table,
                '--TARGET_S3_PATH': target_s3_path,
                '--TempDir': 's3://aws-glue-assets-bucket/temporary/',
                '--additional-python-modules': 'boto3,pandas'
            },
            'MaxCapacity': max_capacity,
            'Timeout': 2880,  # 48 hours
            'MaxRetries': 1,
            'GlueVersion': '3.0'
        }
        
        try:
            response = self.glue_client.create_job(**job_config)
            print(f"Glue ETL job '{job_name}' created successfully")
            return response
        except Exception as e:
            print(f"Error creating Glue ETL job: {str(e)}")
            return {}
    
    def start_job_run(self, job_name: str, arguments: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Starts a Glue job run
        """
        job_run_config = {'JobName': job_name}
        
        if arguments:
            job_run_config['Arguments'] = arguments
            
        try:
            response = self.glue_client.start_job_run(**job_run_config)
            print(f"Job run started for '{job_name}' with run ID: {response.get('JobRunId')}")
            return response
        except Exception as e:
            print(f"Error starting job run: {str(e)}")
            return {}
    
    def get_job_run_status(self, job_name: str, job_run_id: str) -> Dict[str, Any]:
        """
        Gets the status of a job run
        """
        try:
            response = self.glue_client.get_job_run(JobName=job_name, RunId=job_run_id)
            return response.get('JobRun', {})
        except Exception as e:
            print(f"Error getting job run status: {str(e)}")
            return {}

if __name__ == "__main__":
    # Example usage
    job_manager = GlueJobManager()
    
    # Configuration parameters
    JOB_NAME = "retail-data-etl-job"
    IAM_ROLE_ARN = "arn:aws:iam::ACCOUNT_ID:role/GlueServiceRole"
    SCRIPT_LOCATION = "s3://your-bucket-name/scripts/retail_data_etl.py"
    SOURCE_DATABASE = "retail_analytics_db"
    SOURCE_TABLE = "raw_sales_data"
    TARGET_S3_PATH = "s3://your-bucket-name/processed-data/"
    
    # Create ETL job
    job_response = job_manager.create_etl_job(
        job_name=JOB_NAME,
        iam_role_arn=IAM_ROLE_ARN,
        script_location=SCRIPT_LOCATION,
        source_database=SOURCE_DATABASE,
        source_table=SOURCE_TABLE,
        target_s3_path=TARGET_S3_PATH
    )
    
    # Start job run
    if job_response:
        run_response = job_manager.start_job_run(JOB_NAME)
        print(f"Job run response: {run_response}")