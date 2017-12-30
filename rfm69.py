import spidev
from RFM69_reg import *
import select
import time 
import gpio_controller
import logging

modes = {
    'sleep' : 0,
    'stdby' : 1,
    'fs'    : 2,
    'tx'    : 3,
    'rx'    : 4,
    }
RFM69ConfigTbl = [
 [0x02|0x80,0x00],        #RegDataModul : Packet Mode, FSK, no Shaping
 [0x07|0x80,REG_FRFMSB],
 [0x08|0x80,REG_FRFMID],
 [0x09|0x80,REG_FRFLSB],
 [0x05|0x80,0x02],        #RegFdevMsb      241*61Hz = 35KHz   
 [0x06|0x80,0x41],        #RegFdevLsb
 [0x03|0x80,0x34],        #RegBitrateMsb      32MHz/0x3410 = 2.4kpbs
 [0x04|0x80,0x10],        #RegBitrateLsb
 [0x13|0x80,0x1a],        #RegOcp         Disable OCP
 [0x18|0x80,0x08],        #RegLNA            200R   
 [0x19|0x80,0x52],        #RegRxBw         RxBW  83KHz
 [0x2C|0x80,0x00],        #RegPreambleMsb   
 [0x2D|0x80,0x0A],        #RegPreambleLsb   10Byte Preamble
 [0x2E|0x80,0x90],        #enable Sync.Word   2+1=3bytes
 [0x2F|0x80,0xAA],        #0xAA            SyncWord = aa2dd4
 [0x30|0x80,0x2D],        #0x2D
 [0x31|0x80,0xD4],        #0xD4
 [0x37|0x80,0x30],        #RegPacketConfig1  enable CRC manchester encode
 [0x38|0x80,0x0C],        #RegPayloadLength  8bytes for length & Fixed length
 [0x3C|0x80,0x95],        #RegFiFoThresh      
 [0x58|0x80,0x2D],        #RegTestLna        increase sensitivity with LNA (Note: consumption also increase!)
 [0x6F|0x80,0x30],        #RegTestDAGC       Improved DAGC
 [0x01|0x80,0x04],        # RegOpMode = Standby   
]

#io5 not necessary
class Rfm69:
    def __init__(self,busno=0,devno=0,reset=25,IO0=22):
        logging.debug("init rfm69 class")
        #init spi        
        self.spi = spidev.SpiDev()
        self.spi.open(busno,devno)
        self.spi.bits_per_word = 8
        self.spi.max_speed_hz = 200000
        #init gpio
        self.Io0 = IO0
        self.resetpin = reset
        path = '/sys/class/gpio/gpio'
        
        try:
            f = open('/sys/class/gpio/export','w')
            f.write(str(reset)+'\n')
            f.close()
        except:
            None
        with open(path+str(reset)+'/direction','w') as f:
            f.write('out')
        with open(path+str(reset)+'/value','w') as f:
            f.write('0')
        self.gpio_in=gpio_controller.gpioC()
        self.gpio_in.addPin(self.Io0,'rising')
        self.initModule()
        
    def initModule(self):
        for i in RFM69ConfigTbl:
            self.spi.xfer(i)

        """
        #self.reset()
        
		#Clocks
        self.spi.xfer([RFM_WRITE|BITRATEMSB,REG_BRMSB,REG_BRLSB,REG_FDEVMSB,REG_FDEVLSB,REG_FRFMSB,REG_FRFMID,REG_FRFLSB])
        #Afc: Improve AFC
        self.spi.xfer([RFM_WRITE|AFCCTRL,0b00100000])
        #offset=488Hz
        self.spi.xfer([RFM_WRITE|TESTAFC, 1])
        #RX Registers
        #LNA in = 50Ohm, AGC on; dcc=0.04*RxBW, RxBw=10.4k; afcdcc=0.02*RxBw, RxBwafc=10.4k;auto AFC;
        self.spi.xfer([RFM_WRITE|LNA,0b00001000,0b01001011,0b01001011])
        self.spi.xfer([RFM_WRITE|AFCFEI,0b0000100])
        self.spi.xfer([RFM_WRITE|DIOMAPPING1,0b01000000,0b11110111])
        
        #power
        self.spi.xfer([RFM_WRITE|PALEVEL,REG_PALEVEL])
        


        #preamble size
        self.spi.xfer([RFM_WRITE|PREAMBLELSB,PREAMBLESIZE])
        #sync
        #sync on; FIFOFILLCONDITION=if sync address interrupt; syncSize=8bypte; syntTolleranze=0;
        self.spi.xfer([RFM_WRITE|SYNCCONFIG,0b10111011,SYNCID,SYNCID,SYNCID,SYNCID,SYNCID,SYNCID,SYNCID,SYNCID])
        #packet config
        #FIX lenth; Manchester; No CRC; No Address  pyloadLength
        self.spi.xfer([RFM_WRITE|PACKETCONFIG1,0b0010000,PACKETLENGTH])
        #interpacketdelay = 416us,AutoRxRestartOn AesOff
        self.spi.xfer([RFM_WRITE|PACKETCONFIG2,0b00010010])
        #continuousdagc
        self.spi.xfer([RFM_WRITE|TESTDAGC,0x20])
        #rssi threshold:
        self.spi.xfer([RFM_WRITE|RSSITHRESH,145])
        """
        

        
    def reset(self):
        with open('/sys/class/gpio/gpio'+str(self.resetpin)+'/value','w') as f:
            f.write('1')
        time.sleep(0.1)
        with open('/sys/class/gpio/gpio'+str(self.resetpin)+'/value','w') as f:
            f.write('0')

    def getMode(self):
        temp = self.spi.xfer([RFM_READ|OPMODE,0])
        temp = (int(temp[1])>>2)&0x7
        return temp

    def setMode(self,mode):
        temp = self.spi.xfer([RFM_READ|OPMODE,0])
        temp = temp[1] & 0b11100011
        temp = temp|(modes[mode]<<2)
        self.spi.xfer([RFM_WRITE|OPMODE,temp])
        while not(self.getFlag() & (1<<7)):
            None


    def getFlag(self):
        temp = self.spi.xfer([RFM_READ|IRQFLAGS1,0,0])
        return (temp[2]<<8)|temp[1]
        #return temp

    def getRssi(self):
        self.spi.xfer([RFM_WRITE|RSSICONFIG,1])
        while self.spi.xfer([RFM_READ|RSSICONFIG,0])[1]:
            None
        rssi = self.spi.xfer([RFM_READ|RSSIVALUE,0])[1]/-2
        return rssi

    def getVersion(self):
        temp = self.spi.xfer([RFM_READ|VERSION,0])
        return temp[1]

    def readReg(self,reg):
        return self.spi.xfer([RFM_READ|reg,0])[1]

    def writeReg(self,reg,val):
        self.spi.xfer([RFM_WRITE|reg,val])

    def readBuff(self):
        data = []
        while(self.getFlag() & (1<<14)):
            data.append(self.spi.xfer([0,0])[1])
        return data

    def restartRx(self):
        self.spi.xfer([RFM_WRITE|PACKETCONFIG2,0x06])

    def rx(self,timeout):
        logging.debug("rx: mode = {}".format(self.getMode()))
        if self.getMode() != 4:
            self.setMode('rx')
        logging.debug("set mode to rx: {}".format(self.getMode()))
        while True:
            if self.gpio_in.getValue()[self.Io0]=='0':
                self.gpio_in.poll(timeout)
            if (self.getFlag() & (1<<10)):
                if (self.getFlag() & (1<<9)) == 0:
                    logging.info("crc error")
                    self.readBuff()
                    self.setMode('rx')
                else:
                    logging.debug("read rfm69")
                    return self.readBuff()
            else:
                logging.debug("unexpected error, Flag={}, Mode={}".format(self.getFlag(),self.getMode()))
                return None
        
        
   
        

        
