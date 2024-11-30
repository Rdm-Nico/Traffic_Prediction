import osmnx as ox
import argparse
from neo4j import GraphDatabase
from Neo4j import NeoDriver



def add_options():
    parser = argparse.ArgumentParser(description='Creation of routing graph.')
    parser.add_argument('--latitude', '-x', dest='lat', type=float,
                        help="""Insert latitude of city center""",
                        required=True)
    parser.add_argument('--longitude', '-y', dest='lon', type=float,
                        help="""Insert longitude of city center""",
                        required=True)
    parser.add_argument('--distance', '-d', dest='dist', type=float,
                        help="""Insert distance (in meters) of the area to be cover""",
                        required=True)
    parser.add_argument('--neo4jURL', '-n', dest='neo4jURL', type=str,
                        help="""Insert the address of the local neo4j instance. For example: neo4j://localhost:7687""",
                        required=True)
    parser.add_argument('--neo4juser', '-u', dest='neo4juser', type=str,
                        help="""Insert the name of the user of the local neo4j instance.""",
                        required=True)
    parser.add_argument('--neo4jpwd', '-p', dest='neo4jpwd', type=str,
                        help="""Insert the password of the local neo4j instance.""",
                        required=True)
    parser.add_argument('--nameFile', '-f', dest='file_name', type=str,
                        help="""Insert the name of the .graphml file.""",
                        required=True)
    return parser


def main(args=None):
    argParser = add_options()
    #retireve attributes
    options = argParser.parse_args(args=args)
    #connecting to the neo4j instance
    greeter = NeoDriver(options)
    path = greeter.get_path()[0][0] + '/' + options.file_name
    #using osmnx to generate the graphml file
    G = ox.graph_from_point((options.lat, options.lon),
                            dist=int(options.dist),
                            dist_type='bbox',
                            simplify=False,
                            network_type='drive'
                            )
    ox.save_graphml(G, path)
    #check if there is a spatial layer and if there is not generate it
    #greeter.generate_spatial_layer()
    #creating the graph
    greeter.creation_graph()
    #setting nodes' labels
    greeter.set_label()
    #setting nodes' locations
    greeter.set_location()
    #setting nodes' distances
    greeter.set_distance()
    #setting index
    greeter.set_index()
    #inserting the nodes in the spatial layer
    
    greeter.close()



main()
