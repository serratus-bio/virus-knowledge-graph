# !pip install taxoniq
import pandas as pd
import taxoniq
from google.colab import files

df = pd.read_csv('host_nodes.csv')
df = df.reset_index()

missing_ids = []
tax_ids = [None] * len(df)

for index, row in df.iterrows():
  try:
    t = taxoniq.Taxon(scientific_name=row['scientific_name'])
    tax_ids[index] = t.tax_id
  except:
    missing_ids.append(row['scientific_name'])

df['taxonomy_id'] = tax_ids
df.to_csv('host_nodes_id.csv', columns=['scientific_name', 'taxonomy_id'], index=False,)
files.download('host_nodes_id.csv')
