$DBDIR = "../data/postgres"
$DBNAME = 'altexdb'

pg_ctl initdb -D $DBDIR
pg_ctl start -D $DBDIR
createdb $DBNAME

psql -d $DBNAME -c 'CREATE EXTENSION postgis;'
