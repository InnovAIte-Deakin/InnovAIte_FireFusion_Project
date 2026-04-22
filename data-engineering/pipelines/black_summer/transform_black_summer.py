import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_ROOT = os.getenv("DATA_ROOT")

file = os.path.join(DATA_ROOT, "processed", "bushfire_metadata.csv")

print("Loading metadata...")

df = pd.read_csv(file)

df['ignition_date'] = pd.to_datetime(df['ignition_date'], errors='coerce')

black_summer = df[
    (df['ignition_date'] >= "2019-08-01") &
    (df['ignition_date'] <= "2020-02-29")
]

print("Black Summer Records:", len(black_summer))

print("\nPreview:")
print(black_summer.head())

output = os.path.join(DATA_ROOT, "processed", "black_summer.csv")

black_summer.to_csv(output, index=False)

print("\nBlack Summer dataset saved")