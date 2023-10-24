#!/usr/bin/python
import RPi.GPIO as GPIO
import redis
import time
import sys
import os


def listen(p, subs=(), psubs=()):
    if not subs and not psubs: raise ValueError('Must have subs')
    c = False
    t = 0
    while True:
        try:
            if subs: p.subscribe(*subs)
            if psubs: p.psubscribe(*psubs)
            t = 0
            c = True
            #print('Connected')
            for a in p.listen():
                yield a
        except redis.exceptions.ConnectionError:
            if c:
                c = False
                #print('Disconnected')
            #print('Connection failed, waiting %s seconds' % t)
            time.sleep(t)
            if not t:
                t = 1
            else:
                t *= 2
                if t > 60: t = 60

debug = 'debug' in sys.argv

def beep(b):
    GPIO.output(iopin, True)
    time.sleep(b)
    GPIO.output(iopin, False)

def daa():
  if debug: print('daa')
  beep(0.3)

def dit():
  if debug: print('dit')
  beep(0.1)

def ilp():
  if debug: print('ilp')
  time.sleep(0.1)

def lpa():
  if debug: print('lpa')
  time.sleep(0.3)

def wpa():
  if debug: print('wpa')
  time.sleep(0.7)

def mpa():
  if debug: print('mpa')
  time.sleep(1)


def letter(a):
    if a in morse:
        if debug: print('letter', a)
        for b in morse[a]:
            if b:
                daa()
            else:
                dit()
            ilp()
        lpa()
    else:
        wpa()

def message(a):
    for b in a:
        letter(b)
    mpa()

def main():
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(iopin, GPIO.OUT)
        r = redis.Redis()
        for a in listen(r.pubsub(), subs=['morse']):
            if not isinstance(a['data'], bytes): continue
            message(a['data'].decode('utf8').lower())
    finally:
        GPIO.cleanup()

def fork(func):
    pid = os.fork()
    if pid > 0:
        return
    os.chdir("/")
    os.setsid()
    os.umask(0)
    pid = os.fork()
    if pid > 0:
        return
    func()

iopin = 24

morse = {
    'a': (0, 1),
    'b': (1, 0, 0, 0),
    'c': (1, 0, 1, 0),
    'd': (1, 0, 0),
    'e': (0,),
    'f': (0, 0, 1, 0),
    'g': (1, 1, 0),
    'h': (1, 1, 1, 1),
    'i': (0, 0),
    'j': (0, 1, 1, 1),
    'k': (1, 0, 1),
    'l': (0, 1, 0, 0),
    'm': (1, 1),
    'n': (1, 0),
    'o': (1, 1, 1),
    'p': (0, 1, 1, 0),
    'q': (1, 1, 0, 1),
    'r': (0, 1, 0),
    's': (0, 0, 0),
    't': (1,),
    'u': (0, 0, 1),
    'v': (0, 0, 1),
    'w': (0, 1, 1),
    'x': (1, 0, 0, 1),
    'y': (1, 0, 1, 1),
    'z': (1, 1, 0, 0),
    '1': (0, 1, 1, 1, 1),
    '2': (0, 0, 1, 1, 1),
    '3': (0, 0, 0, 1, 1),
    '4': (0, 0, 0, 0, 1),
    '5': (0, 0, 0, 0, 0),
    '6': (1, 0, 0, 0, 0),
    '7': (1, 1, 0, 0, 0),
    '8': (1, 1, 1, 0, 0),
    '9': (1, 1, 1, 1, 0),
    '0': (1, 1, 1, 1, 1),
}

if __name__ == '__main__':
    main()
