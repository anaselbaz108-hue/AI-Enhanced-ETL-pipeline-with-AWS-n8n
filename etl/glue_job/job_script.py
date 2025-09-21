from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql.functions import (
    col, to_date, year, month, dayofmonth, when, trim
)

# Initialize GlueContext and SparkSession
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Read from Glue Data Catalog (update these names)
database_name = "retail-sales-db"
table_name = "raw_zone"

# Read as DynamicFrame from Data Catalog
dyf = glueContext.create_dynamic_frame.from_catalog(
    database=database_name,
    table_name=table_name
)

# Convert to Spark DataFrame
df = dyf.toDF()

# Clean and transform
df = df.select([trim(col(c)).alias(c.strip().lower().replace(" ", "_")) for c in df.columns])

# Convert date column (date only: yyyy-MM-dd)
df = df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))

# Drop rows with nulls in key columns
df = df.na.drop(subset=["transaction_id", "date", "customer_id", "product_category", "total_amount"])

# Fix negative / zero values
df = df.withColumn("quantity", when(col("quantity") <= 0, None).otherwise(col("quantity")))
df = df.withColumn("price_per_unit", when(col("price_per_unit") <= 0, None).otherwise(col("price_per_unit")))
df = df.withColumn("total_amount", when(col("total_amount") <= 0, None).otherwise(col("total_amount")))

# Remove duplicates
df = df.dropDuplicates(["transaction_id"])

# Add partitioning columns
df = df.withColumn("year", year(col("date"))) \
       .withColumn("month", month(col("date"))) \
       .withColumn("day", dayofmonth(col("date")))

# Debug - show row count and partition columns before writing
print(f"Row count before write: {df.count()}")
df.select("year", "month", "day").show(5)
df.printSchema()

# Write to Parquet, partitioned by year/month/day (update S3 path)
output_path = "s3://retailsalespipelinebucket/processed-zone/"
df.write.mode("append").partitionBy("year", "month", "day").parquet(output_path)

print("✅ ETL Job Completed Successfully")
