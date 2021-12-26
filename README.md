[![ResZip Cover](cover.jpg)](https://github.com/indiesoftby/defold-liveupdate-reszip)

# ResZip: use Live Update to improve load speed of HTML5 game

In short, HTML5 games should load **as fast as possible**! Why -> https://vimeo.com/350139974

It's important to deliver something meaningful to the user as soon as possible — the longer they wait for the game to load, the bigger the chance they will leave before waiting for everything to finish.

The solution is to split your Defold game resources into two parts: resources required for the first level plus **everything else**. The game lazily loads more content or loads it on demand while players are playing the first level. Defold has the [Live Update](https://defold.com/manuals/live-update/) feature that we can use to implement this idea, and the project aims to demonstrate the usage of it.

This project contains:
1. The `liveupdate_reszip.reszip` module that loads and extracts the missing resources.
2. Travis CI script `.travis.yml` shows you how to automatically build your game and prepare the `resources.zip` file.
3. [The magic JS code](liveupdate_reszip/manifests/web/engine_template.html) that removes temporary Live Update files before the start of your game.

Check out the online demos:
1. [**Demo 1**](https://indiesoftby.github.io/defold-liveupdate-reszip/latest/index.html) - this project. **Tap anywhere to load level 2.**
2. [**Demo 2**](https://indiesoftby.github.io/defold-liveupdate-reszip/alt-version/index.html) - the same but with an alternative `resources.zip` file to test that it can handle upgrade of the game.

## Current Status

💬 Feel free to ask questions: [the topic about this asset is on the Defold forum](https://forum.defold.com/t/use-live-update-to-improve-load-speed-of-html5-game/67686).

| Asset Version   | Defold Version | Status        |
| --------------- | -------------- | ------------- |
| 1.1.1           | 1.2.190        | Tested ✅     |

### Showcase

This is a list of some games that have used ResZip:

| Game            | Links               |
| --------------- | ------------------- |
| Duo Vikings 3   | [Play it on Poki](https://poki.com/en/g/duo-vikings-3) |
| Puffy Cat       | [Play it on Poki](https://poki.com/en/g/puffy-cat) |
| Puffy Cat 2     | [Play it on Poki](https://poki.com/en/g/puffy-cat-2) |

## Installation

1. Use it in your own project by adding this project as a [Defold library dependency](http://www.defold.com/manuals/libraries/). Open your `game.project` file and in the dependencies field under project add:

https://github.com/indiesoftby/defold-liveupdate-reszip/archive/main.zip

2. Follow the [Live Update tutorial](https://defold.com/manuals/live-update/) on the Defold website and exclude chosen collections in proxies. Use the `Zip` mode for Live Update and publish the Live Update content through `Project / Bundle...` or using `bob.jar` (the arg is `--liveupdate yes`). Move the resulting .zip file with resources into your production build folder.
3. Look at the `example/main.script` to learn how to check for the missing resources and how to load them from the .zip resources file.

### Advanced Usage

You can to remove an unused manifest from the `resources.zip` file to reduce its size: 

```bash
7z d -r resources.zip liveupdate.game.dmanifest
```

## Credits

This project is licensed under the terms of the CC0 1.0 Universal license. It's developed and supported by [@aglitchman](https://github.com/aglitchman). 

Also, the project uses [miniz](https://github.com/richgel999/miniz), a data compression library.

The demo contains third-party music files which require attribution:
```
Ethernight Club by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/7612-ethernight-club
License: https://filmmusic.io/standard-license
```
