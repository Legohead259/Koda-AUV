from pgmpy.readwrite import BIFReader
import numpy as np
import pandas as pd
from pgmpy.inference import VariableElimination
import os
from services.run_inferrence import get_barrel_belief

SM_CUTOFF= 0.80
ML_CUTOFF = 1.2
L_CUTOFF = 3
def convert_to_label(x):
    if x >= ML_CUTOFF:
        return 'L'
    elif x >= SM_CUTOFF:
        return 'M'
    else:
        return 'S'

def belief(readings, model):
    np_readings = np.array(readings).astype(float)
    if len(np_readings) != 5:
        raise Exception("Invalid input format")

    labeledReadings = [convert_to_label(d) for d in np_readings]
    
    infer = VariableElimination(model)
    
    # print("Inferring...")
    # Consider readings in order [D1, D2, D3, D4, D5]
    return infer.query(['Barrel'], evidence={'D1': labeledReadings[0], 'D2': labeledReadings[1], 'D3': labeledReadings[2], 'D4': labeledReadings[3], 'D5': labeledReadings[4]})

def main():
    # print("Loading model...")
    # reader = BIFReader("./model/barrel_model.bif")
    # model = reader.get_model()
    # print(reader.get_states())
    # belief_map = belief([1.0, 2.0, 2.0, 1.0, 1.0], model)
    # print(belief_map.get_value(Barrel='Yes'))
    # print(belief_map.get_value(Barrel='No'))
    get_barrel_belief([1.0, 2.0, 2.0, 1.0, 1.0])

if __name__ == "__main__":
    main()