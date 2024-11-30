from datetime import datetime
import pandas as pd

"""
This file is used for clean and make digestibal the csv file to Neo4j
"""

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

if __name__ == "__main__":
    input_file = "./raw_data/traffic_data_10000.csv"
    df = pd.read_csv(input_file,sep="|")

    print(df.columns)
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
    df.to_csv("./raw_data/traffic_data_january_2020_B.csv", index=False)