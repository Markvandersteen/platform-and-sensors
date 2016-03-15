#!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time
import sys
# import Adafruit_DHT
from threading import Thread
import os
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

# setting up template directory
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
CSS_DIR =os.path.join(os.path.dirname(os.path.abspath(__file__)), 'css')
print (ASSETS_DIR)
app = Flask(__name__, static_folder=ASSETS_DIR)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None



def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0

    while True:
        # humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302 , 4)
        humidity = 44.22
        temperature = 21.23
        time.sleep(2)
        socketio.emit('my response',
                      {'data': 'Server generated response ', 'count': count, 'humidity' : humidity, 'temperature' : temperature},
                      namespace='/test')
        count += 1


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')




@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
