"""
Demo Flask application to test the operation of Flask with socket.io

Aim is to create a webpage that is constantly updated with random numbers from a background python process.

30th May 2014

===================

Updated 13th April 2018

+ Upgraded code to Python 3
+ Used Python3 SocketIO implementation
+ Updated CDN Javascript and CSS sources

"""




# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event
import pymongo

__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["penny"]
upcoming_collection = db["upcoming"]
tracking_collection = db["tracking"]

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()


def get_upcoming_string(upcoming):
    upcoming_str = ""
    for u in upcoming:
        if (u["cardtype"] == "None"):
            upcoming_str  +=  str(u["seconds_left"]) + ": Bid Pack "  + str(u["bidvalue"]) + " (" +str(u["auctionid"])  + ")<br>"
        else:
            upcoming_str  += str(u["seconds_left"]) + ": " + u["cardtype"] + " $" + str(u["cardvalue"]) + " (" + str(u["auctionid"]) + ")<br>"
    return upcoming_str

def create_auction_table(a_data, auction_id):
    auction_str = "<table bgcolor='#555555' border=1><TR><TD bgcolor='#777777' colspan=7>"

    if (a_data["cardtype"] == "None"):
        auction_str  += "<H4>" + auction_id + ": Bid Pack "  + str(a_data["bidvalue"]) + "</h4>"
    else:
        auction_str  += "<H4>" + auction_id + ": " + a_data["cardtype"] + " $" + str(a_data["cardvalue"]) 

    if a_data["tracking_OK"]:
        auction_str += " - OK"
    else:
        auction_str += "- <font color='red'>NOT FULLY TRACKING!</font>"

    auction_str += "</h4>"

    if (a_data["bom_ev"] <= 0):
        bom_bgcolor = "red"
    else:
        bom_bgcolor = "green"
    if (a_data["manual_ev"] <= 0):
        manual_bgcolor = "red"
    else:
        manual_bgcolor = "green"
    auction_str += "</td></tr>"
    auction_str += "<tr><td>Current Bid</td><td>Current Winner</td><td>Profit if win</td><td>Prob. of Win (manual)</td><td>Expected Value (manual)</td><td>Prob. of Win (bidomatic)</td><td>Expected Value (bidomatic)</td></tr>"
    auction_str += "<tr><td align='center'>{:}</td><td align='center'>{:}</td><td align='center'>${:.2f}</td><td align='center'>{:.4f}</td><td align='center' bgcolor = '{:}'><b><font size=+2>${:.2f}</font></b></td><td align='center'>{:.4f}</td><td align='center' bgcolor = '{:}'><b><font size=+2>${:.2f}</font></b></td>".format(str(a_data["bid"]), a_data["last_user"],
                                    a_data["potential_profit"],a_data["manual_proba"], manual_bgcolor, a_data["manual_ev"], a_data["bom_proba"], bom_bgcolor, a_data["bom_ev"])
    auction_str += "</table><br>"
    return auction_str

def updatePage():
    """
    Send a message to the page to update the live auctions and upcoming auctions.
    
    Parameters: None
    Returns: None
    """

    while not thread_stop_event.isSet():
   
        upcoming_str = get_upcoming_string(upcoming_collection.find_one({})["auctions"])
        msg_dict = {'upcoming': upcoming_str}
        tracked_auctions = tracking_collection.find({})
        for i in range(10):
            msg_dict ["auction" + str(i)] = ""
        i = 0
        for ta in tracked_auctions:
            a_data = ta["data"]
            if "bom_ev" not in a_data.keys():
                print("weird error")
                print (ta)
                continue
            auction_str = create_auction_table(a_data, str(ta["_id"]))
            msg_dict ["auction" + str(i)]= auction_str
            i+=1
        
        socketio.emit('newnumber', msg_dict, namespace='/test')
        

        socketio.sleep(.2)


@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = socketio.start_background_task(updatePage)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    
    socketio.run(app, host='0.0.0.0')
