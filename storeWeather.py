import datetime
import json
import os


class storeWeather(object):
    def __init__(self,path,):
        self.path=path
        self.today=0
        self.get_today()
        self.day=[[],[],[],[]]
        self.week=[[],[],[],[]]
        self.month=[[],[],[],[]]
        self.year=[[],[],[],[]]
        self.load_history()
        self.weekcnt=0
        self.weektempT=0
        self.weektempP=0
        self.weektemprh=0
        self.monthcnt=0
        self.monthtempT=0
        self.monthtempP=0
        self.monthtemprh=0
        self.load_history()

    def get_today(self):
        self.today=datetime.datetime.now()

    def load_history(self):

        #if no history files add on. else open and load history.
        daypath=self.path+'days/'+'{}.{}.{}.json'.format(self.today.year,self.today.month,self.today.day)
        if os.path.isfile(daypath):
            with open(daypath,'r') as f:
                self.day = eval(json.load(f))
        else:
            with open(daypath,'w') as f:
                json.dump(repr(self.day),f)

        weekpath=self.path+'weeks/'+'{}.{}.json'.format(self.today.year,self.today.isocalendar()[1])
        if os.path.isfile(weekpath):
            with open(weekpath,'r') as f:
                self.week = eval(json.load(f))
        else:
            with open(weekpath,'w') as f:
                json.dump(repr(self.week),f)


        monthpath=self.path+'months/'+'{}.{}.json'.format(self.today.year,self.today.month)
        if os.path.isfile(monthpath):
            with open(monthpath,'r') as f:
                self.month = eval(json.load(f))
        else:
            with open(monthpath,'w') as f:
                json.dump(repr(self.month),f)

        yearpath=self.path+'years/'+'{}.json'.format(self.today.year)
        if os.path.isfile(yearpath):
            with open(yearpath,'r') as f:
                self.year = eval(json.load(f))
        else:
            with open(yearpath,'w') as f:
                json.dump(repr(self.year),f)
        

    def collectDay(self,time, temp, pressure,rh):

        if self.today.isocalendar() == time.isocalendar():
            self.day[0].append(time)
            self.day[1].append(temp)
            self.day[2].append(pressure)
            self.day[3].append(rh)
            daypath=self.path+'days/'+'{}.{}.{}.json'.format(self.today.year,self.today.month,self.today.day)
            with open(daypath,'w+') as f:
                json.dump(repr(self.day),f)
        else:
            print("new day")
            self.day=[[],[],[],[]]
            self.day[0].append(time)
            self.day[1].append(temp)
            self.day[2].append(pressure)
            self.day[3].append(rh)
            daypath=self.path+'days/'+'{}.{}.{}.json'.format(time.year,time.month,time.day)
            with open(daypath,'w') as f:
                json.dump(repr(self.day),f)


    def collectWeek(self,time, temp, pressure,rh):

        self.weekcnt=self.weekcnt+1
        self.weektempT = self.weektempT + temp
        self.weektempP = self.weektempP + pressure
        self.weektemprh = self.weektemprh + rh

        if self.weekcnt==10 or self.today.isocalendar()[1] != time.isocalendar()[1]:

            self.weektempT = round(self.weektempT/self.weekcnt,2)
            self.weektempP = round(self.weektempP/self.weekcnt,3)
            self.weektemprh = round(self.weektemprh/self.weekcnt,3)
            self.weekcnt=0
            
            if self.today.isocalendar()[1] == time.isocalendar()[1]:
                self.week[0].append(time)
                self.week[1].append(self.weektempT)
                self.week[2].append(self.weektempP)
                self.week[3].append(self.weektemprh)
                weekpath=self.path+'weeks/'+'{}.{}.json'.format(self.today.year,self.today.isocalendar()[1])
                with open(weekpath,'w+') as f:
                    json.dump(repr(self.week),f)
            else:
                
                self.week=[[],[],[],[]]
                self.week[0].append(time)
                self.week[1].append(self.weektempT)
                self.week[2].append(self.weektempP)
                self.week[3].append(self.weektemprh)
                weekpath=self.path+'weeks/'+'{}.{}.json'.format(time.year,time.isocalendar()[1])
                with open(weekpath,'w') as f:
                    json.dump(repr(self.week),f)
           	
            self.weektempT=0
            self.weektempP=0
            self.weektemprh=0


    def collectMonth(self,time, temp, pressure,rh):

        self.monthcnt=self.monthcnt+1
        self.monthtempT = self.monthtempT + temp
        self.monthtempP = self.monthtempP + pressure
        self.monthtemprh = self.monthtemprh + rh

        if self.monthcnt==60 or self.today.month != time.month:

            
            self.monthtempT = round(self.monthtempT/self.monthcnt,2)
            self.monthtempP = round(self.monthtempP/self.monthcnt,3)
            self.monthtemprh = round(self.monthtemprh/self.monthcnt,3)  
            self.monthcnt=0
            if self.today.month == time.month:
                self.month[0].append(time)
                self.month[1].append(self.monthtempT)
                self.month[2].append(self.monthtempP)
                self.month[3].append(self.monthtemprh)
                monthpath=self.path+'months/'+'{}.{}.json'.format(self.today.year,self.today.month)
                with open(monthpath,'w+') as f:
                    json.dump(repr(self.month),f)
            else:
                
                self.month=[[],[],[],[]]
                self.month[0].append(time)
                self.month[1].append(self.monthtempT)
                self.month[2].append(self.monthtempP)
                self.month[3].append(self.monthtemprh)
                monthpath=self.path+'months/'+'{}.{}.json'.format(time.year,time.month)
                with open(monthpath,'w') as f:
                    json.dump(repr(self.month),f)
            self.monthtempT = 0
            self.monthtempP = 0
            self.monthtemprh = 0


    def collectYear(self,time):

        if self.today.day != time.day:
            
            daypath=self.path+'days/'+'{}.{}.{}.json'.format(self.today.year,self.today.month,self.today.day)
            with open(daypath,'r') as f:
                temp = eval(json.load(f))
            T=0
            P=0
            rh=0
            for i in range(0,len(temp[0])):
                T=T+temp[1][i]
                P=P+temp[2][i]
                rh=rh+temp[3][i]
            T=round(T/len(temp[0]),2)
            P=round(P/len(temp[0]),3)
            rh=round(rh/len(temp[0]),3)
            if self.today.year==time.year:
                
                self.year[0].append(self.today)
                self.year[1].append(T)
                self.year[2].append(P)
                self.year[3].append(rh)
                yearpath=self.path+'years/'+'{}.json'.format(self.today.year)
                with open(yearpath,'w+') as f:
                    json.dump(repr(self.year),f)
            else:
                
                self.year=[[],[],[],[]]
                self.year[0].append(self.today)
                self.year[1].append(T)
                self.year[2].append(P)
                self.year[3].append(rh)
                yearpath=self.path+'years/'+'{}.json'.format(time.year)
                with open(yearpath,'w') as f:
                    json.dump(repr(self.year),f)
