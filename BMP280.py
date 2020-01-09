import smbus
import time
import matplotlib.pyplot as plt


class BMP280:
    
    def __init__(self, bus=1, address=0x76):
        
        # Create I2C bus instance
        self.bus = smbus.SMBus(bus)
        
        # Set the I2C address
        self.address    = address
        
        # Set the default sensor configuration
        self.spi3w_en = '00'
        self.filter   = '101'
        self.t_sb     = '000'
        
        self.osrs_t   = '010'
        self.osrs_p   = '101'
        self.mode     = '11'
        
        # Add the register information
        self.temp_xlsb  = 0xFC
        self.temp_lsb   = 0xFB
        self.temp_msb   = 0xFA
        self.press_xlsb = 0xF9
        self.press_lsb  = 0xF8
        self.press_msb  = 0xF7
        self.config     = 0xF5
        self.ctrl_meas  = 0xF4
        self.status     = 0xF3
        self.reset      = 0xE0
        self.id         = 0xD0
        self.calib      = 0x88
        
        # Add the registers for the temperature coefficients
        self.T1_reg     = 0x88
        self.T2_reg     = 0x8A
        self.T3_reg     = 0x8C
        
        # Add the registers for the pressure coefficients
        self.P1_reg     = 0x8E
        self.P2_reg     = 0x90
        self.P3_reg     = 0x92
        self.P4_reg     = 0x94
        self.P5_reg     = 0x96
        self.P6_reg     = 0x98
        self.P7_reg     = 0x9A
        self.P8_reg     = 0x9C
        self.P9_reg     = 0x9E
        
    @staticmethod
    def _signed(x):
        
        if x > 32767:
            x -= 65536
        
        return x
        
    def write_register(self, register, int_value):
        
        self.bus.write_byte_data(self.address, register, int_value)
        
    def set_config(self):
        
        settings = hex(int(self.t_sb + self.filter + self.spi3w_en, 2))
        self.write_register(self.config, int(settings, 16))
        
        if self.read_config_register()[0] == int(settings, 16):
            print('Config register updated')
        else:
            print('Could not update config register')
            
    def set_control(self):
        
        settings = hex(int(self.osrs_t + self.osrs_p + self.mode, 2))
        self.write_register(self.ctrl_meas, int(settings, 16))
        
        if self.read_control_register()[0] == int(settings, 16):
            print('Control register updated')
        else:
            print('Could not update control register')
        
    def read_register(self, register, num_bytes=1):
        
        return self.bus.read_i2c_block_data(self.address, register, num_bytes)

    def read_config_register(self):
        
        return self.read_register(self.config)   
            
    def read_control_register(self):
        
        return self.read_register(self.ctrl_meas)
    
    def read_status_register(self):
        
        return self.read_register(self.status)

    def read_calibration(self):
        
        # Read all 24 calibration registers back from the last calibration register 
        return self.read_register(self.calib, 24)

    def read_data(self):
        
        # Read all 6 data registers back from the pressure MSB register (burst read)
        return self.read_register(self.press_msb, 6)
    
    def get_temperature_coefficients(self):
        
        T1 = self.bus.read_word_data(self.address, self.T1_reg) & 0xFFFF
        T2 = self.bus.read_word_data(self.address, self.T2_reg) & 0xFFFF
        T3 = self.bus.read_word_data(self.address, self.T3_reg) & 0xFFFF
        
        temp_coeffs = [T1, self._signed(T2), self._signed(T3)]
        
        return temp_coeffs
    
    def get_pressure_coefficients(self):
        
        P1 = self.bus.read_word_data(self.address, self.P1_reg) & 0xFFFF
        P2 = self.bus.read_word_data(self.address, self.P2_reg) & 0xFFFF
        P3 = self.bus.read_word_data(self.address, self.P3_reg) & 0xFFFF
        P4 = self.bus.read_word_data(self.address, self.P4_reg) & 0xFFFF
        P5 = self.bus.read_word_data(self.address, self.P5_reg) & 0xFFFF
        P6 = self.bus.read_word_data(self.address, self.P6_reg) & 0xFFFF
        P7 = self.bus.read_word_data(self.address, self.P7_reg) & 0xFFFF
        P8 = self.bus.read_word_data(self.address, self.P8_reg) & 0xFFFF
        P9 = self.bus.read_word_data(self.address, self.P9_reg) & 0xFFFF
        
        pres_coeffs = [P1, self._signed(P2), self._signed(P3), self._signed(P4), self._signed(P5),
                 self._signed(P6), self._signed(P7), self._signed(P8), self._signed(P9)]
        
        return pres_coeffs
    
    def get_adc(self):
        
        data = self.read_data()
        adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
        adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16
        
        return adc_p, adc_t
    
    @staticmethod
    def convert_adct(adc_t, temp_coeffs):
        
        # Temperature offset calculations
        var1  = ((adc_t) / 16384.0 - (temp_coeffs[0]) / 1024.0) * (temp_coeffs[1])
        var2  = (((adc_t) / 131072.0 - (temp_coeffs[0]) / 8192.0) * ((adc_t)/131072.0 - (temp_coeffs[0])/8192.0)) * (temp_coeffs[2])       
        t_fine = (var1 + var2)
        
        temperature = t_fine / 5120.0
        
        return temperature, t_fine
    
    def convert_adcp(self, adc_p, adc_t, pres_coeffs, temp_coeffs):
        
        _, t_fine = self.convert_adct(adc_t, temp_coeffs)
        
        # Pressure offset calculations
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * (pres_coeffs[5]) / 32768.0
        var2 = var2 + var1 * (pres_coeffs[4]) * 2.0
        var2 = (var2 / 4.0) + ((pres_coeffs[3]) * 65536.0)
        var1 = ((pres_coeffs[2]) * var1 * var1 / 524288.0 + (pres_coeffs[1]) * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * (pres_coeffs[0])
        p    = 1048576.0 - adc_p
        p    = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = (pres_coeffs[8]) * p * p / 2147483648.0
        var2 = p * (pres_coeffs[7]) / 32768.0
        pressure = (p + (var1 + var2 + (pres_coeffs[6])) / 16.0) / 100
        
        return pressure

    def get_data(self):
        
        adc_p, adc_t = self.get_adc()
        temp_coeffs = self.get_temperature_coefficients()
        pres_coeffs = self.get_pressure_coefficients()
        
        temp, _ = self.convert_adct(adc_t, temp_coeffs)
        pres = self.convert_adcp(adc_p, adc_t, pres_coeffs, temp_coeffs)
        
        return pres, temp
           
        
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
