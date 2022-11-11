import pandas as pd
import numpy as np
import os
from scipy.optimize import curve_fit
from statistics import NormalDist

def load_samples(data_dir):
    files = os.listdir(data_dir)
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

    return pd.DataFrame(data={'GT': GT, 'MEAN':SENSOR_MEAN, 'STD':SENSOR_STD, 'B': BARREL})

df = load_samples('./data')

dataset = df[df['B'] == False]

X = np.array(dataset['MEAN'])
y = np.array(dataset['STD'])

# Fit the function a * np.exp(b * t) + c to x and y
p = np.polyfit(X, np.log(y), 1)
predict = lambda x: np.exp(p[1]) * np.exp(p[0] * x)

min_distance_from_wall = 0.9
max_distance_from_wall = 1.1
number_of_nodes = 5
samples_size_per_dist = 500

overshoot_dist_percentage = 0.2

columns = { 'x1':[], 'x2':[], 'x3':[], 'x4':[], 'x5':[], 'barrel':[] }
  
df2 = pd.DataFrame(columns)
tests = [0.8,1.2]
for i in tests:
    std = predict(i)
    sensor_noise_generator = NormalDist(mu=0, sigma=std)
    
    for k in range(0, 2 * samples_size_per_dist):
        sample = np.full((number_of_nodes), i) - np.array(sensor_noise_generator.samples(n = number_of_nodes, seed = None))
        
        row = pd.DataFrame({ 'x1': [sample[0]], 'x2': [sample[1]], 'x3': [sample[2]], 'x4': [sample[3]], 'x5': [sample[4]], 'barrel': 0 })

        df2 = pd.concat([df2, row], ignore_index = True)
    barrel_coeff = overshoot_dist_percentage + 1

    barrel_patterns = [
        # [barrel_coeff,1,1,1,1],
        # [barrel_coeff,barrel_coeff,1,1,1],
        [1,barrel_coeff,barrel_coeff,1,1],
        [1,1,barrel_coeff,barrel_coeff,1],
        # [1,1,1,barrel_coeff,barrel_coeff],
        # [1,1,1,1,barrel_coeff],
    ]
    
    for k in range(0, samples_size_per_dist):
        for pattern in barrel_patterns:
            barrel_sample = np.array(pattern) * i - np.array(sensor_noise_generator.samples(n = number_of_nodes, seed = None))
            barrel_row = pd.DataFrame({ 'x1': [barrel_sample[0]], 'x2': [barrel_sample[1]], 'x3': [barrel_sample[2]], 'x4': [barrel_sample[3]], 'x5': [barrel_sample[4]], 'barrel': 1 })
            df2 = pd.concat([df2, barrel_row], ignore_index = True)


df2.to_csv('simulated_data.csv', index=False)

