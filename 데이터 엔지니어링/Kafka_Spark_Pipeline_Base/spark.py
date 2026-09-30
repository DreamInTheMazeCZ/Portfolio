from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import from_json, col

spark = (
    SparkSession.builder
    .remote("sc://localhost:15002")
    .appName("TaxiStreamingApp")
    .getOrCreate()
)

# ===== ===== Spark 데이터 읽기 ===== ===== 
# df = (
#     spark.read
#     .format("kafka")
#     .option("kafka.bootstrap.servers", "kafka:29092")
#     .option("subscribe", "taxi_trip")
#     .option("startingOffsets", "earliest")
#     .option("endingOffsets", "latest")
#     .load()
# )

# df.selectExpr(
#     "CAST(key AS STRING) AS key",
#     "CAST(value AS STRING) AS value",
#     "topic",
#     "partition",
#     "offset",
#     "timestamp"
# ).show(10, truncate=False)


# ===== ===== Kafka 스트리밍 데이터 읽기 ===== ===== 
raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:29092")
    .option("subscribe", "taxi_trip")
    .option("startingOffsets", "earliest")
    .load()
)

# query = (
#     raw_df
#     .selectExpr(
#         "CAST(key AS STRING) AS key",
#         "CAST(value AS STRING) AS value",
#         "topic",
#         "partition",
#         "offset",
#         "timestamp"
#     )
#     .writeStream
#     .format("console")
#     .outputMode("append")
#     .option("truncate", False)
#     .option("numRows", 5)
#     .start()
# )

schema = StructType([
    StructField("trip_id", StringType()),
    StructField("pickup_datetime", StringType()),
    StructField("pickup_zone", StringType()),
    StructField("dropoff_zone", StringType()),
    StructField("passenger_count", IntegerType()),
    StructField("distance", DoubleType()),
    StructField("fare_amount", DoubleType()),
])

taxi_df = (
    raw_df
    .selectExpr("CAST(value AS STRING)")
    .select(
        from_json(col("value"), schema).alias("data")
    )
    .select("data.*")
)


# taxi_df 디버깅
debug_query = (
    taxi_df
    .writeStream
    .format("console")
    .outputMode("append")
    .option("truncate", False)
    .option("numRows", 5)
    .start()
)


result_df = (
    taxi_df
    .groupBy("pickup_zone")
    .count()
)

debug_result_query = (
    result_df
    .writeStream
    .format("console")
    .outputMode("complete")
    .option("truncate", False)
    .start()
)


def write_to_postgres(batch_df, batch_id):

    print(f"\n========== BATCH {batch_id} ==========")

    try:
        print("1. Batch received")

        batch_df.show(truncate=False)

        count = batch_df.count()
        print(f"2. Row count: {count}")

        if count == 0:
            print("3. Empty batch - skip")
            return

        print("4. Starting PostgreSQL write...")

        (
            batch_df
            .write
            .format("jdbc")
            .option(
                "url",
                "jdbc:postgresql://postgres:5432/sparkdb"
            )
            .option("dbtable", "taxi_zone_count")
            .option("user", "spark")
            .option("password", "spark1234!@")
            .option("driver", "org.postgresql.Driver")
            .mode("append")
            .save()
        )

        print("5. PostgreSQL write SUCCESS")

    except Exception as e:
        print("!!! PostgreSQL write FAILED !!!")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception: {e}")

        raise

    finally:
        print(f"========== END BATCH {batch_id} ==========\n")

query = (
    result_df
    .writeStream
    .foreachBatch(write_to_postgres)
    .outputMode("complete")
    .start()
)

print("Streaming started. Press Ctrl+C to stop.")

query.awaitTermination()
