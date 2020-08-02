import json
import pandas as pd
import boto3
from sqlalchemy import create_engine
import os
import urllib.parse
import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

class PostgressDB():
    def __init__(self, username, password, port, host, database):
        self.user_name = username
        self.password = password
        self.port = port
        self.host = host
        self.database = database
        self.conn_string = self.__get_connect_string()

    def __get_connect_string(self):
        """
        Build the connection string for postgres
        :return: String: valid connection string for sqlalchemy engine
        """
        return 'postgresql://{}:{}@{}:{}/{}'.format(self.user_name, self.password, self.host, self.port, self.database)

    def create_engine(self):
        """
        return a create_engine object with pooling
        :return:
        """
        return create_engine(self.conn_string, pool_size=20, max_overflow=0)


def process_json_file(jsonf):
    """
    Process the result from appflow google analytics extraction. The json structure needs to
    converted to a table structure
    :param jsonf: JSON structure
    :return: Pandas Dataframe
    """
    logger.info("Starting conversion JSON format to table format.")
    logger.info("Detecting {} valid JSON structures in the objects".format(str(len(jsonf))))
    #JsonF is a list but the cols and metrics will always be the same across multiple jsons for 1 file
    cols = []
    try:
        cols = [r for r in jsonf[0]['reports'][0]['columnHeader']['dimensions']]
    except:
        logger.warning("No dimensions specified.")
    metrics = []
    try:
        metrics = [r['name'] for r in jsonf[0]['reports'][0]['columnHeader']['metricHeader']['metricHeaderEntries']]
    except:
        logger.warning("No metrics specified.")


    pd_result = None

    for list_index in range(len(jsonf)):
        data_rows = [r for r in jsonf[list_index]['reports'][0]['data']['rows']]
        dim_result_dict = {}

        for row in data_rows:
            #if there are dimensions, extract the dimension data and add values per key
            for i in range(len(cols)):
                if cols[i] in dim_result_dict.keys():
                    data_list = dim_result_dict[cols[i]]
                    data_list.append(row['dimensions'][i])
                    dim_result_dict.update({cols[i]: data_list})
                else:
                    dim_result_dict[cols[i]] = [row['dimensions'][i]]

            # if there are metrics, extract the metrics data and add values per key
            for i in range(len(metrics)):
                if metrics[i] in dim_result_dict.keys():
                    data_list = dim_result_dict[metrics[i]]
                    data_list.append(row['metrics'][0]['values'][i])
                    dim_result_dict.update({metrics[i]: data_list})
                else:
                    dim_result_dict[metrics[i]] = [row['metrics'][0]['values'][i]]
        #Create dataframe for the first JSON object otherwise append to existing
        if list_index == 0:
            pd_result = pd.DataFrame.from_dict(dim_result_dict)
        else:
            pd_result = pd_result.append(pd.DataFrame.from_dict(dim_result_dict))
        logger.info("Finished conversion JSON format to table format.")
    return pd_result

def lambda_handler(event, context):
    logger.info("Starting appflow conversion")
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    s3_client = boto3.client('s3')

    logger.info("Processing bucket {}, filename {}".format(bucket_name,object_key))

    raw_object = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    raw_data = json.loads('[' + raw_object['Body'].read().decode('utf-8').replace('}\n{', '},{') + ']')
    #Raw data is always a list of JSON objects
    pd_result = process_json_file(raw_data)

    db = PostgressDB(username=os.getenv("DB_USERNAME"),
                     password=os.getenv("DB_PASSWORD"),
                     port=5432,
                     host=os.getenv("DB_HOST"),
                     database=os.getenv("DB_DATABASE"))
    db_tmp_table = os.getenv("DB_TABLE_TMP")
    logger.info("Writing data to the table {}".format(db_tmp_table))

    pd_result.to_sql(name=db_tmp_table, con=db.create_engine(), index=False, if_exists='replace')

    logger.info("Finished appflow conversion")
