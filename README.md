[![ResZip Cover](cover.jpg)](https://github.com/indiesoftby/defold-liveupdate-reszip)

# ResZip: use Live Update to improve load speed of HTML5 game

In short, HTML5 games should load **as fast as possible**! Why -> https://vimeo.com/350139974

It's important to deliver something meaningful to the user as soon as possible — the longer they wait for the game to load, the bigger the chance they will leave before waiting for everything to finish.

You can do the following things:
- Split your Defold game resources into two parts: resources required for the first level plus **everything else**. The game lazily loads more content or loads it on demand while players are playing the first level.
- Or make SD/HD versions of your atlases to lazily load HD graphics on game start (*the example will be added later*).

Defold has the [Live Update](https://defold.com/manuals/live-update/) feature that we can use to implement these ideas, and the project aims to demonstrate the usage of it. The project contains:

1. The Lua `liveupdate_reszip.reszip` module that downloads (with progress!) and extracts the missing resources.
2. [The magic JS code](liveupdate_reszip/manifests/web/engine_template.html) that removes Live Update cache from IndexedDB before the start of your game. This step is based on our experience of Live Update usage in Defold. Defold often fails to use the mix of resources from different versions of the game and the best solution is to clear its cache on every launch.
3. The Bash script (`example_build_script.sh`) shows you how to automatically build your game for the web and move the `resources.zip` file to your build result folder.

Check out the online demos:
1. [**Demo 1**](https://indiesoftby.github.io/defold-liveupdate-reszip/latest/index.html) - this project. **Tap anywhere to load level 2.**
2. [**Demo 2**](https://indiesoftby.github.io/defold-liveupdate-reszip/alt-version/index.html) - the same but with an alternative `resources.zip` file to test that it can handle upgrade of the game.

## Current Status

💬 Feel free to ask questions: [the topic about this asset is on the Defold forum](https://forum.defold.com/t/use-live-update-to-improve-load-speed-of-html5-game/67686).

| Asset Version   | Defold Version | Status        |
| --------------- | -------------- | ------------- |
| 1.3.0           | 1.5.0          | Tested ✅     |
| 1.2.0           | 1.4.7-8        | Tested ✅     |
| 1.2.0           | 1.4.6          | Doesn't work ❌ |
| 1.2.0           | 1.4.5          | Tested ✅     |

### Showcase

This is a list of some games that have used ResZip:

| Game            | Links | Extra |
| --------------- | ----- | ----- |
| Duo Vikings     | [Play it on Poki](https://poki.com/en/g/duo-vikings) |
| Duo Vikings 2   | [Play it on Poki](https://poki.com/en/g/duo-vikings-2) |
| Duo Vikings 3   | [Play it on Poki](https://poki.com/en/g/duo-vikings-3) |
| Fish Eat Fish   | [Play it on Poki](https://poki.com/en/g/fish-eat-fish) | The total size of the game is only 4 MB! After its start, it downloads the HD version of the graphics (~10MB) and applies it depending on the hardware capabilities. |
| Monkey Mart     | [Play it on Poki](https://poki.com/en/g/monkey-mart) | In the zip archive the game stores and downloads the resources needed for the next levels (shops). |
| Puffy Cat       | [Play it on Poki](https://poki.com/en/g/puffy-cat) | The game loads only 750 KB of data for the first three levels. Everything else (5 MB) is lazily downloaded from the `resources.zip` file. |
| Puffy Cat 2     | [Play it on Poki](https://poki.com/en/g/puffy-cat-2) | Only music and some sounds have been cut out from the game data into the `resources.zip` file. |

## Installation

1. Use it in your own project by adding this project as a [Defold library dependency](http://www.defold.com/manuals/libraries/). Open your `game.project` file and in the dependencies field under project add:

https://github.com/indiesoftby/defold-liveupdate-reszip/archive/main.zip

2. Follow the [Live Update tutorial](https://defold.com/manuals/live-update/) on the Defold website and exclude chosen collections in proxies.
3. Use the `Zip` mode for Live Update and publish the Live Update content through `Project / Bundle...` or using `bob.jar` (the arg is `--liveupdate yes`).
4. Move the resulting .zip file with resources into your production build folder.
5. Look at the `example/main.script` to learn how to check for the missing resources and how to load them from the `.zip` resources file.

### Tips

The easiest way to use ResZip in your project is to move some of your audio files (i.e. sound components) to a proxied collection and exclude the collection for the release build. To play these sounds, you should make an external script that acts as a sound manager of all your in-game audio and knows when proxied sounds are loaded from the `resources.zip` file.

Also, you can remove an unused manifest from the `resources.zip` file to reduce its size: 

```bash
7z d -r resources.zip liveupdate.game.dmanifest
```

### Advanced Usage

ResZip can start preloading the `resources.zip` file as soon as game loading is finished. It's highly recommended to enable this option:

```ini
[liveupdate_reszip]
preload_file = your_resources_file_name.zip
```

#### Deprecated options

~~If the `resources.zip` file contains hundreds or thousands of resources, you can speed up the process of loading resources by enabling batching (only for HTML5!):~~

```lua
reszip.RESOURCES_PER_BATCH = 10
reszip.BATCH_MAX_TIME = 0 -- Seconds. Set 0 or less to disable.
```

## Credits

This project is licensed under the terms of the CC0 1.0 Universal license. It's developed and supported by [@aglitchman](https://github.com/aglitchman). 

Also, the project uses [miniz](https://github.com/richgel999/miniz), a MIT-licensed data compression library.

The demo contains third-party music files which require attribution:
```
Ethernight Club by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/7612-ethernight-club
License: https://filmmusic.io/standard-license
```
