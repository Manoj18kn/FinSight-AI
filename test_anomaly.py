import pandas as pd
from ml.anomaly_detection import detect_anomalies

data = pd.DataFrame({"amount": [100, 200, 150, 180, 5000, 120, 90, 170, 160, 130]})
print(detect_anomalies(data).to_string(index=False))
