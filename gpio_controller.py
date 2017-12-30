import select
import _thread


PATH='/sys/class/gpio/'
#maby add stop thread methode
class gpioC(object):
    def __init__(self):
        self._poll = select.poll()
        self.file = {}
        self.translate = {}
        

    def addPin(self,pin,edge):
        f = open(PATH+'export','w')
        try:
            f.write(str(pin))
            f.close()
        except OSError as e:
            print('error is',e)
            del(f)
        with open(PATH+'gpio'+str(pin)+'/direction','w') as f:
            f.write('in')
        with open(PATH+'gpio'+str(pin)+'/edge','w') as f:
            f.write(edge)
        self.file[pin] = open(PATH+'gpio'+str(pin)+'/value','r')
        self.translate[self.file[pin].fileno()]=pin
        self._poll.register(self.file[pin],select.POLLPRI)

    def rmPin(self,pin):
        if pin in self.file.keys():
            self.poll.unregister(self.file[pin].fileno())
            del(self.translate[self.file[pin].fileno()])
            del(self.file[pin])
        

    def poll(self,timeout):
        ret = {}
        events = self._poll.poll(timeout)
        #print(events)
        for event in events:
            i = self.translate[event[0]]
            #print(i,self.file[i].read())
            ret[i]=self.file[i].read()[:-1]
            self.file[i].seek(0)
        #print(ret)
        return ret

    def strPoll(self, handler):
        _thread.start_new_thread(self._handler, ()) 

    def getValue(self):
        ret = {}		
        for i in self.file:
            ret[self.translate[self.file[i].fileno()]] = self.file[i].read()[0]
            self.file[i].seek(0)
        return ret
            
        
