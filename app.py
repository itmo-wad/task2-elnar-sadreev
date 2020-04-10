from flask import Flask, render_template, request, jsonify, escape, abort, send_from_directory
from flask_socketio import SocketIO
import datetime
from time import sleep
from threading import Thread, Lock, Event
import random

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app)

lock = Lock()
clear_timeout = 60*30
bot_timeout = 30
newbotmsg = ["Hello there! Did you forget about me? Wanna say something? Pleeease..",
"I'm really bored here. Would you say something?",
"Wanna talk to me a little?",
"Hey, do you like sandwiches?"]

smessages = []
lupd = Event()

def clearSessions():
	while 1:
		sleep(clear_timeout)
		lock.acquire()
		smessages.clear()
		lupd.set()
		msglist = smessages
		lock.release()
		socketio.emit('update', msglist)

thr = Thread(target=clearSessions, daemon=True)
thr.start()

def contains(msg, *args):
	for item in args:
		if (msg.find(item)!=-1):
			return True
	return False

def botReply(msg):
	botrep="I don't even know what to say! xD"
	msg=msg.lower()
	if (contains(msg, 'hi', 'hey', 'hello', 'nice to meet you')):
		botrep="Hello! Nice to meet you!"
	elif (contains(msg, 'weather')):
		botrep="The weather is fine. 20&deg; C. Or not :)"
	elif (contains(msg, 'how are you', 'how is it going')):
		botrep="Brilliant! Thank you for asking! You?"
	elif (contains(msg, 'your favorite food')):
		botrep="Metal salad seasoned with oil"
	elif (contains(msg, 'how old are you')):
		botrep="Why not asking Siri?)"
	elif (contains(msg, "i'm bored", 'i am bored', 'tell a joke', 'joke')):
		botrep="I threw a boomerang like 6 years ago and it never came back. Now I live in constant fear."
	elif (contains(msg, 'heads or tails')):
		if (random.randint(0,1)==0):
			botrep="Heads!"
		else:
			botrep="Tails!"
	elif (contains(msg, 'good bye', 'see you', 'see you soon', 'bye')):
		botrep="Already leaving? Alright then. Bye("
	elif (contains(msg, 'lol', 'lmao', 'good', 'fine', 'thanks', 'thank you', 'yes', 'brilliant', 'excellent')):
		botrep="&#128515;"
	elif(contains(msg, 'you are silly', 'you are dumb', 'you are just a robot')):
		botrep="Why would you insult me? Robots have feelings too &#128557;"

	lock.acquire()
	smessages.append({'author': 'Bot', 'msg': botrep, 'time': '{0:%H:%M}'.format(datetime.datetime.now())})
	lupd.set()
	msglist = smessages
	lock.release()
	socketio.emit('update', msglist)

def botNewMsg():
	while 1:
		sleep(bot_timeout)
		lock.acquire()
		smessages.append({'author': 'Bot', 'msg': newbotmsg[random.randrange(0,len(newbotmsg))], 'time': '{0:%H:%M}'.format(datetime.datetime.now())})
		lupd.set()
		msglist = smessages
		lock.release()
		socketio.emit('update', msglist)

thr1 = Thread(target=botNewMsg, daemon=True)
thr1.start()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/short')
def short():
	return render_template('short.html')

@app.route('/long')
def long():
	return render_template('long.html')

@app.route('/websock')
def websock():
	return render_template('websock.html')

@app.route('/newmessage',methods=['POST'])
def newmsg():
	nmsg = request.values["content"]
	lock.acquire()
	smessages.append({'author': 'You', 'msg': str(escape(nmsg)), 'time': '{0:%H:%M}'.format(datetime.datetime.now())})
	lupd.set()
	lock.release()
	Thread(target=botReply, args=(nmsg,), daemon=True).start()
	return jsonify(status="OK")

@app.route('/spoll')
def spoll():
	lock.acquire()
	msglist = smessages
	lock.release()
	return jsonify(msglist)

@app.route('/lpoll')
def lpoll():
	if (not lupd.wait(20)):
		abort(408)
	lock.acquire()
	msglist = smessages
	lupd.clear()
	lock.release()
	return jsonify(msglist)

@app.route('/clear')
def clearhist():
	lock.acquire()
	msglist = smessages.clear()
	lupd.set()
	msglist = smessages
	lock.release()
	socketio.emit('update', msglist)
	return jsonify(status="OK")

@socketio.on('connected')
def connected():
	lock.acquire()
	msglist = smessages
	lock.release()
	return msglist

@socketio.on('newmessage')
def newmessage(msg):
	lock.acquire()
	smessages.append({'author': 'You', 'msg': str(escape(msg)), 'time': '{0:%H:%M}'.format(datetime.datetime.now())})
	msglist = smessages
	lock.release()
	socketio.emit('update', msglist)
	Thread(target=botReply, args=(msg,), daemon=True).start()


if (__name__ == '__main__'):
	app.run(host='0.0.0.0', debug=True, threaded=True)
