[![ResZip Cover](cover.jpg)](https://github.com/indiesoftby/defold-liveupdate-reszip)

# ResZip: use Live Update to improve load speed of HTML5 game

In short, HTML5 games should load **as fast as possible**! Why -> https://vimeo.com/350139974

It's important to deliver something meaningful to the user as soon as possible — the longer they wait for the game to load, the bigger the chance they will leave before waiting for everything to finish.

You can do the following things:
- Split your Defold game resources into two parts: resources required for the first level plus **everything else**. The game lazily loads more content or loads it on demand while players are playing the first level.
- Or make SD/HD versions of your atlases to lazily load HD graphics on game start (*the example will be added later*).

Defold has the [Live Update](https://defold.com/manuals/live-update/) feature that we can use to implement these ideas, and the project aims to demonstrate the usage of it. The project contains:

- The Lua `liveupdate_reszip.reszip` module that downloads (with progress!) and mounts the missing resources.
- The Bash script (`example_build_script.sh`) shows you how to automatically build your game for the web and move the `resources.zip` file to your build result folder.

Check out the online demos:
1. [**Demo 1**](https://indiesoftby.github.io/defold-liveupdate-reszip/latest/index.html) - this project. **Tap anywhere to load level 2.**
2. [**Demo 2**](https://indiesoftby.github.io/defold-liveupdate-reszip/alt-version/index.html) - the same but with an alternative `resources.zip` file to test that it can handle upgrade of the game.

## Current Status

💬 Feel free to ask questions: [the topic about this asset is on the Defold forum](https://forum.defold.com/t/use-live-update-to-improve-load-speed-of-html5-game/67686).

| Asset Version   | Defold Version | Status        |
| --------------- | -------------- | ------------- |
| 1.4.0           | 1.6.1          | Tested ✅     |
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
5. Look at the `example/main.script` to learn how to check for the missing resources and how to mount the `.zip` resources file:

```lua
local zip_filename = sys.get_config("liveupdate_reszip.filename", "resources.zip")
local zip_file_location = (html5 and zip_filename) or ("http://localhost:8080/" .. zip_filename)
local excluded_proxy_url = "/level2#collectionproxy"

local missing_resources = collectionproxy.missing_resources(excluded_proxy_url)
if next(missing_resources) ~= nil then
    print("Some resources are missing, so download and mount the resources archive...")
    assert(liveupdate, "`liveupdate` module is missing.")

    reszip.load_and_mount_zip(zip_file_location, {
        on_finish = finish_handler,
        on_progress = http_loading_progress_handler
    })
else
    -- All resources exist, so load the level:
    print("Resources are already loaded. Let's load level 2!")
    msg.post(excluded_proxy_url, hash("load"))
end
```

> [!IMPORTANT]
> The above example assumes that the `wipe_on_start = 1` option is enabled (see below!), which allows you to not worry about detecting the version of mounted resources when upgrading versions of your game.

### Tips

The easiest way to use ResZip in your project is to move some of your audio files (i.e. sound components) to a proxied collection and exclude the collection for the release build. To play these sounds, you should make an external script that acts as a sound manager of all your in-game audio and knows when proxied sounds are loaded from the `resources.zip` file.

### Advanced Usage

#### Preload resources

ResZip can start preloading the `resources.zip` file as soon as game loading is finished. It's highly recommended to enable this option because the engine initialisation takes some time, during which we can already start loading resources:

```ini
[liveupdate_reszip]
preload_file = your_resources_file_name.zip
```

If you suspect a bug in Live Update or ResZip, the following option can be used to force Live Update data to be completely cleared before the game starts:

```ini
[liveupdate_reszip]
wipe_on_start = 1
```

## Credits

This project is licensed under the terms of the CC0 1.0 Universal license. It's developed and supported by [@aglitchman](https://github.com/aglitchman). 

The demo contains third-party music files which require attribution:
```
Ethernight Club by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/7612-ethernight-club
License: https://filmmusic.io/standard-license
```
