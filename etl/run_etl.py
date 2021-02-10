import sys
import time
import logging
import subprocess
import datetime

logging.basicConfig(filename = sys.argv[1],
                    format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p',
                    level = logging.INFO)

script = 'jason.py'
sensor = 'jason2'
workingdir = f'../data/altimetry/{sensor}/'
dbname= 'altexdb'
username = 'kmarkert'
landFile = '../data/ancillary/land_area.geojson'


start = datetime.datetime.strptime('2008-07-04',"%Y-%m-%d")
end = datetime.datetime.strptime('2008-12-31',"%Y-%m-%d")
iters = (end-start).days + 1

for t in range(iters):
    date = start + datetime.timedelta(t)
    dateStr = date.strftime('%Y-%m-%d')
    logging.info(f' ingesting {dateStr} for {sensor}...')
    cmd = f'python {script} etl {sensor} {workingdir} {dbname} --startTime {dateStr} --endTime {dateStr} --username {username} --spatialFilter {landFile} --cleanup'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = proc.communicate()
    logging.info(f"STDOUT: {out}")
    logging.error(f"STDERR: {err}")

    time.sleep((60*5))