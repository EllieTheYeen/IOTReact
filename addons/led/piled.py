#!/usr/bin/python
import RPi.GPIO as GPIO
import redis
import time
import os


def listen(p, subs=(), psubs=()):
    if not subs and not psubs:
        raise ValueError("Must have subs")
    c = False
    t = 0
    while True:
        try:
            if subs:
                p.subscribe(*subs)
            if psubs:
                p.psubscribe(*psubs)
            t = 0
            c = True
            # print('Connected')
            for a in p.listen():
                yield a
        except redis.exceptions.ConnectionError:
            if c:
                c = False
                # print('Disconnected')
            # print('Connection failed, waiting %s seconds' % t)
            time.sleep(t)
            if not t:
                t = 1
            else:
                t *= 2
                if t > 60:
                    t = 60


def main():
    try:
        GPIO.setmode(GPIO.BCM)
        r = redis.Redis()
        chans = []
        # import time
        for channel, pin in channels.items():
            chans.append(channel)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

        for a in listen(r.pubsub(), subs=chans):
            if a["type"] != "message":
                continue
            chan = a["channel"]
            data = a["data"]
            try:
                chan = chan.decode("utf8")
                data = data.decode("utf8")
            except:
                continue
            stat = (
                False if data.lower() in ("0", "off", "false", "no", "n", "") else True
            )
            if chan in channels:
                GPIO.output(channels[chan], stat)

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


pins = 26, 27, 16, 25, 23, 17, 22, 6
channels = dict(emailed=5)
for a in range(8):
    channels["led%s" % (a + 1)] = pins[a]

print(channels)

if __name__ == "__main__":
    fork(main)
