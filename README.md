### IOTReact 
Which is this is named is an internal project I have used for many years for all kinds of internet of things things and smart home stuff so it practically connects to all smart home devices in the house. Essentially it redirects redis pubsub channels using small functions so you can quickly make small implementations of different smart home functions. I have worked on this for maybe around 10 years as of when this is written (2023) and used it in so many different small and large projects.

Here are some fun things that have been made with it:
1. Home security systems such as activating security cameras when sensors detect movements or alike
2. Post done 3D prints in octoprint in a Slack channel
3. Post error messages from different scripts and bots on Discord
4. Monitor your email for certain mails and beep morse code if they have certain subjects
5. Redirect certain logs to IRC
6. Monitor arpwatch and notify several people of what new devices pop up
7. Start a program when a certain message is encountered
8. Bridge game server chats to IRC or discord chats
9. Make a central error handler for your bots and scripts
10. Beep morse code that is unique for every door in the house when opened

In the `addons` folder there are many addons that have been made for this and they have their own `README.md` for each of them

This is not meant as some product or anything like that but more like some fun code to study for learning what cool things you can do with programming especially related to smart home and internet of things

This assumes that you have a local IRC server and some kind of chat client connected to it like weechat as that is what I use but it will still work anyway but most examples use it

How you use this is you edit `commands.py` (there is a convenient script called `iote` for it) and you put in the handlers you want and they will be run when the matching redis pubsub channel has a message

Some things here might be very broken and some examples incomplete but if you are taking on in trying to use this in some capacity you probably already know how to fix that

Feel free to send pull requests or alike if you make your own addons or edits to this since it might be quite bug ridden and alike
