import boto3
import json
import zipfile
import os
from typing import Dict, Any

class LambdaDeploymentManager:
    """
    Manages deployment of Lambda functions
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
    
    def create_lambda_execution_role(self, role_name: str) -> str:
        """
        Creates IAM role for Lambda execution
        """
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Lambda execution role for retail analytics'
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach basic Lambda execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Attach Athena and S3 policies
            athena_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "athena:*",
                            "s3:GetObject",
                            "s3:ListBucket",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "glue:GetTable",
                            "glue:GetDatabase",
                            "glue:GetPartitions"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName='AthenaS3AccessPolicy',
                PolicyDocument=json.dumps(athena_policy)
            )
            
            return role_arn
            
        except Exception as e:
            print(f"Error creating Lambda execution role: {str(e)}")
            return ""
    
    def create_lambda_function(self, 
                              function_name: str,
                              code_file_path: str,
                              handler: str,
                              role_arn: str,
                              environment_vars: Dict[str, str] = None,
                              timeout: int = 300,
                              memory_size: int = 512) -> Dict[str, Any]:
        """
        Creates Lambda function
        """
        # Create deployment package
        zip_file_path = self._create_deployment_package(code_file_path, function_name)
        
        try:
            with open(zip_file_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            function_config = {
                'FunctionName': function_name,
                'Runtime': 'python3.9',
                'Role': role_arn,
                'Handler': handler,
                'Code': {'ZipFile': zip_content},
                'Description': f'Lambda function for {function_name}',
                'Timeout': timeout,
                'MemorySize': memory_size,
                'Publish': True
            }
            
            if environment_vars:
                function_config['Environment'] = {'Variables': environment_vars}
            
            response = self.lambda_client.create_function(**function_config)
            print(f"Lambda function '{function_name}' created successfully")
            
            # Clean up zip file
            os.remove(zip_file_path)
            
            return response
            
        except Exception as e:
            print(f"Error creating Lambda function: {str(e)}")
            return {}
    
    def _create_deployment_package(self, code_file_path: str, function_name: str) -> str:
        """
        Creates deployment package for Lambda function
        """
        zip_file_path = f"/tmp/{function_name}.zip"
        
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main code file
            zip_file.write(code_file_path, os.path.basename(code_file_path))
            
            # Add requirements if they exist
            requirements_path = os.path.join(os.path.dirname(code_file_path), 'requirements.txt')
            if os.path.exists(requirements_path):
                zip_file.write(requirements_path, 'requirements.txt')
        
        return zip_file_path
    
    def update_function_code(self, function_name: str, code_file_path: str) -> Dict[str, Any]:
        """
        Updates Lambda function code
        """
        zip_file_path = self._create_deployment_package(code_file_path, function_name)
        
        try:
            with open(zip_file_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content,
                Publish=True
            )
            
            print(f"Lambda function '{function_name}' updated successfully")
            
            # Clean up zip file
            os.remove(zip_file_path)
            
            return response
            
        except Exception as e:
            print(f"Error updating Lambda function: {str(e)}")
            return {}

def deploy_lambda_functions():
    """
    Deploys all Lambda functions for the retail analytics pipeline
    """
    deployment_manager = LambdaDeploymentManager()
    
    # Create execution role
    role_arn = deployment_manager.create_lambda_execution_role('RetailAnalyticsLambdaRole')
    
    if not role_arn:
        print("Failed to create Lambda execution role")
        return
    
    # Wait for role to be available
    import time
    time.sleep(10)
    
    # Deploy Athena Query Executor
    athena_executor_response = deployment_manager.create_lambda_function(
        function_name='retail-athena-query-executor',
        code_file_path='athena_query_executor.py',
        handler='athena_query_executor.lambda_handler',
        role_arn=role_arn,
        environment_vars={
            'ATHENA_DATABASE': 'retail_analytics_db',
            'ATHENA_OUTPUT_LOCATION': 's3://your-athena-results-bucket/query-results/'
        },
        timeout=900,  # 15 minutes
        memory_size=1024
    )
    
    # Deploy AI Query Processor
    ai_processor_response = deployment_manager.create_lambda_function(
        function_name='retail-ai-query-processor',
        code_file_path='ai_query_processor.py',
        handler='ai_query_processor.lambda_handler',
        role_arn=role_arn,
        environment_vars={
            'OPENAI_API_KEY': 'your-openai-api-key-here'  # Set this in AWS Console
        },
        timeout=300,
        memory_size=512
    )
    
    return {
        'athena_executor': athena_executor_response,
        'ai_processor': ai_processor_response
    }

if __name__ == "__main__":
    deployment_results = deploy_lambda_functions()
    print("Deployment completed:", json.dumps(deployment_results, indent=2, default=str))