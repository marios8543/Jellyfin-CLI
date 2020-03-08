# Jellyfin CLI

##### A Jellyfin command line client written in Python with urwid.  
![Image](https://i.imgur.com/I3Nbd3R.png)
----

### How to use
This app requires Python3.6 or higher  
You can install it by executing `pip3 install --user jellyfin-cli`  
The first time you run it, you will be greeted by a minimalist login prompt. This will repeat every time the token is invalidated.
After that you can use the interface. Everything except music works.  
Player-wise MPV and VLC are supported out of the box but typically any player that supports network streaming (and that doesn't require any flags) will work. You can specify a custom player path through the `PLAYER_PATH` environment variable.

### Development

Want to contribute? Sure! You are free to create bug reports, feature requests and pull requests. I will try my best to review all of them.