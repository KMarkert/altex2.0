import sqlalchemy as sql
import pandas as pd


def queryDb(query,username='postgres',host='127.0.0.1',port=5432,dbname=None):
    engine = sql.create_engine(f"postgresql://{username}@{host}:{port}/{dbname}", echo=False)
    df = pd.read_sql_query(query,engine)
    if 'geom' in df.columns:
        df.drop(['geom'],axis=1,inplace=True)
    return df

def constructTableQuery(sensor=None,startTime=None,endTime=None):
    query = (
        "SELECT table_name FROM table_index " +
        f"WHERE sensor = '{sensor.lower()}' "+
        f"AND start_time >= '{startTime}' "+
        f"AND end_time <= '{endTime}';"
    )
    return query

def constructSpatialQuery(tables,startTime=None,endTime=None,sensor=None,region=None,columns=None,bbox=None):
    """

    """

    if all(map(lambda x: x==None,(startTime,endTime,region,bbox))):
        raise ValueError("please provide a time or geometry to filter by")

    if columns is not None:
        if type(columns) is str:
            cStr = columns
        else:
            raise TypeError('columns argument expected to be of type str formatted as "col1,col2,.."')
    else:
        cStr = '*'

    query = ""
    for i,table in tables.itertuples():

        query += f"SELECT {cStr}, '{sensor.lower()}' as sensor FROM {table.lower()}"

        prepend = 'WHERE'

        if startTime is not None:
            # inclusive
            query = query + f" {prepend} time >= '{startTime}T00:00:00' "
            prepend = 'AND'

        if endTime is not None:
            # exclusive
            query = query + f" {prepend} time <= '{endTime}T00:00:00' "
            prepend = 'AND'

        if (region is not None) and (bbox is not None):
            raise ValueError('region and bbox keywords are mutually exclusive, please provide only one')

        if region is not None:
            query = query + f" {prepend} ST_Intersects(geom, 'SRID=4326;POLYGON(({region}))') "
            prepend = 'AND'

        if bbox is not None:
            bbox = ','.join([str(i) for i in bbox])
            query = query + f" {prepend} ST_Intersects(geom, ST_MakeEnvelope({bbox}, 4326)) "
            prepend = 'AND'

        if i != (len(tables)-1):
            query += 'UNION '

    return query + ';'
