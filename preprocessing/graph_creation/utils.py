from Neo4j import NeoDriver


def fill_empty(driver:NeoDriver):
    """
    In some case if the sensor data does not have a single measure of a particular day, the measuraments node won't be created for that day. For resolve this issue run this function
    """
    with driver.driver.session() as session:
            result = session.write_transaction(create_null_nodes)
            result = session.write_transaction(create_avg_nodes)
            return result

@staticmethod
def create_null_nodes(tx):
        result = tx.run("""
            MATCH (s:Sensor)-[:HAS]-(m:Measurement) WITH s,COUNT(m.total_flow) as vector WHERE vector <> 2976 //  96 measuraments * 31 days  = 2976
            WITH s
            UNWIND range(1, 31) AS day
            OPTIONAL MATCH(s)-[:HAS]-(m:Measurement)
            WHERE m.dayOfMonth = day
            WITH day,s
            WHERE m is NULL
            FOREACH (i IN range(0, 95) |
            MERGE (m:Measurement {
                sensor_id: s.id,
                start_time: datetime({year: 2020, month: 1, day: day, hour: 0, minute:0, second: 0}),
                end_time: datetime({year: 2020, month: 1, day: day, hour: 0, minute:15, second: 0}),
                rangeCount:i,
                dayOfMonth: day,
                total_flow: 0,
                fake: true
                })
            MERGE (s)-[:HAS]->(m)
            )
        """)
        return result.consume()


@staticmethod
def create_avg_nodes(tx):
       result = tx.run("""
            CREATE INDEX measurement_time FOR (m:Measurement) ON (m.start_time, m.end_time)                    
            MATCH (s:Sensor)-[:HAS]-(m:Measurement) WITH s, COUNT(m.total_flow) as vector WHERE vector <> 2976
            UNWIND range(1,31) as day
            UNWIND range(0,95) as i
            WITH s, day, i, 
            datetime({year: 2020, month: 1, day: day, hour: i/4, minute: (i % 4) * 15, second: 0}) as start_time,
            CASE
                WHEN i = 95 AND day = 31 THEN datetime({year: 2020, month: 2, day: 1, hour: 0, minute: 0, second: 0})
                WHEN i = 95 THEN datetime({year: 2020, month: 1, day: day+1, hour: 0, minute: 0, second: 0})
                ELSE datetime({year: 2020, month: 1, day: day, hour: (i + 1)/4, minute: ((i + 1) % 4) * 15, second: 0})
            END as end_time
            WHERE NOT EXISTS {
                MATCH (s)-[:HAS]-(m:Measurement)
                WHERE m.start_time = start_time AND m.end_time = end_time
            }

            WITH s, day, i, start_time, end_time
            MATCH (s)-[:HAS]-(existing:Measurement)
            WHERE existing.start_time.hour = start_time.hour 
            AND existing.start_time.minute = start_time.minute
            WITH s, day, i, start_time, end_time, avg(existing.total_flow) as avg_value

            MERGE (m:Measurement {
                    sensor_id: s.id,
                    start_time: start_time,
                    end_time: end_time,
                    dayOfMonth: day,
                    total_flow: avg_value,
                    fake: true
            })
            MERGE (s)-[:HAS]->(m)
                """)
       return result.consume()
