from neo4j import GraphDatabase
import numpy as np
import pandas as pd

class NeoDriver:
    def __init__(self, options):
        
        self.options = options
        print(type(self.options))
        self.driver = GraphDatabase.driver(self.options.neo4jURL, auth=(self.options.neo4juser, self.options.neo4jpwd))
        print('connection confirmed')

    def close(self):
        self.driver.close()

    def creation_graph(self):
        """create the graph from the .graphml file"""
        with self.driver.session() as session:
            result = session.write_transaction(self._creation_graph, self.options.file_name)
            return result
        
    def run_query(self, query, params={}):
        with self.driver.session() as session:
            result = session.run(query, params)
            return pd.DataFrame([r.values() for r in result], columns=result.keys())

    @staticmethod
    def _creation_graph(tx, file):
        result = tx.run("""
                        CALL apoc.import.graphml($file, {storeNodeIds: true, defaultRelationshipType: 'ROUTE'});
                    """, file=file)
        return result.values()
    def get_path(self):
        """gets the path of the neo4j instance"""
        with self.driver.session() as session:
            result = session.write_transaction(self._get_path) 
            print(f' this is the result: {result}')
            return result

    @staticmethod
    def _get_path(tx):
        # fix with the version of 5.24:
        result = tx.run("""
                        Call dbms.listConfig() YIELD name, value
                        WHERE name='server.directories.import'
                        RETURN value
                    """)
        return result.values()
        
    def get_import_folder_name(self):
        """get the name of the import directory for the neo4j instance"""
        with self.driver.session() as session:
            result = session.write_transaction(self._get_import_folder_name)
            return result

    @staticmethod
    def _get_import_folder_name(tx):
        result = tx.run("""
                        Call dbms.listConfig() yield name,value where name = 'dbms.directories.import' return value;
                    """)
        return result.values()

    def set_label(self):
        """set the Node lable to nodes"""
        with self.driver.session() as session:
            result = session.write_transaction(self._creation_label)
            return result

    @staticmethod
    def _creation_label(tx):
        result = tx.run("""
                        MATCH (n) SET n:RoadJunction;
                    """)
        return result.values()

    def set_location(self):
        """insert the location in the node attributes"""
        with self.driver.session() as session:
            result = session.write_transaction(self._creation_location)
            return result

    @staticmethod
    def _creation_location(tx):
        result = tx.run("""
                           MATCH (n:RoadJunction) SET n.location = point({latitude: tofloat(n.y), longitude: tofloat(n.x)}),
                                            n.lat = tofloat(n.y), 
                                            n.lon = tofloat(n.x),
                                            n.geometry='POINT(' + n.y + ' ' + n.x +')';
                       """)
        return result.values()

    def set_distance(self):
        """insert the distance in the nodes' relationships."""
        with self.driver.session() as session:
            result = session.write_transaction(self._set_distance)
            return result

    @staticmethod
    def _set_distance(tx):
        result = tx.run("""
                           MATCH (n:RoadJunction)-[r:ROUTE]-() SET r.distance=tofloat(r.length), r.status='active'
                       """)
        return result.values()
    
    def set_index(self):
        """create index on nodes"""
        with self.driver.session() as session:
            result = session.write_transaction(self._set_index)
            return result

    @staticmethod
    def _set_index(tx):
        result = tx.run("""
                           create index FOR :RoadJunction(id)
                       """)
        return result.values()
        
    def generate_spatial_layer(self):
        """generate the spatial layer of the project"""
        with self.driver.session() as session:
            result = session.write_transaction(self._generate_spatial_layer)
            return result

    @staticmethod
    def _generate_spatial_layer(tx):
        result = tx.run("""
                call spatial.layers()
                """)
        if len(result.values()) == 0:
            result = tx.run("""
                call spatial.addWKTLayer('spatial', 'geometry')
                """)
        return result.values()
        
    def import_nodes_in_spatial_layer(self):
        """insert the road junctions in the spatial layer of the project"""
        with self.driver.session() as session:
            result = session.write_transaction(self._import_nodes_in_spatial_layer)
            return result

    @staticmethod
    def _import_nodes_in_spatial_layer(tx):
        result = tx.run("""
        match (n:RoadJunction)
        CALL spatial.addNode('spatial', n) yield node return node;
        """)
        return result.values()
    
    def create_sensor_graph(self, loc_file):
        """Create the sensor graph from the CSV file"""
        with self.driver.session() as session:
            result = session.write_transaction(self._create_sensor_graph, loc_file)
            return result

    @staticmethod
    def _create_sensor_graph(tx, file):
        result = tx.run("""
            LOAD CSV WITH HEADERS FROM 'file:///' + $file AS row FIELDTERMINATOR ';'
            WITH row
            WHERE row.road_section <> '(null)'
            MERGE (s:Sensor {id: row.id})
            SET s.latitude = toFloat(row.latitude),
                s.longitude = toFloat(row.longitude),
                s.num_segment = CASE WHEN row.num_segment = '(null)' THEN NULL ELSE toInteger(row.num_segment) END
            MERGE (r:RoadSection {id: row.road_section})
            WITH s,row
            MATCH (j:RoadJunction {id: row.nearest_node})
            MERGE (s)-[:LOCATED_ON]->(r)
            MERGE (s)-[:NEAREST_TO]->(j)
        """, file=file)
        return result.consume()

    def to_npz(self):
        """
        Create the npz file from the flow data  store in the graph
        """ 
        with self.driver.session() as session:
            
            # store all vectors
            vectors = []
            # compute the query
            results = session.execute_read(self._get_flow)
            for node in results:
                print(f'save data of sensor: {node.data()['Sensor']}')
                v = node.data()['vector']
                vectors.append(v)
            
            flows = np.array(vectors).swapaxes(1,0)

            print(f'flows shape: {flows.shape}')
        
            return flows

    @staticmethod
    def _get_flow(tx):
        result = tx.run("""
                        MATCH (s:Sensor)-[:HAS]-(m:Measurement) ORDER BY m.start_time RETURN s.id as Sensor,collect(m.total_flow) as vector ORDER BY s.id
                    """)
        return list(result)


    
    def get_adj(self):
        """
        Get adjacency matrix of the Graph
        """
        with self.driver.session() as session:
            # create the rel
            print("create relations with distance = ",self.options.dst)
            results = session.execute_write(self._create_adj, self.options.dst)
            print(results)

            # return adj matrix 
            vectors = []
            results = session.execute_read(self._get_adj)
            for node in results:
                print(f'save data of sensor: {node.data()['Sensor']}')
                v = node.data()['vector']
                vectors.append(v)
            
            adj = np.array(vectors)

            print(f' adj shape: {adj.shape}')
            return adj


    @staticmethod
    def _create_adj(tx, dst):
        result = tx.run("""
                         MATCH(s:Sensor),(t:Sensor)
                         WHERE s.id < t.id
                        WITH
                        point({longitude: s.longitude, latitude: s.latitude}) AS sourcePoint,
                        point({longitude: t.longitude, latitude: t.latitude}) AS targetPoint,s,t
                        WITH round(point.distance(sourcePoint, targetPoint)) AS travelDistance,s,t
                        WHERE travelDistance <= toInteger($dst)
                        MERGE (s)-[r:LINK_TO]->(t)
                        MERGE (s)<-[r1:LINK_TO]-(t)
                        SET r.distance = travelDistance
                        SET r1.distance = travelDistance 
                    """, dst=dst)
        return result.consume()
    
    @staticmethod
    def _get_adj(tx):
        result = tx.run("""
                        MATCH (s:Sensor)
                        WITH collect(s) as sensors, collect(s.id) as sensor_ids
                        UNWIND sensors as source
                        WITH source, sensor_ids, sensors
                        ORDER BY source.id
                        WITH source, sensor_ids, collect(source) as sources, sensors
                        UNWIND sensors as target
                        WITH source, target, sensor_ids
                        ORDER BY target.id
                        OPTIONAL MATCH (source)-[r:LINK_TO]->(target)
                        WITH source.id as Sensor, collect(CASE WHEN r IS NOT NULL THEN 1 ELSE 0 END) as vector
                        RETURN Sensor, vector
                        ORDER BY Sensor
                        """)
        return list(result)
    
    def __del__(self):
        self.close()
    