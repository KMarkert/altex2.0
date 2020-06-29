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
  return render_template("index.html")

@app.route("/map/")
def map_page():
    return render_template("map.html")

@app.route("/info/")
def info_page():
    return render_template("info.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.route("/api/", methods=['GET'])
def get_capabilities():
    info = {
        "api": {
            "getWaterLevel": {
                "startTime": "beginning time to access altimetry data. accepts "
                    "ISO 8601 date format (YYYY-MM-DD)",
                "endTime": "ending time to access altimetry data. accepts "
                    "ISO 8601 date format (YYYY-MM-DD)",
                "sensor" : "name of sensor to access data. options are: "
                    "Jason2, Jason3, and Saral",
                "region": "a string of polygon coordinates creating a linearring "
                    "polygon formatted as 'x y, x y , ... , x y'. mutually exclusive "
                    "with bbox parameter",
                "bbox" : "list of bounding box coordinates to filter data formatted "
                    "as [W,S,E,N]. mutually exclusive with region parameter",
                "applyFilter": "boolean parameter to use the outlier filter when "
                    "estimating daily water levels"
            },
            "getTable": {
                "startTime": "beginning time to access altimetry data. accepts "
                    "ISO 8601 date format (YYYY-MM-DD)",
                "endTime": "ending time to access altimetry data. accepts "
                    "ISO 8601 date format (YYYY-MM-DD)",
                "sensor" : "name of sensor to access data. options are: "
                    "Jason2, Jason3, and Saral",
                "region": "a string of polygon coordinates creating a linearring "
                    "polygon formatted as 'x y, x y , ... , x y'. mutually exclusive "
                    "with bbox parameter",
                "bbox" : "list of bounding box coordinates to filter data formatted "
                    "as [W,S,E,N]. mutually exclusive with region parameter",
            }
        }
    }

    return jsonify(info)

@app.route("/api/getWaterLevel/", methods=['GET'])
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

            queryParams['dataset'] = config.BQDATASET
            queryParams['exclude'] = ['geom','lon','lat']

            q = dbio.constructQuery(**queryParams)
            df= dbio.queryDb(q,projectid=config.PROJECT_ID)

            filter = request.args.get("applyFilter")
            if filter in [True,'True','true',1,'TRUE']:
                filter = True
            else:
                filter = False

            wl = waterlevel.calcWaterLevel(df,applyFilter=filter)

            return_obj['result'] = wl.to_json(orient='split')

        except Exception as e:
            return_obj['error'] = str(e)

    return jsonify(return_obj)


@app.route("/api/getTable/", methods=['GET'])
def getTable():
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

            queryParams['dataset'] = config.BQDATASET
            queryParams['exclude'] = ['geom']
            print(queryParams)

            q = dbio.constructQuery(**queryParams)
            df= dbio.queryDb(q,projectid=config.PROJECT_ID)

            return_obj['result'] = df.to_json(orient='split',index=False)

        except Exception as e:
            return_obj['error'] = str(e)

    return jsonify(return_obj)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
