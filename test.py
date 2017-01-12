#!/usr/bin/env python
import os, time, sys, urllib, re

# http://eyalarubas.com/python-subproc-nonblock.html
from subprocess import Popen, PIPE
from time import sleep
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read

RECORD_FROM = 2.5
DURATION = 5. # sec
SHADER_PATH = '000-void.frag'
TMP_DIR = '/tmp/'
TMP_SHD = TMP_DIR + 'shader.frag'

class Shader:
    COMMAND='glslViewer'
    process = {}
    cout = {}
    wait_time = 0.0001
    time = 0.
    delta = 0.
    fps = 0

    def __init__(self, filename, options = {}):
        cmd = [self.COMMAND]
        if options.has_key("scale"):
            cmd.append('-w '+ str(options["scale"]))
            cmd.append('-h '+ str(options["scale"]))
        else:
            cmd.append('-w 5000')
            cmd.append('-h 5000')
        if options.has_key("visible"):
            if not options["visible"]:
                cmd.append('--headless')
        else:
            cmd.append('--headless')

        cmd.append(filename)
        self.process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr = PIPE, shell=False)
        flags = fcntl(self.process.stdout, F_GETFL) # get current self.process.stdout flags
        fcntl(self.process.stdout, F_SETFL, flags | O_NONBLOCK)
        # self.cout = NonBlockingStreamReader(self.process)

    def read(self):
        while True:
            try:
                return read(self.process.stdout.fileno(), 1024).rstrip()
            except OSError:
                return 'none'

    def isFinish(self):
        return self.process.poll() is not None
    def getTime(self):
        self.process.stdin.write('time\n')
        sleep(self.wait_time)
        answer = self.read()
        if answer:
            if answer.replace('.','',1).isdigit():
                self.time = float(answer)
        return self.time
        
    def getDelta(self):
        self.process.stdin.write('delta\n')
        sleep(self.wait_time)
        answer = self.read()
        if answer:
            if answer.replace('.','',1).isdigit():
                self.delta = float(answer)
        return self.delta


    def getFPS(self):
        return self.process.stdin.write('fps\n')
        sleep(self.wait_time)
        answer = self.read()
        if answer:
            if answer.replace('.','',1).isdigit():
                self.fps = float(answer)
        return self.fps

    def stop(self):
        self.process.kill()


if len(sys.argv) > 1:
    SHADER_PATH = sys.argv[1]
else:
    print 'This script dowload a shader and their resorces:\nUse:\n$ ./glslLoader.py [URL|LOG_#]\n'
    exit()

if SHADER_PATH.isdigit():
    SHADER_PATH='https://thebookofshaders.com/log/' + SHADER_PATH + '.frag'

if SHADER_PATH.startswith('http'):
    http = urllib.URLopener()
    http.retrieve(SHADER_PATH, TMP_SHD)
    SHADER_PATH=TMP_SHD

shader = Shader(SHADER_PATH)
time_start = time.time()

values = []
samples = []
old_value = 0.0
while True:
    time_now = time.time()
    time_diff = time_now - time_start
    if time_diff >= RECORD_FROM*0.1:
        if time_diff >= DURATION*0.1 or shader.isFinish():
            break
        value = float(shader.getDelta())
        if not value == old_value:
            values.append(value)
            samples.append(time_diff)
            print time_diff,value
shader.stop()

average = sum(values)/float(len(values))
print "Shader average: ",average

import plotly
import plotly.plotly as py
import plotly.graph_objs as go

plotly.tools.set_credentials_file(username='patriciogv', api_key='ELwIF5EOISZA8lhW92z3')

trace1 = go.Scatter(
    x=samples,
    y=values
)

py.iplot([trace1], filename=os.path.basename(SHADER_PATH))

print "Finish"