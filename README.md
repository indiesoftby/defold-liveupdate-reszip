# ResZip. Use LiveUpdate to improve load speed of HTML5 game

In short, HTML5 games should load **as fast as possible**! 

The possible solution is to split resources in the Defold game into two parts: all resources required for the first level of your game plus *the rest resources*. The game loads the rest while players are playing the first level. Defold has the [LiveUpdate](https://defold.com/manuals/live-update/) feature that we can use to implement this idea.

This project aims to demonstrate the usage of LiveUpdate for HTML5 games. It contains:
1. The `liveupdate_reszip.reszip` module that loads and extracts the missing resources.
2. Travis CI script `.travis.yml` shows you how to automatically build your game and prepare the `resources.zip` file.

The project uses [Miniz](https://github.com/richgel999/miniz), a data compression library. Take into account that it increases your release build size on 20KB.

# WORK IN PROGRESS

[**Online demo 🐲**](https://indiesoftby.github.io/defold-liveupdate-reszip/latest/index.html)

## Installation

1. Use it in your own project by adding this project as a [Defold library dependency](http://www.defold.com/manuals/libraries/). Open your `game.project` file and in the dependencies field under project add:

https://github.com/indiesoftby/defold-liveupdate-reszip/archive/main.zip

2. 

## Advanced Usage

You can to remove an unused manifest from the `resources.zip` file: 

```bash
7z d -r resources.zip liveupdate.game.dmanifest
```

