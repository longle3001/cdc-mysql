import os
import findspark
findspark.init()

from pyspark.sql import SparkSession

# # Set AWS credentials as environment variables
# os.environ["AWS_ACCESS_KEY_ID"] = "test"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

# Create SparkSession
spark = SparkSession.builder \
    .appName("S3App") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.2,com.amazonaws:aws-java-sdk-bundle:1.11.375") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.access.key", "a") \
    .config("spark.hadoop.fs.s3a.secret.key", "a") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

# Read a JSON file from S3 (LocalStack)
try:
    df = spark.read.json("s3a://mybucket/stripe/2024/07/13/type=json/users_235554.json")
    df.show()
    df.printSchema()
except Exception as e:
    print(f"-- lỗi: Error reading data: {e}")