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
import rfm69
import logging
import HDC1080
import storeWeather
from IPython.core.debugger import Tracer;


PATH='/root/webserver2/'


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


# some protected url
@app.route('/')
@login_required
@nocache
def home():
    global PATH

    t0=datetime.datetime.now()
    daypath=PATH+'data/local/days/'+'{}.{}.{}.json'.format(t0.year,t0.month,t0.day)
    if os.path.isfile(daypath):
        with open(daypath,'r') as f:
            data = eval(json.load(f))
    else:
        data=[[],[],[],[]]

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





@app.route('/getNewData', methods=['GET','POST'])
def check_selected():

    global PATH

    post = request.args.get('post', 0)
    post=post.split(' ')
    duration=post[0]
    geo=post[1]
    date=post[2].split('.')
    date=datetime.datetime(int(date[2]), int(date[1]), int(date[0]))
    fc=float(post[3])
 
    if geo=='local': path=PATH+'data/local/'
    else: path=PATH+'data/remote/' 

    pathBevor=path

    if duration=='day': 
        path = path+'days/{}.{}.{}.json'.format(date.year,date.month,date.day)
        dateBevor = date - datetime.timedelta(days=1)
        pathBevor = pathBevor+'days/{}.{}.{}.json'.format(dateBevor.year,dateBevor.month,dateBevor.day)
    elif duration=='week': 
        path = path+'weeks/{}.{}.json'.format(date.year,date.isocalendar()[1])
        dateBevor = date - datetime.timedelta(days=7)
        pathBevor = pathBevor+'weeks/{}.{}.json'.format(dateBevor.year,dateBevor.isocalendar()[1])
    elif duration=='month':
        path = path+'months/{}.{}.json'.format(date.year,date.month)
        dateBevor = date - datetime.timedelta(days=date.day)
        pathBevor = pathBevor+'months/{}.{}.json'.format(pathBevor.year,pathBevor.month)
    elif duration=='year': path = path+'years/{}.json'.format(date.year)   
    
    if os.path.isfile(path):    
        with open(path,'r') as f:
            data=eval(json.load(f)) 
    else: data=[[],[],[],[]]

    if duration !='year' and fc>0:
        if os.path.isfile(pathBevor):
            with open(pathBevor,'r') as f:
                dataBevor=eval(json.load(f))
        else: dataBevor=[[],[],[]]
    #here the filtering must be done. the filter initial condition must get filled with the dataBevor last indexes.
    #filter data here!
    if(fc>0 and duration!='year'):
        if duration=="day":
            None
        elif duration=="week":
            None
        elif duration=="month":
            None

    time=(json.dumps(data[0], cls=plotly.utils.PlotlyJSONEncoder)) 
    
    #print(jsonify(graphs="hello"))
    return jsonify(time=eval(time),presure=data[2],temperature=data[1],rh=data[3])

##########################################################################



def getweather():
    global PATH
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

        stw.collectDay(t0, tempT, tempP,temprh)	
        stw.collectWeek(t0, tempT, tempP,temprh)
        stw.collectMonth(t0, tempT, tempP,temprh)
        stw.collectYear(t0)
        
        stw.get_today()           
			     
        
        #cam.capture(PATH+'/static/pic.JPG')
        #time.sleep(60)

def getremote():
    logging.debug("Start getremote")
    s = rfm69.Rfm69()
    stw = storeWeather.storeWeather(PATH+'data/remote/')
    logging.debug("history loaded")
    
    while True:
        try:        
            #Tracer()()
            data = s.rx(120*1000)
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


            else:
                logging.debug("somethink went wrong, reinit")
                logging.debug("flags bevor are {}, mode ={}".format(s.getFlag(), s.getMode()))
                #s.reset()
                #s.initModule()
                s=rfm69.Rfm69()
                time.sleep(0.1)
                logging.debug("flags afer are {}, mode ={}".format(s.getFlag(), s.getMode()))
        except Exception as e:
            logging.debug("unknown error: {}".format(e)) 
    

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s:%(filename)s:%(funcName)s:%(message)s:',filename='logging.log',level=logging.DEBUG)
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
    
