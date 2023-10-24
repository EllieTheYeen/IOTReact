#!/usr/bin/python3
import importlib
import traceback
import threading
import datetime
import signal
import time

import redis

import commands
import stuff


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


def handle(*a):
    print("handled")
    rehash()


def gethandlers(thing):
    channelhandlers = dict()
    patternhandlers = dict()

    patterns = set()
    channels = set()

    for listener in thing.listeners:
        a = listener.get()
        out = a["out"]
        func = a["func"]
        sync = a["sync"]
        pattern = a["pattern"]
        if pattern is not None:
            spatterns = [pattern] if isinstance(pattern, str) else pattern
            patterns.update(spatterns)
            for spattern in spatterns:
                phandlers = patternhandlers.setdefault(spattern, [])
                phandlers.append(dict(func=func, sync=sync, out=out))
        channel = a["channel"]
        if channel is not None:
            schannels = [channel] if isinstance(channel, str) else channel
            channels.update(schannels)
            for schannel in schannels:
                pchannels = channelhandlers.setdefault(schannel, [])
                pchannels.append(dict(func=func, sync=sync, out=out))
    return patterns, channels, patternhandlers, channelhandlers


def updatesubscriptions():
    global patterns, channels, patternhandlers, channelhandlers
    oldpatterns = patterns
    oldchannels = channels
    patterns, channels, patternhandlers, channelhandlers = gethandlers(stuff)
    for pattern in patterns - oldpatterns:
        psubscribe(pattern)
    for channel in channels - oldchannels:
        subscribe(channel)
    for pattern in oldpatterns - patterns:
        punsubscribe(pattern)
    for channel in oldchannels - channels:
        unsubscribe(channel)


def rehash():
    try:
        stuff.listeners = []
        importlib.reload(commands)
        updatesubscriptions()
        r.publish("iot.out", "reloaded")
    except Exception as e:
        traceback.print_exc()
        r.publish("iot.err", traceback.format_exc())


def runcallbacks(handlers, channel, pattern, message):
    for handler in handlers:

        def function():
            try:
                out = handler["out"]
                func = handler["func"]
                d = dict()
                extras = func.__code__.co_varnames
                if "redis" in extras:
                    d["redis"] = r
                response = func(channel, pattern, message, **d)
                if response is not None:
                    r.publish("iot.out", response)
            except Exception as e:
                t = datetime.datetime.now()
                m = traceback.format_exc()
                print(t, handler["func"].__name__)
                print("\n".join("%s %s" % (t, a) for a in m.split("\n")))
                r.publish("iot.err", traceback.format_exc())

        if handler["sync"]:
            function()
        else:
            t = threading.Thread(target=function)
            t.daemon = True
            t.start()


def handleiotrcommand(cmd):
    if cmd == "reload":
        rehash()
    elif cmd == "shutdown":
        r.publish("iot.out", "shutting down")
        exit()


def subscribe(channel):
    if debug:
        print("Subscribe:", channel)
    p.subscribe(channel)


def unsubscribe(channel):
    if debug:
        print("Unsubscribe:", channel)
    p.unsubscribe(channel)


def psubscribe(pattern):
    if debug:
        print("Psubscribe:", pattern)
    p.psubscribe(pattern)


def punsubscribe(pattern):
    if debug:
        print("Punubscribe:", pattern)
    p.punsubscribe(pattern)


patterns = set()
channels = set()

systemchannels = ("iotrc",)

signal.signal(1, handle)


def main():
    r = redis.Redis()
    p = r.pubsub()
    updatesubscriptions()
    subscribe("iotrc")
    r.publish("iot.out", "starting up")

    for a in listen(p, subs=channels, psubs=patterns):
        if debug:
            print("Message:", a)
        type = a["type"]
        channel = a["channel"]
        channel = (
            channel
            if isinstance(channel, str)
            else (channel and channel.decode("utf8"))
        )
        pattern = a["pattern"]
        pattern = (
            pattern
            if isinstance(pattern, str)
            else (pattern and pattern.decode("utf8"))
        )
        data = a["data"]
        try:
            data = data.decode("utf8")
        except:
            pass
        if debug:
            print((type, channel, pattern, data))
        if type == "message":
            if channel == "iotrc":
                handleiotrcommand(data)
                continue
            runcallbacks(channelhandlers.get(channel, []), channel, None, data)
        elif type == "pmessage":
            runcallbacks(patternhandlers.get(pattern, []), channel, pattern, data)
        elif type == "subscribe":
            if channel and channel not in channels and channel not in systemchannels:
                unsubscribe(channel)
        elif type == "psubscribe":
            if pattern and pattern not in patterns:
                punsubscribe(pattern)


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


debug = 0

if __name__ == "__main__":
    fork(main)
