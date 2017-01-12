#!/usr/bin/env python
import os, time, sys, urllib, re

# http://eyalarubas.com/python-subproc-nonblock.html
from subprocess import Popen, PIPE
from time import sleep
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read

RECORD_FROM = 5.
DURATION = 10. # sec
SHADER_PATH = '000-void.frag'
TMP_DIR = '/tmp/'

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

name_shader = os.path.basename(SHADER_PATH);
name,ext = os.path.splitext(name_shader)

if SHADER_PATH.startswith('http'):
    http = urllib.URLopener()
    TMP_SHD = TMP_DIR + name_shader
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
            print str(time_diff)+','+str(value)
shader.stop()

average = sum(values)/float(len(values))
print "Shader average: ",average

import matplotlib.pyplot as plt
fig, ax = plt.subplots( nrows=1, ncols=1 )
ax.plot(samples, values)
fig.savefig(name+'.png')   # save the figure to file
plt.close(fig)

print "Finish"