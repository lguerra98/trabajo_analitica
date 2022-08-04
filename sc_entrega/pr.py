from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

credentials = service_account.Credentials.from_service_account_file('python_pk_trabajo_analitica.json')

project_id = 'sunlit-inn-353723'
client = bigquery.Client(credentials= credentials, project=project_id)
 
query = "SELECT * FROM `sunlit-inn-353723.trabajo_final_analitica.condiciones_vida`"
#df = pd.read_gbq(query, project_id=project_id)

df2 = client.query(query).to_dataframe()
#%%

df2['porcentaje'][0]