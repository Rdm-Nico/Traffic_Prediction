from neo4j import GraphDatabase
import numpy as np
import argparse
from Neo4j import NeoDriver
# this file creates the .npy and .npz files for the model 

def add_options():
    parser = argparse.ArgumentParser(description='Creation of sensors graph.')
    parser.add_argument('--neo4jURL', '-n', dest='neo4jURL', type=str,
                        help="""Insert the address of the local neo4j instance. For example: neo4j://localhost:7687""",
                        required=True)
    parser.add_argument('--neo4juser', '-u', dest='neo4juser', type=str,
                        help="""Insert the name of the user of the local neo4j instance.""",
                        required=True)
    parser.add_argument('--neo4jpwd', '-p', dest='neo4jpwd', type=str,
                        help="""Insert the password of the local neo4j instance.""",
                        required=True)
    parser.add_argument('--dst', '-d', dest='dst', type=str,
                        help="""Insert the distance for compute the adj matrix""",
                        default=300,
                        required=False)
    return parser


if __name__ == "__main__":
    argParser = add_options()
    #retireve attributes
    options = argParser.parse_args()

    # create the connection
    greeter = NeoDriver(options)

    # create the npz file
    flows = greeter.to_npz()
    np.savez(f'../data/data_{options.dst}.npz', data=flows)

    # create the adj file
    adj = greeter.get_adj()
    np.save(f'../data/adj_{options.dst}.npy',adj)

    print(f'file created')





