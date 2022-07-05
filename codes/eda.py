import pandas as pd
from dataprep import eda as dpeda
df = pd.read_csv('~/Desktop/ckip_absa/test_data/review_clean.csv')
print(df)


report = dpeda.create_report(df, title='review EDA Report')
report.save('review_eda')

