import os
import h5py
import time
import pandas as pd
from BMP280 import BMP280

sensor = BMP280()

# Read the trimming parameters from the NVM
print('Reading trimming parameters')
temp_coeffs = sensor.get_temperature_coefficients()
pres_coeffs = sensor.get_pressure_coefficients()

# Update the configuration and the control register with the default settings
sensor.set_config()
sensor.set_control()

timestamp = time.time()
press, temp = sensor.get_data()
df = pd.DataFrame([(timestamp, press, temp)], columns=['time', 'pressure', 'temperature'])

df.to_hdf('./data/data.hdf5', key='data', mode='w')

