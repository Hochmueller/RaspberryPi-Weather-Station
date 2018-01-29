from flask import Flask, Response, redirect, url_for, request, session, abort, render_template,jsonify
from flask.ext.login import LoginManager, UserMixin, \
                                login_required, login_user, logout_user 

import json
import plotly
import datetime
import numpy as np
import _thread
import time
import HP03S
import HDC1080
import picamera
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from nocache import nocache
import os.path
import os
import rfm69
import logging
import HDC1080
import storeWeather
from IPython.core.debugger import Tracer;
import scipy.signal
from calendar import mdays

PATH=os.path.dirname(os.path.realpath(__file__))+'/'


app = Flask(__name__)

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# silly user model
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# create some users with ids 1 to 20       
users = [User(id) for id in range(1, 21)]


sample_rate = 0.0166
nyq_rate = sample_rate / 2.0
width = 0.08
ripple_db = -20.0
N, beta = scipy.signal.kaiserord(ripple_db, width)
cutoff_hz = 1/(60*60)
taps = scipy.signal.firwin(N, cutoff_hz/nyq_rate, window=('kaiser', beta))

# some protected url
@app.route('/')
@login_required
@nocache
def home():
    global PATH
    global N
    t0=datetime.datetime.now()
    daypath=PATH+'data/local/days/'+'{}.{}.{}.json'.format(t0.year,t0.month,t0.day)
    if os.path.isfile(daypath):
        with open(daypath,'r') as f:
            data = eval(json.load(f))
    else:
        data=[[],[],[],[]]

    
    if len(data[0])>(N/2):
        data[0]=data[0][:-int(N/2)]
        data[1]=data[1][int(N/2):]
        data[2]=data[2][int(N/2):]
        data[3]=data[3][int(N/2):]
        data[1]=scipy.signal.lfilter(taps, 1.0, data[1],zi=scipy.signal.lfilter_zi(taps,1.0)*data[1][0])[0]
        data[2]=scipy.signal.lfilter(taps, 1.0, data[2],zi=scipy.signal.lfilter_zi(taps,1.0)*data[2][0])[0]
        data[3]=scipy.signal.lfilter(taps, 1.0, data[3],zi=scipy.signal.lfilter_zi(taps,1.0)*data[3][0])[0]
    graphs = [
        dict(
            data=[
                dict(
                    x=data[0],
                    y=data[1],
                    type='scatter'
                ),
            ],
            layout=dict(
                title=''
            )
        ),

        dict(
            data=[
                dict(
                    x = data[0],
                    y = data[2],
                    
                )
            ]
        ),
        dict(
            data=[
                dict(
                    x = data[0],
                    y = data[3],
                    
                )
            ]
        )
    ]

    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['Temperature','Airpressure','Relative Humidity']

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('static.html',
                           ids=ids,
                           graphJSON=graphJSON,
                            filename='pic.JPG')

 
# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        if password == username + "_secret":
            id = username.split('user')[1]
            user = User(id)
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')
    
    
# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response



@app.route('/getCurrent',methods=['GET','POST'])
def getlive():
    post = request.args.get('post', 0)
    post=post.split(' ')
    duration=post[0]
    date=post[1].split('.')
    date=datetime.datetime(int(date[2]), int(date[1]), int(date[0]))

    pathIndoor=PATH+'data/local/'
    pathOutdoor=PATH+'data/remote/'

    if duration=='day': 
        pathIndoor = pathIndoor+'days/{}.{}.{}.json'.format(date.year,date.month,date.day)
        pathOutdoor = pathOutdoor+'days/{}.{}.{}.json'.format(date.year,date.month,date.day)
    elif duration=='week': 
        pathIndoor = pathIndoor+'weeks/{}.{}.json'.format(date.year,date.isocalendar()[1])
        pathOutdoor = pathOutdoor+'weeks/{}.{}.json'.format(date.year,date.isocalendar()[1])
    elif duration=='month':
        pathIndoor = pathIndoor+'months/{}.{}.json'.format(date.year,date.month)
        pathOutdoor = pathOutdoor+'months/{}.{}.json'.format(date.year,date.month)
    elif duration=='year': 
        pathIndoor = pathIndoor+'years/{}.json'.format(date.year)   
        pathOutdoor = pathOutdoor+'years/{}.json'.format(date.year)
    
    if os.path.isfile(pathIndoor):    
        with open(pathIndoor,'r') as f:
            dataIndoor=eval(json.load(f)) 
    else: dataIndoor=[[0],[0],[0],[0]]
    
    TInN=round(float(Indoordata[0]),2)
    TInMax=round(float(max(dataIndoor[1])),2)
    TInMin=round(float(min(dataIndoor[1])),2)

    PInN=round(float(Indoordata[1]),2)
    PInMax=round(float(max(dataIndoor[2])),2)
    PInMin=round(float(min(dataIndoor[2])),2)

    HrInN=round(float(Indoordata[2]),2)
    HrInMax=round(float(max(dataIndoor[3])),2)
    HrInMin=round(float(min(dataIndoor[3])),2)

    if os.path.isfile(pathOutdoor):    
        with open(pathOutdoor,'r') as f:
            dataOutdoor=eval(json.load(f)) 
    else: dataOutdoor=[[0],[0],[0],[0]]    
    
    TOutN=round(float(remotedata[0]),2)
    TOutMax=round(float(max(dataOutdoor[1])),2)
    TOutMin=round(float(min(dataOutdoor[1])),2)

    POutN=round(float(remotedata[1]),2)
    POutMax=round(float(max(dataOutdoor[2])),2)
    POutMin=round(float(min(dataOutdoor[2])),2)

    HrOutN=round(float(remotedata[2]),2)
    HrOutMax=round(float(max(dataOutdoor[3])),2)
    HrOutMin=round(float(min(dataOutdoor[3])),2)
    
    return jsonify(TInN=TInN,TInMax=TInMax,TInMin=TInMin,PInN=PInN,PInMax=PInMax,PInMin=PInMin,HrInN=HrInN,HrInMax=HrInMax,HrInMin=HrInMin,TOutN=TOutN,TOutMax=TOutMax,TOutMin=TOutMin,POutN=POutN,POutMax=POutMax,POutMin=POutMin,HrOutN=HrOutN,HrOutMax=HrOutMax,HrOutMin=HrOutMin)


@app.route('/getNewData', methods=['GET','POST'])
def check_selected():
    global taps
    global N
    global PATH
    #Tracer()()
    post = request.args.get('post', 0)
    post=post.split(' ')
    duration=post[0]
    geo=post[1]
    date=post[2].split('.')
    date=datetime.datetime(int(date[2]), int(date[1]), int(date[0]))
    fc=float(post[3])
 
    if geo=='local': path=PATH+'data/local/'
    else: path=PATH+'data/remote/' 

    pathAfter=path

	#denkfehler, ich benötige dataafter
    if duration=='day': 
        path = path+'days/{}.{}.{}.json'.format(date.year,date.month,date.day)
        dateAfter = date + datetime.timedelta(days=1)
        pathAfter = pathAfter+'days/{}.{}.{}.json'.format(dateAfter.year,dateAfter.month,dateAfter.day)
    elif duration=='week': 
        path = path+'weeks/{}.{}.json'.format(date.year,date.isocalendar()[1])
        dateAfter = date + datetime.timedelta(days=7)
        pathAfter = pathAfter+'weeks/{}.{}.json'.format(dateAfter.year,dateAfter.isocalendar()[1])
    elif duration=='month':
        path = path+'months/{}.{}.json'.format(date.year,date.month)
        dateAfter = date + datetime.timedelta(mdays[date.month])
        pathAfter = pathAfter+'months/{}.{}.json'.format(dateAfter.year,dateAfter.month)
    elif duration=='year': path = path+'years/{}.json'.format(date.year)   
    
    if os.path.isfile(path):    
        with open(path,'r') as f:
            data=eval(json.load(f)) 
    else: data=[[],[],[],[]]

    if duration !='year' and fc>0:
        if os.path.isfile(pathAfter):
            with open(pathAfter,'r') as f:
                dataAfter=eval(json.load(f))
            #next day long enought for appending
            if(len(dataAfter[0])>(N/2)):
                data[1]=data[1][int(N/2):]+dataAfter[1][:int(N/2)]
                data[2]=data[2][int(N/2):]+dataAfter[2][:int(N/2)]
                data[3]=data[3][int(N/2):]+dataAfter[3][:int(N/2)]
        else:
            #day long enougth for shifting
            if(len(data[0])>(N/2)):
                data[0]=data[0][:-int(N/2)]
                data[1]=data[1][int(N/2):]
                data[2]=data[2][int(N/2):]
                data[3]=data[3][int(N/2):]

        
    #here the filtering must be done. the filter initial condition must get filled with the dataAfter last indexes.
    #filter data here!
    if(fc>0 and duration!='year' and len(data[0])>(N/2)):
        data[1]=list(scipy.signal.lfilter(taps, 1.0, data[1],zi=scipy.signal.lfilter_zi(taps,1.0)*data[1][0])[0])
        data[2]=list(scipy.signal.lfilter(taps, 1.0, data[2],zi=scipy.signal.lfilter_zi(taps,1.0)*data[2][0])[0])
        data[3]=list(scipy.signal.lfilter(taps, 1.0, data[3],zi=scipy.signal.lfilter_zi(taps,1.0)*data[3][0])[0])
        
       

    time=(json.dumps(data[0], cls=plotly.utils.PlotlyJSONEncoder)) 
    
    #print(jsonify(graphs="hello"))
    return jsonify(time=eval(time),presure=data[2],temperature=data[1],rh=data[3])

##########################################################################
Indoordata=[0,0,0]



def getweather():
    global PATH
    global hp
    global hdc
    logging.debug("start get weather")
    hp = HP03S.hp03s()
    hdc=HDC1080.hdc1080()
    #cam = picamera.PiCamera()
    #cam.resolution = (1280,720)
    stw = storeWeather.storeWeather(PATH+'data/local/')
    t0=datetime.datetime.now()

    while(1):  
	
        tempT=0
        tempP=0
        temprh=0
        cnt = 0
        diff = datetime.datetime.now() - t0
        while(diff.total_seconds()<60):
            tempT = tempT + hp.getTemperature()
            tempP = tempP + hp.getPressure()
            temprh = temprh + hdc.getData()[1]
            time.sleep(10)
            cnt = cnt+1
            diff = datetime.datetime.now() - t0

        t0 = datetime.datetime.now()	
        tempT = tempT/cnt
        tempP = tempP/cnt
        temprh = temprh/cnt

        Indoordata[0]=tempT
        Indoordata[1]=tempP
        Indoordata[2]=temprh

        stw.collectDay(t0, tempT, tempP,temprh)	
        stw.collectWeek(t0, tempT, tempP,temprh)
        stw.collectMonth(t0, tempT, tempP,temprh)
        stw.collectYear(t0)
        
        stw.get_today()           
			     
        
        #cam.capture(PATH+'/static/pic.JPG')
        #time.sleep(60)

remotedata=[0,0,0]

def getremote():
    global remotedata
    logging.debug("Start getremote")
    s = rfm69.Rfm69()
    stw = storeWeather.storeWeather(PATH+'data/remote/')
    logging.debug("history loaded")
    
    while True:
        try:        
            
            data = s.rx(120*1000)
            #Tracer()()
            if data:
                logging.debug("received remote package")
                tempT = float(np.fromstring(bytes(data[:4]),np.float32)[0])
                tempP = float(np.fromstring(bytes(data[4:8]),np.float32)[0])
                temprh = float(np.fromstring(bytes(data[10:12]),np.uint16)[0])
                temprh = temprh/65536*100

                t0 = datetime.datetime.now()
                stw.collectDay(t0, tempT, tempP,temprh)	
                stw.collectWeek(t0, tempT, tempP,temprh)
                stw.collectMonth(t0, tempT, tempP,temprh)
                stw.collectYear(t0)

                stw.get_today()   
                remotedata[0]=tempT
                remotedata[1]=tempP
                remotedata[2]=temprh


            else:
                logging.debug("somethink went wrong, reinit")
                logging.debug("flags bevor are {}, mode ={}".format(s.getFlag(), s.getMode()))
                #s.reset()
                #s.initModule()
                del(s)
                s=rfm69.Rfm69()
                time.sleep(0.1)
                logging.debug("flags afer are {}, mode ={}".format(s.getFlag(), s.getMode()))
        except Exception as e:
            logging.debug("unknown error: {}".format(e)) 
    

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s:%(filename)s:%(funcName)s:%(message)s:',filename=os.path.dirname(os.path.realpath(__file__))+'/logging.log',level=logging.DEBUG)
    logging.debug('start')
    _thread.start_new_thread(getweather, ())
    _thread.start_new_thread(getremote, ())
    #app.run(host='0.0.0.0',port=5000)
    app.config["CACHE_TYPE"] = "null"
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start() 
    while(1):
        pass
    
