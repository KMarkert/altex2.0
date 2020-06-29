import sqlalchemy as sql
import pandas as pd

def queryDb(query,projectid=None):
    df = pd.read_gbq(query,project_id=projectid)
    if 'geom' in df.columns:
        df.drop(['geom'],axis=1,inplace=True)
    return df

def constructQuery(startTime=None,endTime=None,dataset=None,table=None,region=None,bbox=None,exclude=None):
    """

    """

    if all(map(lambda x: x==None,(startTime,endTime,region,bbox))):
        raise ValueError("please provide a time or geometry to filter by")

    if exclude is not None:
        if len(exclude) > 1:
            excludeCols = ','.join(exclude)
        else:
            excludeCols = exclude[0]
        cStr = f'* EXCEPT ({excludeCols})'
    else:
        cStr = '*'

    query = f"SELECT {cStr}, '{table.lower()}' as sensor FROM `{dataset.lower()}.{table.lower()}`"

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
        query = query + f" {prepend} ST_Intersects(geom, ST_GEOGFROMTEXT('POLYGON(({region}))')) "
        prepend = 'AND'

    if bbox is not None:
        bbox = ','.join([str(i) for i in bbox])
        query = query + f" {prepend} ST_IntersectsBox(geom, {bbox}) "
        prepend = 'AND'

    return query + ';'
