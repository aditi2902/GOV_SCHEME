import pandas as pd

df = pd.read_csv("data/updated_data.csv")

print(df.columns)
print(df.shape)
print(df.iloc[0]["scheme_name"])

print(df.iloc[0]["eligibility"])