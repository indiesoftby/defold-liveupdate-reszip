# LiveUpdate with "resources.zip" Demo Project

The task is: loading time of HTML5 game should be **AS SHORT AS POSSIBLE**. The possible solution is to split resources in your game into two parts: all resources required for the first level of your game and the rest. The game loads the rest resources while players are playing the first level. Defold has the [LiveUpdate](https://defold.com/manuals/live-update/) feature that we can use for this task.

This project aims to demonstrate the usage of LiveUpdate for HTML5 games. It contains:
1. The `liveupdate_reszip.reszip` module that loads, extracts and stores the missing resources.
2. Travis CI script `.travis.yml` shows you how to automatically build your game and prepare the `resources.zip` file.

# WORK IN PROGRESS

[**Online demo 🐲**](https://indiesoftby.github.io/defold-liveupdate-reszip/latest/index.html)

## Installation

You can use it in your own project by adding this project as a [Defold library dependency](http://www.defold.com/manuals/libraries/). Open your `game.project` file and in the dependencies field under project add:

https://github.com/indiesoftby/defold-liveupdate-reszip/archive/main.zip

Or point to the ZIP file of a [specific release](https://github.com/indiesoftby/defold-liveupdate-reszip/releases).

## Usage

...
