import sys
from pathlib import Path

import pandas as pd
import numpy as np

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/vgsales.csv")
df = pd.read_csv(csv_path)

columns = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]
df[columns] = df[columns].astype(float) * 1_000_000

df.to_csv(csv_path, index=False) #Não rode novamente, por favor :)

