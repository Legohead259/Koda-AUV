import pandas as pd
import numpy as np
import os
from scipy.optimize import curve_fit
from statistics import NormalDist

SM_CUTOFF= 0.80
ML_CUTOFF = 1.2
L_CUTOFF = 3

TRAVEL_DIST = 1

# D will be characterized in three categories: SMALL (d < SM_CUTOFF), MEDIUM (d >= ML_CUTOFF)
# we will consider that all the distances are equally likely to occur, regardless of data
def get_d_prior(std_predictor):
    # sigma = std_predictor(TRAVEL_DIST)
    # print(sigma)
    # dist = NormalDist(mu=TRAVEL_DIST, sigma=sigma)
    # a = dist.cdf(SM_CUTOFF)
    # b = dist.cdf(ML_CUTOFF)
    # return  [[a], [b-a], [1-b]]
    return [[1/3], [1/3], [1/3]]

# Load dataframe from multiple samples
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


# Probability of X (true distance) given d (sonar measured distance) using weighted intensity measurements
# we will assume the true distance probably given a measure follows a normal distribution
def get_x_given_d(predict):
    
    # Predict the mean and std for S, M, L by considering the distribution in the mid point between discrete values
    # Calculate probabilities for S, M, L given measurement was S.
    S_mean = SM_CUTOFF / 2
    S_std = predict(S_mean)
    
    S_dist = NormalDist(mu=S_mean, sigma=S_std)
    a = S_dist.cdf(SM_CUTOFF)
    b = S_dist.cdf(ML_CUTOFF)
    S_CPT = [a, b-a, 1-b]

    M_mean = (SM_CUTOFF + ML_CUTOFF) / 2
    M_std = predict(M_mean)
    
    M_dist = NormalDist(mu=M_mean, sigma=M_std)
    a = M_dist.cdf(SM_CUTOFF)
    b = M_dist.cdf(ML_CUTOFF)
    M_CPT = [a, b-a, 1-b]
    
    L_mean = (ML_CUTOFF + L_CUTOFF) / 2
    L_std = predict(L_mean)
    
    L_dist = NormalDist(mu=L_mean, sigma=L_std)
    a = L_dist.cdf(SM_CUTOFF)
    b = L_dist.cdf(ML_CUTOFF)
    L_CPT = [a, b-a, 1-b]
    
    return [S_CPT, M_CPT, L_CPT]

def convert_to_label(x):
    if x >= ML_CUTOFF:
        return 2
    elif x >= SM_CUTOFF:
        return 1
    else:
        return 0

# Probability of a barrel given last 3 X's
def get_barrel_given_x(samples_csv):
    df = pd.read_csv(samples_csv).dropna().astype(float)
    df['x1'] = df['x1'].transform(convert_to_label)
    df['x2'] = df['x2'].transform(convert_to_label)
    df['x3'] = df['x3'].transform(convert_to_label)
    df['x4'] = df['x4'].transform(convert_to_label)
    df['x5'] = df['x5'].transform(convert_to_label)
    
    print(df)

    # Calculate Non-barrel probabilities
    nonbarrel_probabilities = []
    
    for i in range(0,3):
        for j in range(0,3):
            for k in range(0,3):
                for l in range(0,3):
                    for m in range(0,3):
                        parcial_df = df[(df['x1'] == i)&(df['x2'] == j)&(df['x3'] == k)&(df['x4'] == l)&(df['x5'] == m)]
                        total_samples = len(parcial_df)
                        if total_samples == 0:
                            nonbarrel_probabilities.append(1.0)
                            continue
                            
                        barrel_samples = len(parcial_df[parcial_df['barrel'] == 1])
                        p_barrel = barrel_samples / total_samples
                        
                        nonbarrel_probabilities.append(1 - p_barrel)

    barrel_probabilities = [1 - x for x in nonbarrel_probabilities]
    return [nonbarrel_probabilities, barrel_probabilities]

def std_predict_model(df):
    # First we will pick up only samples without barrels
    dataset = df[df['B'] == False]
    
    # Create a model to estimate the standard deviation given certain mean based on the samples we have
    X = np.array(dataset['MEAN'])
    y = np.array(dataset['STD'])

    # Fit the function a * np.exp(b * t) + c to x and y
    p = np.polyfit(X, np.log(y), 1)
    predict = lambda x: np.exp(p[1]) * np.exp(p[0] * x)
    return predict

samples = load_samples('./data')
std_predictor = std_predict_model(samples)

d_priors = get_d_prior(std_predictor)
x_cond_values = get_x_given_d(std_predictor)

print(d_priors)
print(x_cond_values)

from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD

model = BayesianNetwork([('D1', 'X1'), ('D2', 'X2'), ('D3', 'X3'), ('D4', 'X4'), ('D5', 'X5'), ('X1', 'Barrel'), ('X2', 'Barrel'), ('X3', 'Barrel'), ('X4', 'Barrel'), ('X5', 'Barrel')])

# # Defining individual CPDs.
cpd_d1 = TabularCPD(variable='D1', variable_card=3, values=d_priors, state_names={'D1': ['S', 'M', 'L']})
cpd_d2 = TabularCPD(variable='D2', variable_card=3, values=d_priors, state_names={'D2': ['S', 'M', 'L']})
cpd_d3 = TabularCPD(variable='D3', variable_card=3, values=d_priors, state_names={'D3': ['S', 'M', 'L']})
cpd_d4 = TabularCPD(variable='D4', variable_card=3, values=d_priors, state_names={'D4': ['S', 'M', 'L']})
cpd_d5 = TabularCPD(variable='D5', variable_card=3, values=d_priors, state_names={'D5': ['S', 'M', 'L']})

print(cpd_d1)
print(cpd_d2)
print(cpd_d3)
print(cpd_d4)
print(cpd_d5)

cpd_x1 = TabularCPD(variable='X1', variable_card=3, values=x_cond_values, evidence=['D1'], evidence_card=[3], state_names={'X1': ['S', 'M', 'L'], 'D1': ['S', 'M', 'L']})
print(cpd_x1)

cpd_x2 = TabularCPD(variable='X2', variable_card=3, values=x_cond_values, evidence=['D2'], evidence_card=[3], state_names={'X2': ['S', 'M', 'L'], 'D2': ['S', 'M', 'L']})
print(cpd_x2)

cpd_x3 = TabularCPD(variable='X3', variable_card=3, values=x_cond_values, evidence=['D3'], evidence_card=[3], state_names={'X3': ['S', 'M', 'L'], 'D3': ['S', 'M', 'L']})
print(cpd_x3)

cpd_x4 = TabularCPD(variable='X4', variable_card=3, values=x_cond_values, evidence=['D4'], evidence_card=[3], state_names={'X4': ['S', 'M', 'L'], 'D4': ['S', 'M', 'L']})
print(cpd_x4)

cpd_x5 = TabularCPD(variable='X5', variable_card=3, values=x_cond_values, evidence=['D5'], evidence_card=[3], state_names={'X5': ['S', 'M', 'L'], 'D5': ['S', 'M', 'L']})
print(cpd_x5)

barrel_probabilities = get_barrel_given_x('./simulated_data.csv')
cpd_barrel = TabularCPD(variable='Barrel', variable_card=2, values=barrel_probabilities, evidence=['X1', 'X2', 'X3', 'X4', 'X5'], evidence_card=[3, 3, 3, 3, 3],
                      state_names={'X1': ['S', 'M', 'L'],
                                   'X2': ['S', 'M', 'L'],
                                   'X3': ['S', 'M', 'L'],
                                   'X4': ['S', 'M', 'L'],
                                   'X5': ['S', 'M', 'L'],
                                   'Barrel': ['No', 'Yes']})
print(cpd_barrel)

# # Associating the CPDs with the network
model.add_cpds(cpd_d1, cpd_d2, cpd_d3,cpd_d4,cpd_d5, cpd_x1, cpd_x2, cpd_x3,cpd_x4,cpd_x5, cpd_barrel)

# check_model checks for the network structure and CPDs and verifies that the CPDs are correctly
# defined and sum to 1.
if not model.check_model():
    print("Model Contains errors!")

from pgmpy.inference import VariableElimination
infer = VariableElimination(model)

print("Probability of B given D1=S, D2=S, D3=S, D4=S, D5=S:")
print(infer.query(['Barrel'], evidence={'D1': 'S', 'D2': 'M', 'D3': 'M', 'D4': 'S', 'D5': 'S'}))

print("Probability of B given D1=S, D2=S, D3=S, D4=S, D5=S:")
print(infer.query(['Barrel'], evidence={'D1': 'S', 'D2': 'S', 'D3': 'S', 'D4': 'S', 'D5': 'S'}))

print("Probability of B given D1=M, D2=M, D3=S, D4=S, D5=M:")
print(infer.query(['Barrel'], evidence={'D1': 'M', 'D2': 'M', 'D3': 'S', 'D4': 'S', 'D5': 'M'}))

print("Probability of B given D1=S, D2=M, D3=M, D4=S, D5=S:")
print(infer.query(['Barrel'], evidence={'D1': 'S', 'D2': 'M', 'D3': 'M', 'D4': 'S', 'D5': 'S'}))

print("Probability of B given D1=M, D2=L, D3=L, D4=M, D5=M:")
print(infer.query(['Barrel'], evidence={'D1': 'S', 'D2': 'M', 'D3': 'M', 'D4': 'S', 'D5': 'S'}))

# check_model checks for the network structure and CPDs and verifies that the CPDs are correctly
# defined and sum to 1.
if not model.check_model():
    print("Model Contains errors!")

from pathlib import Path

Path("./cpts").mkdir(parents=True, exist_ok=True)
cpds = model.get_cpds()
for cpd in cpds:
    with open(f'./cpts/cpt-{cpd.variable}.txt', 'w') as f:
        f.write(str(cpd))


Path("./model").mkdir(parents=True, exist_ok=True)

from pgmpy.readwrite import BIFWriter
writer = BIFWriter(model)
writer.write_bif("./model/barrel_model.bif")

