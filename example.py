from BMP280 import BMP280
import time
import matplotlib.pyplot as plt     
        
sensor = BMP280()

# Read the trimming parameters from the NVM
print('Reading trimming parameters')
temp_coeffs = sensor.get_temperature_coefficients()
pres_coeffs = sensor.get_pressure_coefficients()

# Update the configuration and the control register with the default settings
sensor.set_config()
sensor.set_control()

# Define the size of the window which will be plotted (in number of samples)
window = 200

# Define number of samples before stopping
num_samples = 1000

# Collect and display pressure and temperature samples
temperature = []
pressure = []
for i in range(num_samples):

    # Read all data registers (burst read)
    data = sensor.get_adc()

    # Convert the ADC values to pressure and temperature
    temp, _ = sensor.convert_adct(data[1], temp_coeffs)
    pres = sensor.convert_adcp(data[0], data[1], pres_coeffs, temp_coeffs)

    # Append data
    temperature.append(temp)
    pressure.append(pres)

    # If enough samples are collected start visualizing the data
    if i == window:
        plt.ion()
        fig = plt.figure()
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
        
        line1, = ax1.plot(range(window + 1), pressure, 'b-')
        line2, = ax2.plot(range(window + 1), temperature, 'r-')
        
        ax1.set_ylabel('Pressure [hPa]')
        ax2.set_ylabel('Temperature [degC]')
        
    elif i > window:
        start = window + 1
        line1.set_ydata(pressure[-window - 1:])
        line2.set_ydata(temperature[-window - 1:])
        
        ax1.set_ylim(min(pressure[-start:]), max(pressure[-start:]))
        ax2.set_ylim(min(temperature[-start:]), max(temperature[-start:]))

        fig.canvas.draw()

    # Sleep according to default sampling rate according to the sensor settings
    time.sleep(1 / 26.3)


