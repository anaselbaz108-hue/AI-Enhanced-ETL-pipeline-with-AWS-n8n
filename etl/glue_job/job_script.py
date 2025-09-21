"""
AWS Glue ETL Job Script for Athena Insights Automation
Reads raw data from S3, cleans and transforms it, partitions data, 
converts to Parquet format, and writes to S3 for Athena queries.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'source_bucket',
    'target_bucket',
    'database_name'
])

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read raw data from Glue catalog
source_df = glueContext.create_dynamic_frame.from_catalog(
    database=args['database_name'],
    table_name="raw_data_table"
)

# Convert to Spark DataFrame for transformations
spark_df = source_df.toDF()

# Data cleaning and transformation
cleaned_df = spark_df \
    .dropDuplicates() \
    .filter(F.col("id").isNotNull()) \
    .withColumn("processed_date", F.current_date()) \
    .withColumn("year", F.year(F.col("date_column"))) \
    .withColumn("month", F.month(F.col("date_column")))

# Convert back to DynamicFrame
cleaned_dynamic_frame = DynamicFrame.fromDF(cleaned_df, glueContext, "cleaned_data")

# Write to S3 in Parquet format with partitioning
glueContext.write_dynamic_frame.from_options(
    frame=cleaned_dynamic_frame,
    connection_type="s3",
    connection_options={
        "path": f"s3://{args['target_bucket']}/parquet-data/",
        "partitionKeys": ["year", "month"]
    },
    format="parquet"
)

job.commit()