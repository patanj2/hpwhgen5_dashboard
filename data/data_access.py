import json
import os

import pandas as pd
import numpy as np
from pymongo import MongoClient

from data_preprocessing import clean_data


class EcoNetHistory(object):
    # Retrieve the Data on which to do the Dashboard

    def __init__(self):
        client = MongoClient('mongodb://localhost:27017/dev')
        self.client=client
        self.collection = self.client['dev']['history_HPWHGEN512192019']
        dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        with open(os.path.join(dir_path, 'resources', 'appconfig.json')) as f:
            self.config = json.load(f)

    def get_latest_sw_version(self, mac_addresses):
        # TODO do in MongoDB
        address_range = list(range(4736, 4736+32))
        pipeline = [{'$match': {'device_base_address': {'$in': address_range},
                                'mac_address': {"$in": mac_addresses}
                                }},
                    {'$group': {'_id': {'base_address': '$device_base_address',
                                        'mac_address': '$mac_address'},
                                'software_version': {'$max': '$SW_VERSN'}}}
                    ]
        # retrieve data from MongoDB
        mac_addresses = []
        sw_versions = []

        cursor = self.collection.aggregate(pipeline)
        for c in cursor:
            mac_addresses.append(c['_id']['mac_address'])
            sw_versions.append(c['software_version'])

        return pd.DataFrame({'mac_address': mac_addresses,
                             'software_version': sw_versions})

    def get_device_accumulators(self, mac_address, accumulators):
        """
        :param mac_address
        :param accumulators

        """
        parameters = {a: {'$max': '$' + a} for a in accumulators}
        parameters['_id'] = 0

        pipeline = [
            {
                '$match': {
                    'device_base_address': 4736,
                    'mac_address': mac_address
                }
            }, {
                '$group': {
                    '_id': '$mac_address',
                    'HRSHIFAN': {
                        '$max': '$HRSHIFAN'
                    },
                    'HRSLOFAN': {
                        '$max': '$HRSLOFAN'
                    },
                    'HRSLOHTR': {
                        '$max': '$HRSLOHTR'
                    },
                    'HRSUPHTR': {
                        '$max': '$HRSUPHTR'
                    },
                    'HRS_COMP': {
                        '$max': '$HRS_COMP'
                    }
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        temp = list(cursor)
        return pd.DataFrame(temp).set_index('_id')

    def get_alarm_count_by_code(self):
        query = {'device_base_address': 4736}
        projection = {'ALARM_01': 1, 'ALARM_02': 1, 'ALARM_03': 1, 'ALARM_04': 1, '_id': 0}
        cursor = self.collection.find(query, projection)
        data = pd.DataFrame(list(cursor))
        df_obj = data.select_dtypes(['object'])
        data[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

        temp = data.melt(value_vars=['ALARM_01', 'ALARM_02', 'ALARM_03', 'ALARM_04'],
                              var_name='alarm_count',
                              value_name='alarm_code').replace('', np.nan).dropna(how='any').groupby('alarm_code').count().reset_index()

        return temp.loc[temp['alarm_code'].str.len() > 0]


    def read_mongo(self, query={"device_base_address": 4736}):
        """ Read from Mongo and Store into DataFrame """

        # Make a query to the specific DB and Collection
        cursor = self.collection.find(query, {"serial_number": 0,
                                         "transactionId": 0,
                                         "_id": 0,
                                         "cloud2_account_id": 0}, limit=600000)

        # Expand the cursor and construct the DataFrame
        df = pd.DataFrame(list(cursor))

        if not df.empty:
            df = clean_data(df)

        return clean_data(df)

    def query(self, device_base_address, device_mac_address, start_date, end_date):
        query = {"device_base_address": device_base_address,
                 "mac_address": device_mac_address,
                 "timestamp": {"$gt": start_date[0:10], "$lt": end_date[0:10]},
                 "transactionId": {"$lt": "CLOUD"}}

        return self.read_mongo(query)
