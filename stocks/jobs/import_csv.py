import pandas as pd
from sqlalchemy import create_engine

from stocks.core.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

df = pd.read_csv("/Users/jangjiwan/Downloads/백엔드 과제 - 가격.csv")

df_melted = df.melt(id_vars=["date"], var_name="ticker", value_name="price")

# 변환된 데이터 확인 (상위 5개 출력)
print(df_melted.head())

# PostgreSQL에 저장
df_melted.to_sql("daily_ticker", engine, if_exists="append", index=False)