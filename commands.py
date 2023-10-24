from urllib.parse import quote as urlquote
from collections import OrderedDict as odict
import json

import requests

import stuff


listener = stuff.listener


@listener(pattern="syslog.*")
def syslog(c, p, m, redis):
    """
    Syslog to IRC
    """
    redis.publish("toirc.#Syslog", "%s %s" % (c.split(".", 1)[1], m))


@listener(channel="email")
def email(c, p, email, redis):
    """
    Email handler if you have a script that sends your mail topics through a Redis channel.
    A message is in the format
    1337 2023-10-20 16:14:47 example@example.com This is an email subject
    |    |          |        |                   |
    id   day        time     sender              subject
    """
    s = email.split(" ", 4)
    if len(s) != 5:
        return
    id, day, time, sender, subject = s

    # Mute a sender
    if sender == "newsletter@email2.gog.com":
        return
    # Or a bunch of other things we do not want to see
    if (
        sender.endswith("@facebookmail.com")
        or subject == "You have sold an item on the Community Market"
        or "gemenskapsmarknaden" in subject
    ):
        return

    morse = None
    if sender == "no-reply@twitch.tv":
        # Example list of streamers (that I saw playing factorio on twitch)
        streamers = "mikelat", "sfhobbit", "maholic"
        slower = subject.lower()
        if any(s in slower for s in streamers):
            # Special beeps for some steamers to let you know they are on
            morse = "vip"
            redis.publish("led4", "1")
        elif "live:" in subject:
            # Normal beeps for streamers not in the list
            morse = "s"
            redis.publish("led2", "1")
    elif sender == "info@picarto.tv":
        # Special beeps for some senders
        morse = "s"
        redis.publish("led2", "1")
    else:
        morse = "m"
        # Turn on a certain LED (see addons/led)
        redis.publish("emailed", "1")
    if "humblebundle.com" in sender and "FREE" in subject:
        # What if we wanted to make a certain LED light up on a certain subject
        morse = "FREE"
        # This sets the led but it is cleared with the handler irccommands in this file
        redis.publish("led1", "1")

    # Send the mail subject and sender and alike to irc (see addons/irc)
    if email:
        redis.publish("toirc.#M", email)
    # If there is a message to beep then morse beep it (see addons/morse)
    if morse:
        redis.publish("morse", morse)


@listener(channel="boterror")
def boterror(c, p, m, redis):
    """
    This was used for something
    """
    redis.publish("boterrorlocal", m)


@listener(channel="boterrorlocal")
def boterrorlocal(c, p, m, redis):
    """
    Add IRC colors to error messages before sending them to IRC
    """
    color = "\x037,99"
    redis.publish("toirc.#W", color + m.strip().replace("\n", "\n" + color))


@listener(channel="botoutputlocal")
def botoutputlocal(c, p, m, redis):
    """
    Another simple handler for output of bots mostly for use while testing
    """
    redis.publish("toirc.#J", m)


@listener(channel="discorderror")
def discorderror(c, p, m, redis):
    """
    What if you want to send various errors to Discord for easy viewing
    replace this with the id of the channel
    """
    channel = ...
    redis.publish(f"discord.cin.{channel}", m)


@listener(channel="discordnagios")
def discordnagios(c, p, m, redis):
    """
    Why not send statuses from Nagios to discord (see addons/nagios)
    for easy monitoring when you are away
    replace this with the id of the channel
    """
    channel = ...
    redis.publish(f"discord.cin.{channel}", m)


@listener(channel=["fromirc.#A", "fromirc.#All"])
def irccommands(c, p, m, redis):
    """
    Listen to commands from irc (see addons/irc)
    This is mostly for cleaning leds set in the email handler
    but you can add what you want here
    """
    s = m.split(" ", 1)
    if len(s) != 2:
        return
    user, msg = s
    s2 = msg.split(" ", 1)
    cmd = s2[0]
    arg = s2[1] if len(s2) == 2 else ""
    if cmd in ("m", "'"):
        redis.publish("emailed", 0)
    elif cmd in ("l%s" % a for a in range(1, 9)):
        redis.publish("led" + cmd[1:], arg)
    elif cmd == "s":
        redis.publish("led2", 0)


@listener(pattern="octoprintlog.*.*")
def octoprintlogtoirc(c, p, m, redis):
    """
    Octoprint to IRC thing that uses some webhook that is called from another machine
    """
    j = json.loads(m, object_pairs_hook=odict)
    u, n = c.split(".", 2)[1:]
    s = " ".join(
        "%s=%s"
        % (
            k,
            (repr(v)[1:] if isinstance(v, str) else repr(v))
            if any(f in v for f in (" ", "\t", "\r", "\n"))
            else v,
        )
        for k, v in j.items()
    )
    redis.publish("toirc.#Oct", "%s %s %s" % (u, n, s))


@listener(channel="iot.err")
def ioterrtoirc(c, p, m, redis):
    """
    Internal errors from this script to local error notifier
    """
    redis.publish("boterrorlocal", m)


@listener(channel="aio.twitchstatus")
def twitchannounce(c, p, m, redis):
    """
    I used to have a thing where it listened to
    twitch online notifications that later broke down
    so the notifier for this is moved to the email handler
    but including this as an example of what you can do
    """
    j = json.loads(m)
    if not j["handle"]:
        return
    if 1:
        if j["on"]:
            try:
                j["game_id"] = j["raw"][0]["game_id"]
            except:
                j["game_id"] = "UNKNOWN"
            redis.publish("led2", 1)
            redis.publish("morse", "s")
            fmt = "{handle}({userid}) is now streaming {game_id} {title}"
        else:
            fmt = "{handle}({userid}) is no longer streaming"
        msg = fmt.format(**j)
        redis.publish("toirc.#S", msg)


@listener(channel="junk")
def junk(c, p, m, redis):
    """
    A simple handler that just redirects to an IRC channel
    """
    redis.publish("toirc.#J", m)


@listener(channel="aio.youtube")
def youtube(c, p, m, redis):
    """
    Used for a youtube upload notifier through pubsubhubbub but not sure if it still works
    """
    redis.publish("toirc.#Y", m)


@listener(channel=["aio.servererror", "aio.iot.err"])
def serverr(c, p, m, redis):
    """
    If there are errors on the VPS they are sent down to be printed on the local IRC server
    they are sent through a websocket which the server
    """
    # redis.publish('toirc.#W', '\n'.join('Server ' + a for a in m.split('\n')))
    redis.publish("toirc.#W", "Server " + m)


@listener(channel="aio.terrjoinquits")
def terrjoinquits(c, p, m, redis):
    """
    A join notifier for Terraria so when players join it does a beep
    """
    s = m.split(" ", 1)
    on, player = bool(int(s[0])), s[1]
    if on:
        redis.publish("morse", "T")


@listener(channel="aio.dxupdates")
def dxupdates(c, p, m, redis):
    """
    Part of a Dropbox change notifier that uses a webhook
    """
    j = json.loads(m)
    for a in j:
        if a[0]:
            msg = "Update %s %s" % (a[1]["path_display"], a[1]["size"])
        else:
            msg = "Delete %s" % (a[1]["path_display"],)
        redis.publish("toirc.#D", msg)


@listener(pattern="discord.cin.*")
def discordcin(c, p, m, redis):
    """
    A crude way of sending messages on Discord for this script that should be improved
    """
    h = c.split(".", 2)[2]
    # Token for your bot below
    token = ...
    r = requests.post(  # TODO: Split messages
        "https://discordapp.com/api/v6/channels/%s/messages" % (h,),
        headers=dict(Authorization="Bot " + token),
        data=dict(content=m),
        timeout=60,
    )
    if r.status_code != 200:
        # Example of error handling
        redis.publish("boterror", r.content)


@listener(channel="errorreport")
def errorreport(c, p, m, redis):
    """
    Example of a handler that receives reports of failed commands through a wrapper
    """
    j = json.loads(m)
    s = j.get("service")
    e = j.get("error")
    o = j.get("output")
    c = j.get("code")
    d = j.get("command")
    w = j.get("cwd")
    h = j.get("host")
    t = "%s on %s exited with code %s\nCommand: %s\nDir %s" % (s, h, c, d, w)
    if e:
        t += "\n" + str(e)
    if o:
        t += "\nOutput: %s" % o
    redis.publish("boterror", t)


@listener(channel="dbotjout")
def discordevent(c, p, m, redis):
    """
    Listen to specific events on Discord and handle them
    """
    d = json.loads(m)
    t = d["t"]
    if t in ("GUILD_MEMBER_ADD",):
        redis.publish("boterrorlocal", m)


@listener(channel="morse")
def morse(c, p, m, redis):
    """
    Send morse beeps to IRC too (see addons/irc and addons/morse) so you know what they are
    """
    redis.publish("toirc", "Morse " + m)


@listener(channel="winbsupl")
def blackwinscrupload(c, p, m, redis):
    """
    Screenshots that are taken are linked on IRC and send to the image viewer
    """
    redis.publish("toirc.#P", "BlackWin " + m)
    redis.publish("imgin", "http://192.168.0.43/screenshots/windows/" + urlquote(m))


if __name__ == "__main__":
    print("\n".join("%s" % l.get() for l in stuff.listeners))
