#!/usr/bin/python3
from twisted.internet import protocol, defer, reactor
from twisted.words.protocols import irc
import txredisapi as redis
import os


class IRCBot(irc.IRCClient):
    versionName = "IOTReact"
    fingerReply = "IOTReact"
    userinfo = "Announcement bot for IOTReact"
    sourceURL = "https://github.com/EllieTheYeen/IOTReact/"
    nickname = "IOTReact"
    realname = "IOTReact"

    lineRate = 1

    channels = set()

    def signedOn(self):
        print("Signed on")
        for c in ichans:
            self.join(c)

    def noticed(self, user, chan, msg):
        pass

    def lineReceived(self, line):
        irc.IRCClient.lineReceived(self, line)

    def privmsg(self, user, chan, msg):
        if not red:
            return
        if chan.startswith("#") or chan.startswith("&"):
            red.publish("fromirc.%s" % chan, (user.split("!")[0]) + " " + msg)
        else:
            red.publish("fromirc.%s" % (user.split("!")[0]), msg)

    def joined(self, chan):
        try:
            self.channels.add(chan)
        except:
            pass

    def left(self, chan):
        try:
            self.channels.remove(chan)
        except:
            pass

    def connectionLost(self, reason=None):
        irc.IRCClient.connectionLost(self, reason)


class IRCBotFactory(protocol.ReconnectingClientFactory):
    def buildProtocol(self, addr):
        global bot
        self.resetDelay()
        bot = IRCBot()
        bot.factory = self
        return bot


class Subscriber(redis.SubscriberProtocol):
    def connectionMade(self):
        self.subscribe(inp)
        self.subscribe(raw)
        self.psubscribe(patternto)

    def messageReceived(self, pattern, channel, message):
        if debug:
            print(channel, pattern, message)
        if not bot:
            return
        message = str(message)
        if channel == "toirc":
            channel = "toirc.#K"
            pattern = patternto
        if pattern == patternto:
            if "." not in channel:
                return
            chan = channel.split(".", 1)[1]
            if chan.startswith("#"):
                if chan not in bot.channels:
                    bot.join(chan)
                    # Not sure what this does but tell me if you know
                    bot.sendLine("MODE %s -n" % (chan,))
                    bot.sendLine("MODE %s -o %s" % (chan, bot.username))
                col = "\x03" + chancols[chan[1:]] if chan[1:] in chancols else ""
                if chan.lower() not in ignchans:
                    for msg in message.split("\n"):
                        bot.msg("#All", "%s%s %s" % (col, chan, msg))
                if len(chan) == 2 and chan != "#A":
                    for msg in message.split("\n"):
                        bot.msg("#A", "%s%s %s" % (col, chan, msg))

            for msg in message.split("\n"):
                bot.msg(chan, msg)
        elif channel == raw:
            bot.sendLine(message)


class SubscriberFactory(redis.SubscriberFactory):
    protocol = Subscriber
    maxDelay = 120
    continueTrying = True

    def buildProtocol(self, addr):
        if debug:
            print("Redis sub connected", addr)
        p = self.protocol()
        p.factory = self
        self.resetDelay()
        return p


@defer.inlineCallbacks
def redcon():
    global red
    red = yield redis.Connection(charset=None)
    if debug:
        print("Redis pub connected", red)


bot = None
red = None

ignchans = "#all", "#syslog", "#chat"  # Must be lowercase
ichans = "#K", "#A", "#All", "#Syslog", "#Chat"
raw = "rawtoirc"
inp = "toirc"
out = "fromirc"
patternto = "toirc.*"
# Color for certain channels for when they apppear in #All
chancols = dict(
    K="10,01",
    M="8,01",
    N="5,01",
    J="4,01",
    W="7,01",
    S="6,01",
    T="11,01",
    # Messages that are longer than a letter in name will be send to #All but not #A
    Example1="12,01",
    Example2="15,01",
)

debug = 0


def main():
    # log.startLogging(sys.stdout)
    # Connect to Redis sub
    reactor.connectTCP("127.0.0.1", 6379, SubscriberFactory())
    # Connect to IRC local server
    reactor.connectTCP("127.0.0.1", 6667, IRCBotFactory())
    reactor.callWhenRunning(redcon)
    reactor.run()


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


if __name__ == "__main__":
    fork(main)
