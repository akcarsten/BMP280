from BMP280 import BMP280
import time
import matplotlib.pyplot as plt     
        
sensor = BMP280()

temp_coeffs = sensor.get_temperature_coefficients()
pres_coeffs = sensor.get_pressure_coefficients()

sensor.set_config()
sensor.set_control()

window = 200
data = []
temperature = []
pressure = []
for i in range(1000):
    
    data.append(sensor.get_adc())
    
    temp, _ = sensor.convert_adct(data[i][1], temp_coeffs)
    pres = sensor.convert_adcp(data[i][0], data[i][1], pres_coeffs, temp_coeffs)

    temperature.append(temp)
    pressure.append(pres)
    
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
        line1.set_ydata(pressure[-window - 1:])
        line2.set_ydata(temperature[-window - 1:])
        
        ax1.set_ylim((min(pressure[-window - 1:]), max(pressure[-window - 1:])))
        ax2.set_ylim((min(temperature[-window - 1:]), max(temperature[-window - 1:])))

        fig.canvas.draw()
        fig.canvas.flush_events
        
    time.sleep(1 / 26.3)
        
#plt.show()

