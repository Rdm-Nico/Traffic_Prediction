sensor_traffic_location.csv# Importing Data and Preprocessing

1. Create the Modena street Network with the script:

```
python crateJunctionGraph.py -x 44.645885 -y 10.9255707 -d 5000 -n neo4j://localhost:7687 -u neo4j -p passwd -f modena.graphml
```

2. add the sensor information to that graph:
   For import the traffic_data_january_2020 you need to unzip the file inside this [GoogleDrive](https://drive.google.com/file/d/1QwnA0NJzqCiWWa2H9-bBsu4LzFuOxi2H/view?usp=sharing) and place inside data/ folder.
   Run this script:

```
python3 createSensorGraph.py -n neo4j://localhost:7687 -u neo4j -p passwd -l data/sensor_traffic_location.csv -d data/sensor_traffic_observation.csv
```

Where the `sensor_traffic_location.csv ` has the information for the sensor location and `sensor_traffic_observation.csv` has the information on the flow. 3. Run this query for import the data inside Neo4j DBMS:

```Chyper
:auto

CREATE INDEX measurement_lookup IF NOT EXISTS FOR (m:Measurement) ON (m.sensor_id, m.start_time, m.end_time);
CREATE INDEX sensor_lookup IF NOT EXISTS FOR (s:Sensor) ON (s.id);

LOAD CSV WITH HEADERS FROM 'file:///' + $file AS row
CALL {
    WITH row
    WITH row.id_sensor_traffic AS sensor_id,
         datetime(replace(row.datetime, ' ', 'T')) AS dt,
         toInteger(row.flow) AS flow

    WITH sensor_id,
         datetime({year: dt.year, month: dt.month, day: dt.day}) as dayStart,
         dt,
         flow

    WITH sensor_id,
         dayStart,
         collect({dt: dt, flow: flow}) as measurements

    UNWIND range(0, 95) AS interval // 24 * 4 = 96 intervals of 15 min in a day
    WITH sensor_id,
         dayStart + duration({minutes: interval * 15}) AS intervalStart,
         dayStart + duration({minutes: (interval + 1) * 15}) AS intervalEnd,
         measurements

    WITH sensor_id,
         intervalStart,
         intervalEnd,
         [x IN measurements WHERE
          datetime(x.dt) >= intervalStart AND
          datetime(x.dt) < intervalEnd] AS interval_measurements

    WITH sensor_id,
         intervalStart,
         intervalEnd,
         CASE
             WHEN size(interval_measurements) > 0
             THEN reduce(s = 0, m IN interval_measurements | s + m.flow)
             ELSE 0
         END as total_flow

    MATCH (s:Sensor {id: sensor_id})

    MERGE (f:Measurement {
        sensor_id: sensor_id,
        start_time: intervalStart,
        end_time: intervalEnd
    })
    ON CREATE SET
        f.total_flow = total_flow
    ON MATCH SET
        f.total_flow = f.total_flow + total_flow

    MERGE (s)-[:HAS]->(f)
    }
} IN TRANSACTIONS OF 10000 ROWS
```
