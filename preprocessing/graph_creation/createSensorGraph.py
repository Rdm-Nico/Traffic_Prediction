# this file is used for create the sensors graph by the data/ folder 
import argparse
import os
import shutil
import pandas as pd 
from datetime import datetime
from Neo4j import NeoDriver


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
    parser.add_argument('--locFile', '-l', dest='loc_file', type=str,
                        help="""Insert the name of the csv location""",
                        required=False)
    parser.add_argument('--dataFile', '-d', dest='data_file', type=str,
                        help="""Insert the name of the csv data""",
                        required=False)
    return parser


def uniform_data(data_str):
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(data_str, "%d/%m/%y %H:%M")
            # add second and microsec
            dt = dt.replace(second=0, microsecond=0)
        except ValueError:
            raise ValueError(f"unknown format: {data_str}")
    # return data in uniform format with truncted decimal
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-7] 

def preproc_data(input_file):
    """
    IMPORTANT: this function clean specific error/improvement of the csv file inside googleDrive. if another data source is used check whether the changes that are needed to be made are the same 
    """
    df = pd.read_csv(input_file,sep="|")
    # rename the column 
    df.rename(columns={column : column.strip() for column in df.columns}, inplace=True)
    # delete useless columns
    del df['vehicle_type']
    del df['speed']
    # drop all nan
    df = df.dropna(how='any', axis=0)
    # strip the columns 
    df[['id_sensor_traffic', 'datetime']] = df[['id_sensor_traffic', 'datetime']].apply(lambda x: x.str.strip())
    
    # select the column
    data_colum = df.columns[1]
    # apply conv
    df[data_colum] = df[data_colum].apply(uniform_data)

    # save 
    df.to_csv(input_file, index=False)

def main(args=None):
    argParser = add_options()
    #retireve attributes
    options = argParser.parse_args(args=args)
    #connecting to the neo4j instance
    greeter = NeoDriver(options.neo4jURL, options.neo4juser, options.neo4jpwd)
    path = greeter.get_path()[0][0]
    # Copy the location and data files to the Neo4j import directory
    
    if options.loc_file:
        loc_file_dest = os.path.join(path, os.path.basename(options.loc_file))
        if not os.path.exists(loc_file_dest):
            shutil.copy2(options.loc_file, loc_file_dest)
    
    if options.data_file:
        data_file_dest = os.path.join(path, os.path.basename(options.data_file))
        if not os.path.exists(data_file_dest):
            print('preprocessing flow data...')
            preproc_data(options.data_file)
            shutil.copy2(options.data_file, data_file_dest)

    print(f"Files copied to Neo4j import directory: {path}")
    # Create the sensor graph from CSV
    if options.loc_file:
        result = greeter.create_sensor_graph(os.path.basename(options.loc_file))
        print(f"Sensor graph created: {result.counters}")
    greeter.close()



if __name__ == "__main__":
    main()


