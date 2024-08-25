import os
import pandas as pd
# import pandas_gbq as pdgbq

import google.auth
from google.oauth2 import service_account
from google.cloud import bigquery


GOOGLE_PROJECT = os.getenv("GOOGLE_PROJECT", 'gristmill5')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", 'creds/gristmill5-e521e2f08f35.json')

def bq_conn(sql):

    try:
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        client = bigquery.Client(GOOGLE_PROJECT, credentials)
        df = client.query(sql, project=GOOGLE_PROJECT).to_dataframe()

        return df

    except Exception as e:
        print(e)
        return 'error running query'
