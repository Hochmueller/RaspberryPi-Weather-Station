import smbus
from time import sleep
import struct, array, time, io, fcntl
import numpy as np

I2C_SLAVE=0x0703

ADDRESS=0x40
CONFIG_REG = 0x02
RH_REG = 0x01
TEMP_REG = 0x00



class hdc1080:
    # Initialisierung:
    # Übergabe von Bus (0 oder 1, 0 default)
    # und Port für XCLR Leitung (Default 25: Dritter Pin von rechts oben)
    def __init__(self,busno=1):
        self.HDC1000_fr= io.open("/dev/i2c-"+str(busno), "rb", buffering=0)
        self.HDC1000_fw= io.open("/dev/i2c-"+str(busno), "wb", buffering=0)
        fcntl.ioctl(self.HDC1000_fr, I2C_SLAVE, ADDRESS)
        fcntl.ioctl(self.HDC1000_fw, I2C_SLAVE, ADDRESS)
        time.sleep(0.015) #15ms startup time
        s=[CONFIG_REG ,0x10,0]
        self.HDC1000_fw.write( bytearray(s) )
        
        
    def getData(self):
        s=[TEMP_REG]
        self.HDC1000_fw.write( bytearray(s) )
        sleep(0.1)
        data = self.HDC1000_fr.read(4)
        data = struct.unpack('>HH',data)#np.fromstring(data,np.uint16)
        temp=data[0]/65536*165-40
        rh = data[1]/65536*100
        return temp, rh




