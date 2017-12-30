# -*- coding: iso-8859-1 -*-
import smbus
from time import sleep
from IPython.core.debugger import Tracer

"""
what we need:   enable a I2C interface
                enable a PWM module
"""
class hp03s:
    # Initialisierung:
    # Übergabe von Bus (0 oder 1, 0 default)
    # und Port für XCLR Leitung (Default 25: Dritter Pin von rechts oben)
    def __init__(self,busno=1,xclrpin=4):
        self.bus=smbus.SMBus(busno)
        self.control=0x50
        self.data=0x77
        try:        
            with open('/sys/class/gpio/export','w') as f:
                f.write(str(xclrpin))
        except:
            print("file allreay in use")
        with open("/sys/class/gpio/gpio"+str(xclrpin)+"/direction","w") as f:
            f.write('out')
        try:        
            with open('/sys/class/pwm/pwmchip0/export','w') as f:
                f.write('0')
        except:
            print("file allreay in use")
        with open('/sys/class/pwm/pwmchip0/pwm0/period','w') as f:
            f.write('30500')
        with open('/sys/class/pwm/pwmchip0/pwm0/duty_cycle','w') as f:
            f.write('15250')
        with open('/sys/class/pwm/pwmchip0/pwm0/enable','w') as f:
            f.write('1')
        self.xclr=xclrpin
        self.C1=self.getParam(0x10,0x11)
        self.C2=self.getParam(0x12,0x13)
        self.C3=self.getParam(0x14,0x15)
        self.C4=self.getParam(0x16,0x17)
        self.C5=self.getParam(0x18,0x19)
        self.C6=self.getParam(0x1a,0x1b)
        self.C7=self.getParam(0x1c,0x1d)
        self.A=self.getParam(0x1e)
        self.B=self.getParam(0x1f)
        self.C=self.getParam(0x20)
        self.D=self.getParam(0x21)
    

        

    
    def xclrLOW(self):
        with open("/sys/class/gpio/gpio"+str(self.xclr)+"/value",'w+') as f:
            f.write('0')

    def xclrHIGH(self):
        with open("/sys/class/gpio/gpio"+str(self.xclr)+"/value",'w+') as f:
            f.write('1')

    # Lesen eines ROM Parameters:
    # Bei Angabe von 2 Adressen werden beide ausgelesen und Inhalt als Integer
    # zurückgegeben. Wird nur ein Parameter angegeben erfolgt Rückgabe als Byte
    # Verwendung siehe __init__
    def getParam(self,p1,p2=0):
        self.xclrLOW()
        pa=self.bus.read_byte_data(self.control,p1)
        if p2!=0:
            pb=self.bus.read_byte_data(self.control,p2)
            return(pa*256+pb)
        else:
            return(pa)
        

    # Liesst den Sensorwert für Druck aus dem ADC aus dem der tatsächliche Druck berechnet
    # werden kann
    def getRawPressure(self):
        self.xclrHIGH()
        #sleep(0.5)
        self.bus.write_byte_data(self.data,0xff,0xf0)
        sleep(0.05)
        self.bus.write_byte(self.data,0xfd)
        a=self.bus.read_byte(self.data)
        b=self.bus.read_byte(self.data)
        self.xclrLOW()
        return(a<<8|b)

    # Liesst den Sensorwert für Temperatur aus dem ADC, aus dem die tatsächliche Temperatur 
    # berechnet werden kann
    def getRawTemperature(self):
        self.xclrHIGH()
        #sleep(0.5)
        self.bus.write_byte_data(self.data,0xff,0xe8)
        sleep(0.05)
        self.bus.write_byte(self.data,0xfd)
        a=self.bus.read_byte(self.data)
        b=self.bus.read_byte(self.data)
        self.xclrLOW()
        return(a*256+b)

    # Liesst die Sensorwerte und berechnet die Temperatur
    # Rückgabe als Float
    def getTemperature(self):
        #Tracer()()
        D2=self.getRawTemperature()
        D1=self.getRawPressure()
        if (D2>=self.C5):
            dUT=D2-self.C5-((D2-self.C5)/128)*((D2-self.C5)/128)*self.A/2**self.C
        else:
            dUT=D2-self.C5-((D2-self.C5)/128)*((D2-self.C5)/128)*self.B/2**self.C
        OFF=(self.C2+(self.C4-1024)*dUT/2**14)*4
        SENS=self.C1+self.C3*dUT/2**10
        X=SENS*(D1-7168)/2**14-OFF
        P=X*10/2**5+self.C7
        T=250+dUT*self.C6/2**16-dUT/2**self.D
        return(T/10.0)
    
    # Liesst die Sensorwerte und berechnet den Druck
    # Rückgabe als Float
    def getPressure(self):
        D2=self.getRawTemperature()
        D1=self.getRawPressure()
        if (D2>=self.C5):
            dUT=D2-self.C5-((D2-self.C5)/128)*((D2-self.C5)/128)*self.A/2**self.C
        else:
            dUT=D2-self.C5-((D2-self.C5)/128)*((D2-self.C5)/128)*self.B/2**self.C

        OFF=(self.C2+(self.C4-1024)*dUT/2**14)*4
        SENS=self.C1+self.C3*dUT/2**10
        X=SENS*(D1-7168)/2**14-OFF
        P=X*10/2**5+self.C7
        T=250+dUT*self.C6/2**16-dUT/2**self.D
        return(P/10.0)

    # Berechnet den Druck bezogen auf Meereshöhe
    # Parameter: tatsächlicher Druck, Meereshöhe
    def getPressureSeaLevel(self,realpressure,h):
        E=2.718281828459
        P0=realpressure/(pow(E,(((-1.0)*h)/7990.0)))
        return(P0)

    def getPressureAvg(self, cycle=20):
        P = 0.0
        i = cycle		
        while(i):
            i = i-1
            P = P+self.getPressure()
        P = P/cycle
        return P

    def getTemperatureAvg(self, cycle=20):
        T = 0.0
        i = cycle
        while(i):
            i = i-1
            T = T+self.getTemperature()
        T = T/cycle
        return T

			
