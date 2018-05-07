import binascii, struct, datetime, math, os
from collections import namedtuple
import numpy as np
import pdb
import matplotlib.pyplot as plt
import scipy.io

import read_p

filename = r'C:\FieldTrips\KISSME2017\VMP experiment\UWA_005.p'
output = read_p.main(filename)

matfile = scipy.io.loadmat(r'C:\FieldTrips\KISSME2017\VMP experiment\UWA_005.mat')

matfile['V_Bat'] = matfile.pop('V_Bat')
##
print ''
print ''
print ''
print ''

#start with ax
not_even_close = () # involve deconvolution
validate = True
params = ('Ax', 'Ay', 'Gnd', 'Incl_T', 'Incl_X', 'Incl_Y', 'V_Bat', 
                  'T2', 'T2_dT2', 'T2_fast', 
                  'P' , 'P_dP'  , 'P_fast', 
                  'T1', 'T1_dT1', 'T1_fast', 
                  'gradT1', 'gradT2',
                  'PV', 
                  'W_fast',
                  'speed_fast', 'speed_slow',
                  'sh1', 'sh2')
for param in params:
    mat_vec = np.around(matfile[param].squeeze(), decimals = 2)
    pyp = output[param]
    
    ## some fields, particularly derived ones, may not have both data and data_physical
    #  fields
    has_np = pyp.has_key('data')
    if has_np:
        py_vecnp = np.around(pyp['data'].squeeze(), decimals = 2)
        cnp = py_vecnp == mat_vec
        
    if not pyp.has_key('data_physical'):
        if len(cnp) > 1 and cnp.all():
            print('{0} matches in non-physical units'.format(param))
            continue
        else: 
            print('{0} appears to have a problem with calbration or cdeconvolution'.format(param))
            continue
        
    py_vec = np.around(pyp['data_physical'].squeeze(), decimals = 2)
    c = py_vec == mat_vec
    validate_needed = False
    if len(c) > 1 and c.all():
        print('{0} is good'.format(param))
    else:
        diff_vec = np.abs(py_vec - mat_vec)
        diff_vec_perc = 100 * diff_vec / mat_vec
        if max(diff_vec) < 0.015:
            if validate:
                print('{0} is OK, check plot'.format(param))
                validate_needed = True
            else:
                print('{0} is OK, turn validation on to check plot'.format(param))
        elif cnp.all():
            print('{0} matches in non-physical units'.format(param))
        else:
            print('{0} is bad'.format(param))
            validate_needed = True
    
    if validate and validate_needed:
        fig = plt.figure()
        fig.suptitle('Validation', fontsize=14, fontweight='bold')        
        plt.plot(py_vec, 'r')
        plt.plot(mat_vec)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(top=0.85)
        ax.set_title('Converted ' + pyp['name'])        
        ax.set_xlabel('time')
        ax.set_ylabel(pyp['name'])
        plt.show()

        fig = plt.figure()
        fig.suptitle('Validation', fontsize=14, fontweight='bold')        
        plt.plot(py_vec, 'k')
        ax = fig.add_subplot(111)
        fig.subplots_adjust(top=0.85)
        ax.set_title('Error perentage on converted ' + pyp['name'])        
        ax.set_xlabel('time')
        ax.set_ylabel('%')
        
        if param == 'T1':
            pdb.set_trace()
            
print("Done")