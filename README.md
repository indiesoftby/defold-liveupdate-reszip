[![ResZip Cover](cover.jpg)](https://github.com/indiesoftby/defold-liveupdate-reszip)

# ResZip

A ready-to-use Lua module and example project on how to use LiveUpdate to download extra content in your game. In the world of HTML5 games, we use this to speed up the delivery of the game, as every second counts!

## Detailed Explanation

It's important to deliver something meaningful to the user as soon as possible — the longer they wait for the game to load, the bigger the chance they will leave before waiting for everything to finish. Why? The video explains that well: https://vimeo.com/350139974

You can do the following things:
- Split your Defold game resources into two parts: resources required for the first level plus **everything else**. The game lazily loads more content or loads it on demand while players are playing the first level.
- Or make SD/HD versions of your atlases to lazily load HD graphics on game start.

Defold has the [Live Update](https://defold.com/manuals/live-update/) feature that we can use to implement these ideas, and the project aims to demonstrate the usage of it. The project contains:

- The Lua `liveupdate_reszip.reszip` module that downloads (with progress!) and mounts the missing resources.
- The Bash script (`example_build_script.sh`) shows how to build the web version and put the resource archive into the bundle automatically.

Check out the online demos:
1. [**Demo 1**](https://indiesoftby.github.io/defold-liveupdate-reszip/bundle-1/index.html) - this project. **Tap anywhere to load level 2.**
2. [**Demo 2**](https://indiesoftby.github.io/defold-liveupdate-reszip/bundle-2/index.html) - the same but with an alternative `resources.zip` file to test that it can handle upgrade of the game.
3. [**Demo 3**](https://indiesoftby.github.io/defold-liveupdate-reszip/old-version/index.html) - built with Defold 1.6.2 and the old LiveUpdate API. Use it before demo 1 or 2 to test upgrading an existing browser installation.

## Current Status

💬 Feel free to ask questions: [the topic about this asset is on the Defold forum](https://forum.defold.com/t/use-live-update-to-improve-load-speed-of-html5-game/67686).

| Asset Version   | Defold Version | Status        |
| --------------- | -------------- | ------------- |
| main            | 1.13.1         | Tested ✅     |

## Showcase

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

### 1. Add dependency

Use it in your own project by adding this project as a [Defold library dependency](http://www.defold.com/manuals/libraries/). Open your `game.project` file and in the dependencies field under project add:

https://github.com/indiesoftby/defold-liveupdate-reszip/archive/main.zip

### 2. Prepare your project

Follow the [Live Update tutorial](https://defold.com/manuals/live-update/) on the Defold website and exclude chosen collections in proxies.

Look at the `example/main.script` to learn how to check for the missing resources and how to download and mount the `.zip` resources file:

```lua
-- Paths to the resources files
local zip_filename = sys.get_config_string("liveupdate_reszip.filename", "resources.zip")
local zip_file_location = zip_filename
if not html5 then
    -- You must host your resource file on any hosting service:
    zip_file_location = "http://localhost:8080/" .. zip_filename
end

-- URL of the excluded proxy:
local excluded_proxy_url = "/level2#collectionproxy"

local function is_built_with_excluded_resources()
    if not liveupdate then
        return false
    end
    if liveupdate.is_built_with_excluded_files then
        return liveupdate.is_built_with_excluded_files()
    end
    return next(collectionproxy.get_resources(excluded_proxy_url)) ~= nil
end

-- ResZip mounts the saved archive for this bundle version, or downloads it
-- when it is not available.
if is_built_with_excluded_resources() and not reszip.version_match(zip_filename) then
    print("Mount or download the resources archive...")

    reszip.load_and_mount_zip(zip_file_location, {
        filename = zip_filename,
        delete_old_file = true,
        on_finish = function (self, err)
            if not err then
                -- All resources are loaded, finally load the level:
                print("Everything is OK, load level 2!")
                msg.post(excluded_proxy_url, hash("load"))
            else
                -- Try again?...
                print("ERROR: " .. err)
            end
        end,
        on_progress = function (self, loaded, total)
            -- Update progress in your GUI:
            -- local progress = string.format("%dKB / %dKB", loaded / 1024, total / 1024)
            -- label.set_text("#loading_progress", progress)
        end
    })
else
    -- LiveUpdate is not enabled, i.e. we test the game from IDE. Or all resources exist, so load the level:
    print("Resources are already loaded. Let's load level 2!")
    msg.post(excluded_proxy_url, hash("load"))
end
```

> [!IMPORTANT]
> The example above assumes that you name the resource file differently for each version of the game (`resources_v1.zip`, `resources_v2.zip`). ResZip only restores the file named by the current bundle, so archives left by an older game version cannot override new bundled resources.

### 3. Build your project

Open `Project / Live Update Settings` and set these options:

- Set `Mode` to `Zip`.
- Set `Zip filename` to the same name as `liveupdate_reszip.filename`.
- Enable `Save zip in bundle folder`.

Build the game through `Project / Bundle...` or with Bob and `--liveupdate yes`. Defold will put the resource archive into the bundle. You do not need to move it yourself.

> [!IMPORTANT]
> The included Bash script (`example_build_script.sh`) creates one archive name, passes it to Defold and ResZip, and builds the web bundle. Defold puts the archive in the correct folder.

### 4. Summary

- Put the content that will be downloaded later into the collection proxy.
- Exclude this collection proxy so that Defold will put it in the Live Update zip archive with resources.
- For every unique version of the project, set a unique name for the resource file. ResZip uses resources filename to check if the current version of resources is compatible with what the player already has. This is important for updating your game between versions!
- Use simple-to-use ResZip API to download and mount the resource file.

## Tips

The easiest way to use ResZip in your project is to move some of your audio files (i.e. sound components) to a proxied collection and exclude the collection for the release build. To play these sounds, you should make an external script that acts as a sound manager of all your in-game audio and knows when proxied sounds are loaded from the `resources.zip` file.

## Advanced Usage (HTML5 only)

### Preload resources

ResZip can start preloading the `resources.zip` file as soon as game loading is finished. It's highly recommended to enable this option because the engine initialisation takes some time, during which we can already start loading resources:

```ini
[liveupdate_reszip]
preload_file = your_resources_file_name.zip
```

## Credits

This project is licensed under the terms of the CC0 1.0 Universal license. It's developed and supported by [@aglitchman](https://github.com/aglitchman). 

The demo contains third-party music files which require attribution:
```
Ethernight Club by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/7612-ethernight-club
License: https://filmmusic.io/standard-license
```
