import binascii, struct, datetime, math, os
from collections import namedtuple
import numpy as np
import pdb
import matplotlib.pyplot as plt
import scipy.io

import read_p

filename = r'C:\FieldTrips\KISSME2017\VMP experiment\UWA_005.p'
#output = read_p.main(filename)

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
                  'PV', 
                  'W_fast',
                  'speed_fast', 'speed_slow',
                  'sh1', 'sh2')

W_fast = output['W_fast']['data_physical']
falling_fast = W_fast > 0.3
W_slow = output['W_slow']['data_physical']
falling_slow = W_slow > 0.3
P_fast = output['P_fast']['data_physical']
shallow_fast = P_fast < 10
P_slow = output['P_slow']['data_physical']
shallow_slow = P_slow < 10

#Now to isolate the individual casts and make one plot per cast
fig = plt.figure()
fig.suptitle(filename, fontsize=14, fontweight='bold')   
fig.set_size_inches(8, 6.0)

ax = plt.subplot(3, 2, 1)
vec = output['sh1']['data_physical']
vec[~falling_fast] = np.nan
vec[shallow_fast] = np.nan
plt.plot(vec, output['P_fast']['data_physical'], 'r')
ax.set_xlabel('Shear 1 and 2')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])

ax = plt.subplot(3, 2, 2)
vec = output['sh2']['data_physical']
vec[~falling_fast] = np.nan
vec[shallow_fast] = np.nan
plt.plot(vec, output['P_fast']['data_physical'], 'k')
ax.set_xlabel('Shear 1 and 2')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])
        
ax = plt.subplot(3, 2, 3)
vec = output['T1_hres']['data_physical']
vec[~falling_fast] = np.nan
vec[shallow_fast] = np.nan
plt.plot(vec, output['P_fast']['data_physical'], 'r')
ax.set_xlabel('T 2')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])

ax = plt.subplot(3, 2, 4)
vec = output['W_fast']['data_physical']
vec[~falling_fast] = np.nan
vec[shallow_fast] = np.nan
plt.plot(vec, output['P_fast']['data_physical'], 'r')
ax.set_xlabel('Fall speed')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])
ax.set_xlim(0, 1.5)

ax = plt.subplot(3, 2, 5)
vec = output['Incl_X']['data_physical']
vec[~falling_slow] = np.nan
vec[shallow_slow] = np.nan
plt.plot(vec, output['P_slow']['data_physical'], 'r')
ax.set_xlabel('Incline X')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])

ax = plt.subplot(3, 2, 6)
vec = output['Incl_Y']['data_physical']
vec[~falling_slow] = np.nan
vec[shallow_slow] = np.nan
plt.plot(vec, output['P_slow']['data_physical'], 'r')
ax.set_xlabel('Incline Y')
ax.set_ylabel('Pressure [dBar]')
ax.set_ylim(ax.get_ylim()[::-1])

fig.show()