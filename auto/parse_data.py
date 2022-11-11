
import os
import pandas as pd
import numpy as np

DATA_DIR = "./data"

files = os.listdir(DATA_DIR)
GT = []
SENSOR_MEAN = []
SENSOR_STD = []
BARREL = []

for fname in files:
    barrel = True
    if 'GT_T_' in fname:
        barrel = True
        ground_truth_inches = fname.split('GT_T_')[1].split('i')[0]
    else:
        barrel = False
        ground_truth_inches = fname.split('GT')[1].split('i')[0]
    
    ground_truth_meters = 0.0254 * float(ground_truth_inches)
    df = pd.read_csv(f'./data/{fname}')

    GT.append(ground_truth_meters)
    SENSOR_MEAN.append(df["Likely_distance"].mean())
    SENSOR_STD.append(df["Likely_distance"].std())
    BARREL.append(barrel)
    
    
    print(f'Barrel={barrel}, Ground Truth Meters={ground_truth_meters}, Mean={df["Likely_distance"].mean()}, StD={df["Likely_distance"].std()}')

lr_df = pd.DataFrame(data={'GT': GT, 'MEAN':SENSOR_MEAN, 'STD':SENSOR_STD, 'B': BARREL})
print(lr_df)

from sklearn.linear_model import LinearRegression
dataset = lr_df[lr_df['B'] == False]
X = np.array(dataset['MEAN']).reshape(-1, 1)
print(X)
y = np.array(dataset['STD']).reshape(-1, 1)
print(y)
model_std = LinearRegression().fit(X, y)
predict = 3
print(model_std.predict(np.array([predict]).reshape(1, 1)))

X = np.array(dataset['MEAN'])
y = np.array(dataset['STD'])
print(X)
print(y)
p = np.polyfit(X, np.log(y), 2)
predict = lambda x: np.exp(p[1]) * np.exp(p[0] * x)

import matplotlib.pyplot as plt

x_fitted = np.linspace(np.min(X), np.max(X), 100)
y_fitted = predict(x_fitted)

ax = plt.axes()
ax.scatter(X, y, label='Raw data')
ax.plot(x_fitted, y_fitted, 'k', label='Fitted curve')
ax.set_title('Using polyfit() to fit an exponential function')
ax.set_ylabel('y-Values')
ax.set_ylim(0, 1)
ax.set_xlabel('x-Values')
ax.legend()
plt.show()