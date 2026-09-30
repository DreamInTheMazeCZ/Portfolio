import polars as pl
import json, time

from kafka import KafkaProducer

pl.Config.set_tbl_formatting("ASCII_FULL")
df = pl.read_csv('taxi_trip.csv').slice(1073, 1)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for row in df.to_dicts():
    producer.send('taxi_trip', value=row)
    print(f'Sent Kafka : {row}')
    
    time.sleep(0.1)  # Kafka 과부하 방지 임의 지연
    
producer.flush()
time.sleep(1) # Kafka 전송 완료 대기
producer.close()