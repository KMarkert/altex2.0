from flask import Flask
from flask_cors import CORS
from flask import render_template,url_for

from . import config

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app,resources={r"/api/*": {"origins": "*"}})


@app.route("/")
def index():
  return "Hello, world!"

@app.route("/map/")
def showMap():
    return render_template("map.html")

@app.route("/api")
def get_capabilities():
    return

@app.route("/api/getTimeseries")
def getTimeseries(startTime,endTime,sensor):
    return


@app.route("/api/getRaw")
def getRaw():
    return
