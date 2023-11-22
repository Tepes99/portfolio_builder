from databricks import sql
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
server_hostname = os.getenv('AZURE_DB_HOST')
http_path = os.getenv('AZURE_DB_HTTP_PATH')
access_token = os.getenv('AZURE_DB_ACCESS_TOKEN')

def query_db(query:str)-> pd.DataFrame:
    connection = sql.connect(
                            server_hostname = server_hostname,
                            http_path = http_path,
                            access_token = access_token)

    cursor = connection.cursor()

    cursor.execute(query)

    result = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    cursor.close()
    connection.close()

    return pd.DataFrame(result, columns=columns)
