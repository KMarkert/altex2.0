from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from src import dbio,waterlevel

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/",response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.get("/map/",response_class=HTMLResponse)
def map_page(request: Request):
    return templates.TemplateResponse("map.html",{"request": request})

@app.get("/info/",response_class=HTMLResponse)
def info_page(request: Request):
    return templates.TemplateResponse("info.html",{"request": request})

@app.get("/api/get_table/", response_class=JSONResponse)
def get_table(sensor: str, start_time: str, end_time: str, region: str):

    return_obj = dict()
    
    queryParams = {}
    # get some domain specific information
    queryParams['startTime'] = start_time
    queryParams['endTime'] = end_time
    queryParams['sensor'] = sensor

    tablesq =  dbio.constructTableQuery(**queryParams)
    queryTables = dbio.queryDb(tablesq,username=config.DBUSERNAME,
        host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

    region = region
    # if region is not None:
    queryParams['region'] = region
    # else:
    #     queryParams['bbox'] = request.args.get("bbox")

    q = dbio.constructSpatialQuery(queryTables,**queryParams)
    df= dbio.queryDb(q,username=config.DBUSERNAME,
        host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

    return_obj['result'] = df.to_json(orient='split',index=False)

    return return_obj

@app.get("/api/get_waterlevel/", response_class=JSONResponse)
def get_table(sensor: str, start_time: str, end_time: str, region: str, apply_filter: bool = True):

    return_obj = dict()
    
    queryParams = {}
    # get some domain specific information
    queryParams['startTime'] = start_time
    queryParams['endTime'] = end_time
    queryParams['sensor'] = sensor

    tablesq =  dbio.constructTableQuery(**queryParams)
    queryTables = dbio.queryDb(tablesq,username=config.DBUSERNAME,
        host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

    region = region
    # if region is not None:
    queryParams['region'] = region
    # else:
    #     queryParams['bbox'] = request.args.get("bbox")

    q = dbio.constructSpatialQuery(queryTables,**queryParams)
    df= dbio.queryDb(q,username=config.DBUSERNAME,
        host=config.DBHOST,port=config.DBPORT,dbname=config.DBNAME)

    wl = waterlevel.calcWaterLevel(df,applyFilter=apply_filter)

    return_obj['result'] = wl.to_json(orient='split')

    return return_obj