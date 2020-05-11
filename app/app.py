from flask import Flask
from flask_cors import CORS
from flask import render_template, url_for, jsonify, request

import config
from src import dbio,waterlevel

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app,resources={r"/api/*": {"origins": "*"}})


@app.route("/")
def index():
  return "Hello, world!"

@app.route("/map/")
def showMap():
    return render_template("map.html")

@app.route("/api/")
def get_capabilities():
    # return_obj = {}
    # if request.method is 'GET':

    return 'Hello API!'

@app.route("/api/getWaterLevel/")
def getWaterLevel():
    return_obj = {}
    if request.method == 'GET':
        try:
            queryParams = {}
            # get some domain specific information
            queryParams['startTime'] = request.args.get('startTime')
            queryParams['endTime'] = request.args.get('endTime')
            queryParams['table'] = request.args.get("sensor")

            region = request.args.get("region")
            if region is not None:
                queryParams['region'] = region
            else:
                queryParams['bbox'] = request.args.get("bbox")


            # region = ['-122.21','40.742','-122.20','40.753']
            q = dbio.constructQuery(**queryParams)
            df= dbio.queryDb(q,username=config.DBUSERNAME,
                host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

            df['sensor'] = [request.args.get("sensor") for i in range(df.shape[0])]

            filter = request.args.get("applyFilter")
            if filter in ['True','true',1,'TRUE']:
                filter = True
            else:
                filter = False

            wl = waterlevel.calcWaterLevel(df,applyFilter=filter)

            return_obj['result'] = wl.to_json(orient='split')

        except Exception as e:
            return_obj['error'] = str(e)

    return jsonify(return_obj)


@app.route("/api/getRaw/",methods=['GET'])
def getRaw():
    return_obj = {}
    if request.method == 'GET':
        try:
            queryParams = {}
            # get some domain specific information
            queryParams['startTime'] = request.args.get('startTime')
            queryParams['endTime'] = request.args.get('endTime')
            queryParams['table'] = request.args.get("sensor")

            region = request.args.get("region")
            print(region)
            if region is not None:
                queryParams['region'] = region
            else:
                queryParams['bbox'] = request.args.get("bbox")

            print(queryParams)

            q = dbio.constructQuery(**queryParams)
            # print(q)
            df= dbio.queryDb(q,username=config.DBUSERNAME,
                host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

            # add the sensor name to the dataframe
            df['sensor'] = [request.args.get("sensor") for i in range(df.shape[0])]

            return_obj['result'] = df.to_json(orient='split',index=False)

        except Exception as e:
            return_obj['error'] = str(e)

    return jsonify(return_obj)
