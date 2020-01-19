import os
import h5py
import time
import pandas as pd
from BMP280 import BMP280

data_folder = 'data'
data_file = 'pressure_BMP280.hdf5'
data_path = './{}/{}'.format(data_folder, data_file)

sensor = BMP280()

# Update the configuration and the control register with the default settings
sensor.set_config()
sensor.set_control()

timestamp = time.time()
press, temp = sensor.get_data()
df = pd.DataFrame([(timestamp, press, temp)], columns=['time', 'pressure', 'temperature'])
df.set_index('time', inplace=True)

if os.path.isdir(data_folder) is False:
    os.mkdir(data_folder)

if os.path.isfile(data_path) is False:
    df.to_hdf(data_path, key='data', mode='w', format='table')
else:
    data = pd.HDFStore(data_path)
    data.append('data', df, format='t',  data_columns=True)
    data.close()
