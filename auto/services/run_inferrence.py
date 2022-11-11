import numpy as np
from pgmpy.inference import VariableElimination
from . import reader, model

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

def get_barrel_belief(readings):
    # print(reader.get_states()) # Debug
    belief_map = belief(readings, model)
    print(belief_map.get_value(Barrel='Yes')) # Debug
    print(belief_map.get_value(Barrel='No')) # Debug
    return (belief_map.get_value(Barrel='Yes'), belief_map.get_value(Barrel='No'))