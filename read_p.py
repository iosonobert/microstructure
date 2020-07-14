import struct, datetime, math, os, re
import numpy as np
import pdb
import matplotlib.pyplot as plt
import scipy.interpolate as interp
from scipy.signal import butter, lfilter, freqz, lfiltic, filtfilt

combine_channels = 1       #% set to 1 to combine odd/even channels, 0 to leave as is
eol = '\r\n'
bytes_per_word = 2
speed_cutout = 0.05
vehicle = 'vmp'

def read_p(fn):
    
    with open(fn, "rb") as f_in:
    
        data = f_in.read()
    
    print("file open")
    return data
    
def get_header():

    header_format = ("H" #1  file number
                     "H" #2  record number
                     "H" #3  record number other input devices
                     "H" #4  year
                     "H" #5  month
                     "H" #6  day 
                     "H" #7  hour 
                     "H" #8  minute
                     "H" #9  second
                     "H" #10 millisecond
                     "H" #11 Header version
                     "H" #12 Config string size in bytes
                     "H" #13 Product ID
                     "H" #14 build number
                     "H" #15 timezone (mins from UTC)
                     "H" #16 buffer status
                     "H" #17 restarted
                     "H" #18 header size in bytes (128)
                     "H" #19 record size in bytes (header + data)
                     "H" #20 number of records written to the currrent file
                     "H" #21 Truncted frequency of the outbound clock
                     "H" #22 Fractional part of the frequency of the outboud clock (to 0.001 Hz)
                     "H" #23 unused
                     "H" #24 unused
                     "H" #25 unused
                     "H" #26 unused
                     "H" #27 unused
                     "H" #28 unused
                     "H" #29 number of fast columns
                     "H" #30 number of slow columns
                     "H" #31 number of rows in address matrix
                     "d" #32-35 unused
                     "d" #36-39 unused
                     "d" #40-43 unused
                     "d" #44-47 unused
                     "d" #48-51 unused
                     "d" #52-55 unused
                     "d" #56-59 unused
                     "I" #60-61 unused
                     "H" #62 unused
                     "H" #profile = profile: 0 = vertial, 1 = horzontal
                     "H" #Data type (0=unknown, 1=little endian, 2=big endian)
                     )
                     
    return header_format

def cfg_get_section_tags(config_string):
    
    config_string_lines = cfg_read_str(config_string)  
    section_tags = [n for n in range(0, len(config_string_lines)) if (len(config_string_lines[n]) > 0 and config_string_lines[n][0] == '[' and config_string_lines[n][len(config_string_lines[n])-1] == ']')]
    section_tags.append(len(config_string_lines))
    
    return section_tags
    
def cfg_pull_section(config_string, section_name):

    config_string_lines = cfg_read_str(config_string)  
    #section_tags = [n for n in range(0, len(config_string_lines)) if (len(config_string_lines[n]) > 0 and config_string_lines[n][0] == '[' and config_string_lines[n][len(config_string_lines[n])-1] == ']')]
    #section_tags.append(config_string_lines)
    
    section_tags = cfg_get_section_tags(config_string)
    if section_name == 'vmp':
        pass
        #pdb.set_trace()
        
    #print(section_tags)
    if '['+section_name+']' in config_string_lines:
        section_start = [n for n in range(0, len(config_string_lines)) if config_string_lines[n] == '['+section_name+']']
        section_start = section_start[0]
        section_start_i = [n for n in range(0, len(section_tags)) if section_tags[n] == section_start]
        section_start_i = section_start_i[0]        
        section_end = section_tags[section_start_i+1]
        
        return config_string_lines[section_start:section_end]
        
    else:
        print("Did not find the section")
        return ""
    
def cfg_read_str(config_string):
    
    #Split string
    if '\r\n' in config_string:
        eolu = '\r\n'
    elif '\n' in config_string:
        eolu = '\n'
    else:
        eolu = eol
        
    config_string_lines = config_string.split(eolu)
    config_string_lines = [config_string_line.strip() for config_string_line in config_string_lines]
    #print(config_string_lines)
    
    return config_string_lines

def cfg_get_root(config_string):
        
    root = cfg_pull_section(config_string, 'root')
    if root == '':
        section_tags = cfg_get_section_tags(config_string)
        config_string_lines = cfg_read_str(config_string)
        root = config_string_lines[0:section_tags[0]]
    
    root_dict = cfg_rows2dict(root)
    return root_dict
    
def cfg_interpret_matrix(config_string, asvector = False):
    
    matrix = cfg_pull_section(config_string, 'matrix')
    #rows = len(matrix)
    
    matrix_interp = []
    
    expected = 1
    for row in matrix:
        rownumstr = row[3:5]
        try:
            if expected == int(rownumstr):
                split_row = row[6:].split()
                split_row = [int(split_row_ent) for split_row_ent in split_row]
                matrix_interp.append(split_row)
                expected += 1   
            else:
                print('Bad row')
                
        except Exception as err:
            print(str(err))
            pass
    
    if asvector:
        matrix_vector_interp = []
        for row in matrix_interp:
            matrix_vector_interp += row
            
        matrix_interp = matrix_vector_interp
        
    return np.array(matrix_interp)
    
def cfg_section_dict(config_string, section):
    
    section = cfg_pull_section(config_string, section)
    
    section_dict = cfg_rows2dict(section)
    
    return section_dict

def cfg_rows2dict(rows):
    
    section_dict = {}
    
    for row in rows:
        row = row.strip()
        if len(row) > 0 and row[0] ==';':
            continue
        
        if len(row) > 0 and '=' in row:
            equal_i = [n for n in range(0, len(row)) if row[n] == '=']
            equal_i = equal_i[0]
            #print row[0:equal_i] + ' = ' + row[equal_i+1:]
            section_dict[row[0:equal_i].lower().strip()] = row[equal_i+1:]
            
    return section_dict
     
def cfg_find_channels(config_string):
    
    section_tags = cfg_get_section_tags(config_string)
    config_string_lines = cfg_read_str(config_string)

    tags =  [config_string_lines[n] for n in section_tags[0:-1]]
    print(tags) 
    
    channels = []
    for tag in tags:
        section_dict = cfg_section_dict(config_string, tag[1:-1])
        if type(section_dict) is None:
            continue
        
        if section_dict.has_key('id') and section_dict.has_key('name') and section_dict.has_key('type'):
            channels.append(tag[1:-1])
    
    return channels
    
def ini_parse(ini_file, vehicle):
    
    with open(ini_file) as fo:
        dvpstr = fo.read()
    
    vehicle_info = cfg_section_dict(dvpstr, vehicle)

    return vehicle_info
    
def calibrate(section_dict):
    
    if section_dict["type"].lower() == 'accel':
        required_parameters = ('coef0', 'coef1')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        section_dict["data_physical"] = 9.81*(section_dict["data"] - float(section_dict['coef0']))/float(section_dict['coef1'])
    elif section_dict["type"].lower() == 'gnd':        
        required_parameters = ()
        calibrate_parmeter_check(section_dict, required_parameters)
        
        section_dict["data_physical"] = section_dict["data"] 
    elif section_dict["type"].lower() == 'shear':
        required_parameters = ('adc_fs', 'adc_bits', 'sens', 'diff_gain')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        if not section_dict.has_key("adc_zero"):
            section_dict["adc_zero"] = 0
        if not section_dict.has_key("sig_zero"):
            section_dict["sig_zero"] = 0
            
        cluster = float(section_dict["adc_fs"])/(math.pow(2, float(section_dict["adc_bits"])))
                
        numerator = section_dict["data"]*cluster - float(section_dict["adc_zero"]) - float(section_dict["sig_zero"])
        denominator = 2*math.sqrt(2)*float(section_dict["diff_gain"])*float(section_dict["sens"])
        
        section_dict["data_physical"] = numerator / denominator
        
    elif section_dict["type"].lower() == 'therm':
        
        required_parameters = ('adc_fs', 'adc_bits', 't_0', 'g', 'a', 'b', 'e_b')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        Z1 = (section_dict["data"] - float(section_dict["a"]))/(float(section_dict["b"]))
        Z2 = float(section_dict["adc_fs"])/(math.pow(2, float(section_dict["adc_bits"])))
        Z3 = 2/(float(section_dict["g"])*float(section_dict["e_b"]))
        
        Z = Z1*Z2*Z3
        
        Rt_on_R0 = (1 - Z)/(1 + Z)
        log_Rt_on_R0 = np.log(Rt_on_R0)
        
        if section_dict.has_key("beta"):
            series = (1/float(section_dict["t_0"])) + (1/float(section_dict["beta"]))*log_Rt_on_R0
        elif section_dict.has_key("beta_1"):
            series = (1/float(section_dict["t_0"])) + (1/float(section_dict["beta_1"]))*log_Rt_on_R0
            if section_dict.has_key("beta_2"):
                series = series + 1/float(section_dict["beta_2"])*np.power(log_Rt_on_R0, 2)
                if section_dict.has_key("beta_3"):
                    series = series + 1/float(section_dict["beta_3"])*np.power(log_Rt_on_R0, 3)
        else:
            series = Rt_on_R0
            
        section_dict["data_physical"] = 1/series - 273.15
    elif section_dict["type"].lower() == 'voltage':
        required_parameters = ('adc_fs', 'adc_bits', 'g')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        if not section_dict.has_key("adc_zero"):
            section_dict["adc_zero"] = 0
            
        cluster = float(section_dict["adc_fs"])/(math.pow(2, float(section_dict["adc_bits"])))
                
        section_dict["data_physical"] = (section_dict["data"]*cluster - float(section_dict["adc_zero"]))/float(section_dict["g"])
                
    elif section_dict["type"].lower() == 'poly':
        physical = np.zeros(len(section_dict['data']))
        
        for n in range(0, 10):
            print('{0:02.0f}'.format(n))
            try:
                coeff = float(section_dict['coef{0:01.0f}'.format(n)])
                if coeff == 0:
                    print('coeff{0:01.0f} is zero, skipping'.format(n))
                    continue
                
                physical += coeff*np.power(section_dict["data"], n)
                print('success')
            except:
                print('failed')

        section_dict["data_physical"] = physical      
        
    elif section_dict["type"].lower() == 'inclxy':
        
        N = calibrate_adis(section_dict["data"])
        required_parameters = ('coef0', 'coef1')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        section_dict["data_physical"] = float(section_dict['coef0']) + N*float(section_dict['coef1'])

    elif section_dict["type"].lower() == 'inclt':
        
        N = calibrate_adis(section_dict["data"])
        required_parameters = ('coef0', 'coef1')
        calibrate_parmeter_check(section_dict, required_parameters)
        
        section_dict["data_physical"] = float(section_dict['coef0']) + N*float(section_dict['coef1'])
        
    else:
        raise(Exception("Channel type error", "This is not a recognised type"))
        
    if type(section_dict["data_physical"]) == type(0) or not len(section_dict["data_physical"]) == len(section_dict["data_physical"]):
        section_dict.pop('data_physical')
        print('removed physical') 
        
    return section_dict

def calibrate_parmeter_check(section_dict, required_parameters):
    
    for required_parameter in required_parameters:
        
        if not section_dict.has_key(required_parameter):
            
            print(section_dict)
            print(required_parameter)
            raise(Exception("Key error", "This section is missing a required parameter"))
    
def calibrate_adis(data):
            
    n = data < -np.power(2, 14) # these data points have the MS-bit set and are new.
    data[n] = data[n] + np.power(2, 15) # shift to clear MS-bit
    
    n = data >= np.power(2, 14) # Second MS-bit is set, which indicates an error. 
    data[n] = data[n] - np.power(2, 14) # shift to clear MS-bit
    
    # The data are 2s-compliment for inclination. So we find the upper half of the 
    # 14-bit range. This is the data with negative values. So we shift it down
    # to get a proper 2s-compliment conversion. The temperature data is 12-bit
    # only and will automatically not get shifted.
    n = data >= np.power(2, 13)
    data[n] = data[n] - np.power(2, 14)

    return data

def interp1d_opt(fast_vector, slow_vector):
    
    if len(slow_vector) == len(fast_vector):
        print('Fast and slow are equal in length, no interp needed')
        return slow_vector
    
    generation = 2
    if generation == 1:
        f1 = 1/float(len(slow_vector))
        t_npe = np.arange(0, 1, f1)  
        fm = np.max(t_npe)
        f2 = fm/float(len(fast_vector))
        t_pe = np.arange(0, fm, f2)
    elif generation == 2:
        fs = 1
        ratio = float(len(slow_vector))/float(len(fast_vector))
        t_new = np.arange(0, len(fast_vector), 1)
#        t = np.arange(0, t_new[-1:]+fs-fs/ratio, fs/ratio)
#        t = np.arange(0, t_new[-1:], fs/ratio)
        t = np.linspace(0, t_new[-1:], len(slow_vector))
        t_npe = t
        t_pe = t_new
#        pdb.set_trace()
#    
#    pdb.set_trace()
    f = interp.interp1d(t_npe, slow_vector)
    X_data = f(t_pe)   
    
    if not len(X_data) == len(fast_vector):
        pdb.set_trace()
    
    return X_data
    
def deconvolve(X_dX, X, rate):
    
    bf_order = 1
    nyq = rate/2
    cutoff = 1/(2*np.pi*float(X_dX['diff_gain']))
    normal_cutoff = cutoff / nyq
    
    # interp1 if needed
    X_dX_data = X_dX['data']
    X_data = interp1d_opt(X_dX['data'], X['data'])
        
    # lowpass butterworth filter
    b, a = butter(bf_order, normal_cutoff, btype='low', analog=False)
    
    # initial condition for butterworth
    #zi = np.take(non_pre_emph_hires[0], [0], axis=0)
    
    zi = lfiltic(b, a, X_data, x = X_dX_data)
    X_hires_data, zf = lfilter(b, a, X_dX['data'], zi = zi)
    
#    plt.figure()
#    plt.plot(X_hires_data)
    
    if len(X_data) > 1:
        print('Not doing the second fit as yet')
        pass
        try:
            pc = np.polyfit(X_hires_data, X_data, 1)
        except:
            pdb.set_trace()   
            
        pc2 = [2-pc[0], -pc[1]];
        
        initialOutput = np.polyval(pc2, X_data);
        zi = lfiltic(b, a, initialOutput, x = X_dX_data)
        X_hires_data, zf = lfilter(b, a, X_dX['data'], zi = zi)
        X_hires_data = np.polyval(pc, X_hires_data);
    
    X_hires = {}
    X_hires['name'] = X['name'] + '_hres'
    X_hires['data'] = X_hires_data
    for key in X.keys():
        if key == 'name' or key == 'data':
            continue
        X_hires[key] = X[key]
    
    if X['name'] == 'P':
        #pdb.set_trace()
        pass
    
    return X_hires    
    
def main(fn):
    
    print('***THE CONCEPT OF ODD AND EVEN CHANNELS HAS NOT BEEN IMPLEMENTED, FIX THIS IN THE FUTURE***')
    
    data = read_p(fn)
    file_size = len(data)
    
    header_format = get_header()
                     
    header_size = struct.calcsize(">" + header_format)
    
    # Start offset at zero and read the header
    offset = 0
    header = struct.unpack(">" + header_format, data[offset:offset+header_size])
    
    # Advance offset by header size   
    offset += header_size

    # Read config string and advance offset by config string size    
    config_string_size = header[11]
    config_string = data[offset:offset+config_string_size]
    offset += config_string_size
    first_record_size = header_size + config_string_size
    
    #cfg_section_dict_by_ID(config_string, 1)
    channels = cfg_find_channels(config_string)
    
    # Get record size etc. 
    record_size = header[18]
    n_records = header[19]
    f_clock = float(header[20]) + float(header[21])/1000
    fast_cols = header[28]
    slow_cols = header[29]
    n_cols = fast_cols + slow_cols
    n_rows = header[30]
    n_matrix = n_rows * n_cols
    data_size = record_size - header_size
    fs_fast = f_clock/n_cols
    fs_slow = fs_fast/n_rows
    
    # root stuff
    root = cfg_get_root(config_string)
    rate = float(root['rate'])
    recsize = float(root['recsize'])
    
    # Config Matrix stuff
    matrix_sing = cfg_interpret_matrix(config_string, asvector = True)
    matrix_sweeps_per_record = (data_size/2) /  n_matrix
    matrix = np.tile(matrix_sing, (1, matrix_sweeps_per_record)).T
    
    time_diff_vector = np.tile(np.arange(0.0, recsize, recsize/rate).T, (n_cols, 1))
    time_diff_vector = time_diff_vector.T.reshape(n_cols*rate)
        
    # Number of records
    n_records = (file_size - first_record_size)/(record_size)
    n_records_p = (float(file_size) - float(first_record_size))/float(record_size)
    matrix_count = np.floor((file_size - first_record_size - n_records * header_size) / (n_rows * n_cols * bytes_per_word))
    t_slow = np.arange(0, matrix_count)/fs_slow
    t_fast = np.arange(0, matrix_count*n_rows)/fs_fast

    # 
    all_vectors = np.zeros((n_rows*n_cols*matrix_sweeps_per_record, n_records))
    all_indices = np.zeros((n_rows*n_cols*matrix_sweeps_per_record, n_records))
    all_times = np.zeros((n_rows*n_cols*matrix_sweeps_per_record, n_records)).astype('datetime64[us]')
    
    print("Header digested, reading records")
    for n in range(0, n_records):
    
        next_header = struct.unpack(">" + header_format, data[offset:offset+header_size])
        dto = datetime.datetime(next_header[3], next_header[4], next_header[5], next_header[6], next_header[7], next_header[8], next_header[9]/1000)
        
        offset += header_size
        next_data = struct.unpack(">" + "h"*(data_size/2), data[offset:offset+data_size])
        offset += data_size

        m1 = np.array(next_data)

        all_vectors[0:m1.size, n] = np.reshape(m1, m1.size, 1)
        all_indices[:, n] = matrix.squeeze()        
        all_times[:, n] = np.datetime64(dto, dtype = '<M8[us]') + time_diff_vector.squeeze().astype('timedelta64[us]')
                 
    all_indices = all_indices.T
    all_vectors = all_vectors.T
    all_times = all_times.T
        
    print("Reading complete, calculating time and calibrating")
    
    output = {}
    output['channels'] = channels
    output['config_string'] = config_string
    
    output['all_indices'] = all_indices
    output['all_vectors'] = all_vectors
    output['all_times'] = all_times
    
    ## t_fast and t_slow
    section_names = []
    for channel in channels:
        section_dict = cfg_section_dict(config_string, channel)
         
        channel_id = int(section_dict['id'])
        channel_i = all_indices == channel_id
        channel_data = all_vectors[channel_i]
        channel_data = channel_data.reshape(channel_data.size)
        
        channel_time = all_times[channel_i]
        channel_time = channel_time.reshape(channel_data.size)
        
        section_dict['data'] = channel_data
        section_dict['time'] = channel_time
        output[section_dict['name']] = section_dict
        
        section_names.append(section_dict['name'])
    
    ## Deconvolution
    for section_name in section_names:
        
        section_dict = output[section_name]
        if not section_dict.has_key('diff_gain'):
            print("{0} has no diff_gain property, skippping".format(section_name))
            continue
        
        if section_dict['type'] == 'shear' or section_dict['type'] == 'xmp_shear':
            print("{0} is a shear measurement, skippping".format(section_name))
            continue
        
        res = re.match('(.*)_d(.*?)', section_name)
        if res:
            print("{0} is a fast column".format(section_name))
            would_be_slow_name = res.groups()[0]
        else:
            print "{0} is not a fast column, skipping".format(section_name)
            continue
                    
        if would_be_slow_name in section_names:
            print("{0} has a non-preemphasised column, deconvolve".format(section_name))
        else:
            print("{0} has no non-preemphasised column, skipping for now but this is still possible to process".format(section_name))
            continue
        
        id_here = int(section_dict['id'])
        count_here = np.sum(matrix_sing == id_here)
        rate_here = rate * count_here / n_rows
        deconv = deconvolve(output[section_name], output[would_be_slow_name], rate_here)
        output[deconv['name']] = deconv
        section_names.append(deconv['name'])
        channels.append(deconv['name'])
        output['channels'] = channels
    
    ## Conversion
    # Convert all
    for section_name in section_names:
    
        section_dict = output[section_name]
        try:
            section_dict = calibrate(section_dict)
            print('Calibrated {0}'.format(section_name))
            
        except:
            print('Failed in calibrating {0}'.format(section_name))
            pass
    
    # Fast and slow columns
    for section_name in section_names:

        res = re.match('(.*)_hres', section_name)
        if res:
            print("{0} is a hres column, popping it (Spirit of JSC)".format(section_name))
        else:
            continue
        
        fast_name = res.groups()[0] + '_fast'
        slow_name = res.groups()[0] + '_slow'
        
        hres_col = output[section_name]['data_physical']
        fast_col = interp1d_opt(t_fast, hres_col)
        slow_col = interp1d_opt(t_slow, hres_col)
        
        #output.pop(section_name)
        output[fast_name] = {}
        output[slow_name] = {}
        output[fast_name]['name'] = fast_name
        output[slow_name]['name'] = slow_name
        output[fast_name]['data_physical'] = fast_col
        output[slow_name]['data_physical'] = slow_col
        
        section_names.append(fast_name)
        section_names.append(slow_name)
                
    print('***ASSUMING VMP, FIX THIS IN THE FUTURE***')
    print('***ODAS ATTEMT TO TAKE THIS FROM ROOT AND FAILING THAT ASSUME VMP***')
    
    ## Hotel file
    print('***HAVE DONE NOTHING WITH THE HOTEL FILE, FIX THIS IN THE FUTURE***')
    
    ## Temperature
    print('***HAVE DONE NOTHING WITH THE TEMPERATURE, FIX THIS IN THE FUTURE***')
    
    ## Fall rate
    vi = ini_parse('default_vehicle_attributes.ini', vehicle)
    if not output.has_key('W_slow') and output.has_key('P_slow'):
        
        W_slow = np.gradient(output['P_slow']['data_physical'], 1/fs_slow)
        [b, a] = butter(1, (0.68/float(vi['tau']))/(fs_slow/2))
        W_slow = filtfilt(b, a, W_slow)
        
        W_fast = np.gradient(output['P_fast']['data_physical'], 1/fs_fast)
        [b, a] = butter(1, (0.68/float(vi['tau']))/(fs_fast/2))
        W_fast = filtfilt(b, a, W_fast)
        
        output['W_fast'] = {}
        output['W_slow'] = {}
        output['W_fast']['name'] = 'W_fast'
        output['W_slow']['name'] = 'W_slow'
        output['W_fast']['data_physical'] = W_fast
        output['W_slow']['data_physical'] = W_slow
        
    else:
        #pdb.set_trace()
        raise(Exception('Ahhhhhhh you muffed it!. Still need to convert *_hres to *_fast and *_slow'))
        
    ## Speed
    print('***ONLY DONG SPEED FROM PRESSURE, FIX THIS IN THE FUTURE***')
    if vi['speed_algorithm'].lower().strip() == 'pressure':
       speed_fast = abs(output['W_fast']['data_physical'])
       speed_slow = abs(output['W_slow']['data_physical'])
    else:
        raise(Exception('Carn this isn''t implemented yet'))
        
    # Smooth speed
    # Vehicle specific smoothing of the speed vector.
    [b,a] = butter(1, (0.68/float(vi['tau'])/(fs_slow/2)))
    speed_slow = filtfilt(b, a, speed_slow)
    [b,a] = butter(1, (0.68/float(vi['tau'])/(fs_fast/2)))
    speed_fast = filtfilt(b, a, speed_fast)

    # Fish out the speeds that are smaller then the cutout of speed_cutout
    # to avoid singularities.
    speed_slow[speed_slow < abs(speed_cutout)] = abs(speed_cutout)
    speed_fast[speed_fast < abs(speed_cutout)] = abs(speed_cutout)
    output['speed_fast'] = {}
    output['speed_slow'] = {}
    output['speed_slow']['name'] = 'speed_slow'
    output['speed_fast']['name'] = 'speed_fast'
    output['speed_slow']['data_physical'] = speed_slow
    output['speed_fast']['data_physical'] = speed_fast
    
    ## Shear
    if output.has_key('sh1'):
        output['sh1']['data_physical'] = output['sh1']['data_physical']/np.power(speed_fast, 2)
        
    if output.has_key('sh2'):
        output['sh2']['data_physical'] = output['sh2']['data_physical']/np.power(speed_fast, 2)
    
    ## Gradients
    print('***IVE DONE A HACK JOB OF THE GRADIENTS, FIX THIS IN THE FUTURE***')
    gradT1 = fs_fast*np.insert(np.diff(output['T1_fast']['data_physical']), 0, 0)/output['speed_fast']['data_physical']
    gradT1[0] = gradT1[1]
    output['gradT1'] = {}
    output['gradT1']['name'] = 'gradT1'
    output['gradT1']['data_physical'] = gradT1
    
    gradT2 = fs_fast*np.insert(np.diff(output['T2_fast']['data_physical']), 0, 0)/output['speed_fast']['data_physical']
    gradT2[0] = gradT2[1]
    output['gradT2'] = {}
    output['gradT2']['name'] = 'gradT2'
    output['gradT2']['data_physical'] = gradT2
        
    return output

def print_imgs(output):
    
    path, filename = os.path.split(fn)
    filename_list = filename.split('.')
    filename_ne = filename_list[0]
    
    channels = output['channels']
    config_string = output['config_string']
    all_indices = output['all_indices']
    all_vectors = output['all_vectors']
    all_times = output['all_times']
    
    for channel in channels:
        section_dict = cfg_section_dict(config_string, channel)
         
        channel_id = int(section_dict['id'])
        channel_i = all_indices == channel_id
        channel = all_vectors[channel_i]
        channel = channel.reshape(channel.size)
        
        channel_time = all_times[channel_i]
        channel_time = channel_time.reshape(channel.size)
        
        fig = plt.figure()
        fig.suptitle(section_dict['name'], fontsize=14, fontweight='bold')
        
        plt.plot(channel_time, channel)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(top=0.85)
        ax.set_title('Raw ' + section_dict['name'])
        
        ax.set_xlabel('time')
        ax.set_ylabel(section_dict['name'])
        
        savename = filename_ne + '_' + section_dict['name'] + '_raw.png'
        fig.savefig(savename)
        plt.close(fig)
        print("plotted")
        
        ##
        
        section_dict['data'] = channel
        section_dict['time'] = channel_time
        output[section_dict['name']] = section_dict
        
        print(section_dict["type"])
        try:
            
            fig = plt.figure()
            fig.suptitle(section_dict['name'], fontsize=14, fontweight='bold')
            
            plt.plot(channel_time, channel)
            ax = fig.add_subplot(111)
            fig.subplots_adjust(top=0.85)
            ax.set_title(section_dict['name'])
            
            ax.set_xlabel('time')
            ax.set_ylabel(section_dict['name'])
            
            savename = filename_ne + '_' + section_dict['name'] + '.png'
            fig.savefig(savename)
            plt.close(fig)
            print("plotted")
            
        except:
            pass
#
#filename = r'NWS_N4C_004.p'
#filename = r'UWA_000.P'
#output = main(filename)

