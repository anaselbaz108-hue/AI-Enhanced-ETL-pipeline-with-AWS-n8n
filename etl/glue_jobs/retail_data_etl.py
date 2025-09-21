import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import boto3
from datetime import datetime

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_DATABASE', 'SOURCE_TABLE', 'TARGET_S3_PATH'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

def data_quality_check(df: DataFrame) -> DataFrame:
    """
    Performs data quality checks and adds quality scores
    """
    # Add data quality score based on missing values and data consistency
    df_with_quality = df.withColumn(
        "missing_fields_count",
        when(col("transaction_id").isNull(), 1).otherwise(0) +
        when(col("customer_id").isNull(), 1).otherwise(0) +
        when(col("product_id").isNull(), 1).otherwise(0) +
        when(col("quantity").isNull(), 1).otherwise(0) +
        when(col("unit_price").isNull(), 1).otherwise(0) +
        when(col("transaction_date").isNull(), 1).otherwise(0)
    ).withColumn(
        "data_quality_score",
        1.0 - (col("missing_fields_count") / 6.0)
    ).drop("missing_fields_count")
    
    return df_with_quality

def clean_and_standardize(df: DataFrame) -> DataFrame:
    """
    Cleans and standardizes the data
    """
    # Clean product names
    df_cleaned = df.withColumn(
        "product_name",
        trim(regexp_replace(col("product_name"), "[^a-zA-Z0-9 ]", ""))
    )
    
    # Standardize categories
    df_cleaned = df_cleaned.withColumn(
        "category",
        when(col("category").isin(["Electronics", "ELECTRONICS", "electronics"]), "Electronics")
        .when(col("category").isin(["Clothing", "CLOTHING", "clothing", "Apparel"]), "Clothing")
        .when(col("category").isin(["Home", "HOME", "home", "Home & Garden"]), "Home")
        .when(col("category").isin(["Sports", "SPORTS", "sports", "Sports & Outdoors"]), "Sports")
        .otherwise("Other")
    )
    
    # Standardize payment methods
    df_cleaned = df_cleaned.withColumn(
        "payment_method",
        when(col("payment_method").isin(["Credit Card", "CREDIT_CARD", "credit card"]), "Credit Card")
        .when(col("payment_method").isin(["Debit Card", "DEBIT_CARD", "debit card"]), "Debit Card")
        .when(col("payment_method").isin(["Cash", "CASH", "cash"]), "Cash")
        .when(col("payment_method").isin(["PayPal", "PAYPAL", "paypal"]), "PayPal")
        .otherwise("Other")
    )
    
    # Add revenue category
    df_cleaned = df_cleaned.withColumn(
        "revenue_category",
        when(col("total_amount") >= 500, "High")
        .when(col("total_amount") >= 100, "Medium")
        .otherwise("Low")
    )
    
    # Standardize timestamp
    df_cleaned = df_cleaned.withColumn(
        "transaction_timestamp",
        to_timestamp(col("transaction_date"), "yyyy-MM-dd HH:mm:ss")
    )
    
    # Add partition columns
    df_cleaned = df_cleaned.withColumn("year", year(col("transaction_timestamp"))) \
                          .withColumn("month", format_string("%02d", month(col("transaction_timestamp"))))
    
    return df_cleaned

def filter_valid_data(df: DataFrame) -> DataFrame:
    """
    Filters out invalid data records
    """
    # Filter out records with null essential fields
    df_filtered = df.filter(
        col("transaction_id").isNotNull() &
        col("customer_id").isNotNull() &
        col("product_id").isNotNull() &
        col("quantity").isNotNull() &
        col("unit_price").isNotNull() &
        col("total_amount").isNotNull() &
        col("transaction_timestamp").isNotNull()
    )
    
    # Filter out records with invalid quantities and prices
    df_filtered = df_filtered.filter(
        (col("quantity") > 0) &
        (col("unit_price") > 0) &
        (col("total_amount") > 0)
    )
    
    # Filter out future dates
    current_date = datetime.now()
    df_filtered = df_filtered.filter(
        col("transaction_timestamp") <= current_date
    )
    
    return df_filtered

def main():
    """
    Main ETL processing function
    """
    # Read data from Glue catalog
    datasource = glueContext.create_dynamic_frame.from_catalog(
        database=args['SOURCE_DATABASE'],
        table_name=args['SOURCE_TABLE'],
        transformation_ctx="datasource"
    )
    
    # Convert to DataFrame for processing
    df = datasource.toDF()
    
    print(f"Initial record count: {df.count()}")
    
    # Apply data quality checks
    df_with_quality = data_quality_check(df)
    
    # Clean and standardize data
    df_cleaned = clean_and_standardize(df_with_quality)
    
    # Filter valid data
    df_filtered = filter_valid_data(df_cleaned)
    
    print(f"Final record count after cleaning: {df_filtered.count()}")
    
    # Select final columns for output
    final_columns = [
        "transaction_id", "customer_id", "product_id", "product_name", 
        "category", "quantity", "unit_price", "total_amount", 
        "transaction_timestamp", "store_id", "sales_rep_id", 
        "payment_method", "revenue_category", "data_quality_score",
        "year", "month"
    ]
    
    df_final = df_filtered.select(*final_columns)
    
    # Convert back to DynamicFrame
    dynamic_frame_final = DynamicFrame.fromDF(df_final, glueContext, "dynamic_frame_final")
    
    # Write to S3 in Parquet format with partitioning
    glueContext.write_dynamic_frame.from_options(
        frame=dynamic_frame_final,
        connection_type="s3",
        connection_options={
            "path": args['TARGET_S3_PATH'],
            "partitionKeys": ["year", "month", "category"]
        },
        format="parquet",
        transformation_ctx="datasink"
    )
    
    print("ETL job completed successfully")

if __name__ == "__main__":
    main()
    job.commit()