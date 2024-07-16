import os
# # Set environment variables
os.environ["SPARK_HOME"] = "/opt/homebrew/Cellar/apache-spark/3.5.1/libexec"
os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"

# Verify environment variables
print("SPARK_HOME:", os.environ["SPARK_HOME"])
print("AWS_ACCESS_KEY_ID:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("AWS_SECRET_ACCESS_KEY:", os.environ.get("AWS_SECRET_ACCESS_KEY"))


import hashlib

def pseudonymize_doc_string(doc):
    '''
    Pseudonmyisation is a deterministic type of PII-obscuring
    Its role is to allow identifying users by their hash,
    without revealing the underlying info.
    '''
    # add a constant salt to generate
    salt = 'WI@N57%zZrmk#88c'
    salted_string = doc + salt
    sh = hashlib.sha256()
    sh.update(salted_string.encode())
    hashed_string = sh.digest().hex()
    return hashed_string


import findspark
# Initialize findspark with the specified SPARK_HOME
findspark.init(os.environ["SPARK_HOME"])
import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType

# Create SparkSession
spark = SparkSession.builder \
    .appName("S3App") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.2,com.amazonaws:aws-java-sdk-bundle:1.11.375,ru.yandex.clickhouse:clickhouse-jdbc:0.2.6") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.access.key", os.environ["AWS_ACCESS_KEY_ID"]) \
    .config("spark.hadoop.fs.s3a.secret.key", os.environ["AWS_SECRET_ACCESS_KEY"]) \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .getOrCreate()

pseudonymize_udf = F.udf(pseudonymize_doc_string, StringType())

# Read a JSON file from S3 (LocalStack)
try:
    df = spark.read.json("s3a://mybucket/stripe/2024/07/15/type=json/users_132258.json")
    df = df.withColumn("email", pseudonymize_udf(F.col("email")))
    df.show()
    df.printSchema()
except Exception as e:
    print(f"Error reading data: {e}")



clickhouse_url = "jdbc:clickhouse://localhost:8123/default"
clickhouse_properties = {
    "driver": "ru.yandex.clickhouse.ClickHouseDriver",
    "user": "clickhouse-user",
    "password": "secret"
}

# Write DataFrame to ClickHouse
try:
    df.write \
      .format("jdbc") \
      .option("url", clickhouse_url) \
      .option("dbtable", "users") \
      .option("user", clickhouse_properties["user"]) \
      .option("password", clickhouse_properties["password"]) \
      .option("driver", clickhouse_properties["driver"]) \
      .mode("append") \
      .save()
    print("Data written to ClickHouse successfully.")
except Exception as e:
    print(f"Error writing data to ClickHouse: {e}")