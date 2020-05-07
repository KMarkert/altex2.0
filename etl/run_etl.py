import subprocess
import datetime


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
    print(f'{datetime.datetime.now()}: ingesting {dateStr} for {sensor}...')
    cmd = f'python {script} etl {sensor} {workingdir} {dbname} --startTime {dateStr} --endTime {dateStr} --username {username} --spatialFilter {landFile} --cleanup'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = proc.communicate()
    print(f'{datetime.datetime.now()}: done ingesting \n')
