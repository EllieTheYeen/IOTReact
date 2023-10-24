### ToIRC
An IRC bot that joins IRC and is meant for local IRC servers.

Redis messages where the channel starts with toirc.* is sent to IRC where the message is the content.

IRC messages are sent to the Redis channels fromirc.* where the first word separated by space is the username of the sender and the rest is the message.

Run like `python3 toirc.py` (It is forking)
