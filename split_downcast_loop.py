import binascii, struct, datetime, math, os
from collections import namedtuple
import numpy as np
import pdb
import matplotlib.pyplot as plt
import scipy.io

import read_p

fullpath_nf = r'C:\FieldTrips\KISSME2017\VMP experiment\UWA_{0:03.0f}.p'

for fn in range(0, 43):
    
    fullpath = fullpath_nf.format(fn)
    directory, filename = os.path.split(fullpath)
    filestub, fileext = filename.split('.')
    
    if not os.path.exists(fullpath):
        continue
    
    output = read_p.main(fullpath)
        
    print ''
    print ''
    print ''
    print ''
    
    W_fast = output['W_fast']['data_physical']
    falling_fast = W_fast > 0.3
    W_slow = output['W_slow']['data_physical']
    falling_slow = W_slow > 0.3
    P_fast = output['P_fast']['data_physical']
    shallow_fast = P_fast < 10
    P_slow = output['P_slow']['data_physical']
    shallow_slow = P_slow < 10
    
    keep_fast = np.logical_and(falling_fast, ~shallow_fast)
    keep_slow = np.logical_and(falling_slow, ~shallow_slow)
    
    if not keep_fast.any():
        continue
    
    P_fast_vec = output['P_fast']['data_physical'][keep_fast]
    P_slow_vec = output['P_slow']['data_physical'][keep_slow]
    
    plt.figure()
    plt.plot(P_fast_vec)
    plt.show()
    
    P_max = np.max(P_fast_vec)
    
    ## Split casts
    cast_start_fast = [n for n in range(0, len(P_fast_vec)-1) if P_fast_vec[n]-P_fast_vec[n+1] > 0.7*P_max]
    cast_start_fast = np.array(cast_start_fast) + 1
    cast_stop_fast = cast_start_fast + 0
    cast_start_fast = np.insert(cast_start_fast, 0, 0)
    cast_stop_fast = np.append(cast_stop_fast, np.array(len(P_fast_vec)))
    
    cast_start_slow = [n for n in range(0, len(P_slow_vec)-1) if P_slow_vec[n]-P_slow_vec[n+1] > 0.7*P_max]
    cast_start_slow = np.array(cast_start_slow) + 1
    cast_stop_slow = cast_start_slow + 0
    cast_start_slow = np.insert(cast_start_slow, 0, 0)
    cast_stop_slow = np.append(cast_stop_slow, np.array(len(P_slow_vec)))
    
    
    n_casts = (len(cast_start_fast))
    
    fig = plt.figure()
    fig.suptitle(filename, fontsize=14, fontweight='bold')   
    fig.set_size_inches(8, 8) 
    ax = plt.subplot(1, 1, 1)
    plt.plot(P_fast_vec, 'b')
    cols = ('r', 'k', 'g') * 100
    for n in range(0, n_casts):
        dup_vec = P_fast_vec + 0
        #plt.plot(P_fast_vec[cast_start_fast[n]:cast_stop_fast[n]], cols[n])
        plt.plot(np.arange(cast_start_fast[n], cast_stop_fast[n], 1), P_fast_vec[cast_start_fast[n]:cast_stop_fast[n]], cols[n])
    
    
    save_name = filestub + '_CastDiagram.png'
    fig.savefig(os.path.join(directory, save_name))
    print('Saved ' + save_name)
        
    for n in range(0, n_casts):
    
        #Now to isolate the individual casts and make one plot per cast
        fig = plt.figure()
        fig.suptitle(filename, fontsize=14, fontweight='bold')   
        fig.set_size_inches(8, 8)
        
        ax = plt.subplot(4, 2, 1)
        plt.plot(output['sh1']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 
                 output['P_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 'k', lw = 0.5)
        ax.set_xlabel('Shear 1')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        ax = plt.subplot(4, 2, 2)
        plt.plot(output['sh2']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 
                 output['P_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 'k', lw = 0.5)
        ax.set_xlabel('Shear 2')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
                
        ax = plt.subplot(4, 2, 3)
        plt.plot(output['T1_hres']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 
                 output['P_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 'k', lw = 0.5)
        ax.set_xlabel('T 2')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        ax = plt.subplot(4, 2, 4)
        plt.plot(output['W_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 
                 output['P_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]], 'k', lw = 0.5)
        ax.set_xlabel('Fall speed')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_xlim(0, 1.5)
        
        ax = plt.subplot(4, 2, 5)
        plt.plot(output['Incl_X']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 
                 output['P_slow']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 'k', lw = 0.5)
        ax.set_xlabel('Incline X')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        ax = plt.subplot(4, 2, 6)
        plt.plot(output['Incl_Y']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 
                 output['P_slow']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 'k', lw = 0.5)
        ax.set_xlabel('Incline Y')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        ax = plt.subplot(4, 2, 7)
        plt.plot(output['gradT1']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 
                 output['P_slow']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 'k', lw = 0.5)
        ax.set_xlabel('dT1/dz')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        ax = plt.subplot(4, 2, 8)
        plt.plot(output['gradT2']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 
                 output['P_slow']['data_physical'][keep_slow][cast_start_slow[n]:cast_stop_slow[n]], 'k', lw = 0.5)
        ax.set_xlabel('dT2/dz')
        ax.set_ylabel('Pressure [dBar]')
        ax.set_ylim(ax.get_ylim()[::-1])
        
        save_name = filestub + '_QuickPlot_Cast{0:0.0f}.png'.format(n)
        plt.tight_layout()
        fig.savefig(os.path.join(directory, save_name))
        print('Saved ' + save_name)
        
    order_for_fft = 12
    npoints = np.power(2, order_for_fft)
    
    activity = []
    depths = []
    for n in range(0, n_casts):
        sh1 = output['sh1']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]]
        P = output['P_fast']['data_physical'][keep_fast][cast_start_fast[n]:cast_stop_fast[n]]
        start_point = 0
        end_point = start_point + npoints
        while end_point < len(sh1):
            activity.append(np.var(sh1[start_point:end_point]))
            depths.append(np.mean(P[start_point:end_point]))
            
            start_point += npoints
            end_point += npoints
            pass
    
    activity = np.array(activity)
    depths = np.array(depths)
    
    fig = plt.figure()
    fig.suptitle(filename, fontsize=14, fontweight='bold')   
    fig.set_size_inches(8, 8)
    
    ax = plt.subplot(1, 1, 1)
    plt.plot(activity, 
             depths, 'r')
    ax.set_xlabel('var(Shear 1)')
    ax.set_ylabel('Pressure [dBar]')
    ax.set_ylim(ax.get_ylim()[::-1])
    
    save_name = filestub + '_Sh1Variance.png'
    fig.savefig(os.path.join(directory, save_name))
    print npoints
        