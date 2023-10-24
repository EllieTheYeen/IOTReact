### PiLED
This will let you control a few LEDs through the Redis channels led1 to led8 that are turned on and off if the value in the channel that it listens to is considered truthy and also a special one called emailed that is made to light up when email comes and then cleared by a command.

You should connect 9 LEDs to the Raspberry pi for this unless you change the configuration.

Run like `python3 piled.py` (It is forking)
