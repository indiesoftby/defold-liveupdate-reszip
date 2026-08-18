local APP_NAME = sys.get_config_string("project.title", "reszip")
local MOUNT_NAME = "reszip"
local FILENAME = "resources.zip"

local function finish(self, context, err)
    if context.on_finish then
        context.on_finish(self, err)
    end
    context.on_finish = nil
    context.on_progress = nil
end

local function mount_name_matches(actual_name, expected_name)
    return actual_name == expected_name
        or (type(expected_name) == "string" and actual_name == hash(expected_name))
end

local function basename(uri)
    return uri and uri:match("[^/\\]+$") or nil
end

local function file_exists(path)
    local file = io.open(path, "rb")
    if file then
        file:close()
        return true
    end
    return false
end

local function remove_current_mount(context)
    for _, mount in ipairs(liveupdate.get_mounts()) do
        if mount_name_matches(mount.name, context.mount_name) then
            liveupdate.remove_mount(mount.name)
            return mount.uri and mount.uri:match("^zip:(.+)$") or nil
        end
    end
end

local function delete_replaced_archive(context, old_path, new_path)
    if context.delete_old_file and old_path and old_path ~= new_path then
        local ok, err = os.remove(old_path)
        if not ok then
            print("reszip.lua: unable to delete old resources file `" .. old_path .. "`,", err)
        end
    end
end

local function mount_error(name, uri, result)
    return "Failed to add mount `" .. tostring(name) .. "` to `" .. uri
        .. "` with the result code " .. tostring(result)
end

local function add_mount(context, path, on_success, on_error)
    local old_path = remove_current_mount(context)

    local uri = "zip:" .. path
    local result = liveupdate.add_mount(context.mount_name, uri, context.priority,
        function(self, name, uri, result)
            if result == liveupdate.LIVEUPDATE_OK then
                on_success(self, old_path)
            else
                on_error(self, mount_error(name, uri, result), old_path)
            end
        end)

    if result ~= liveupdate.LIVEUPDATE_OK then
        on_error(nil, mount_error(context.mount_name, uri, result), old_path)
    end
end

local function mount_zip(context, path, replaced_path)
    add_mount(context, path,
        function(self, old_path)
            delete_replaced_archive(context, replaced_path or old_path, path)
            finish(self, context)
        end,
        function(self, err)
            finish(self, context, err)
        end)
end

local function store_and_mount_zip(self, context, data)
    local path = sys.get_save_file(context.app_name, context.filename)
    local temp_path = path .. ".tmp"
    local file, err = io.open(temp_path, "wb")
    if not file then
        finish(self, context, "Unable to open a file for writing (" .. err .. ").")
        return
    end

    local ok, write_err = file:write(data)
    file:close()
    if not ok then
        os.remove(temp_path)
        finish(self, context, "Unable to write data into the resources file (" .. write_err .. ").")
        return
    end

    add_mount(context, temp_path,
        function(self, old_path)
            liveupdate.remove_mount(context.mount_name)

            local renamed, rename_err = os.rename(temp_path, path)
            if not renamed and file_exists(path) then
                local removed, remove_err = os.remove(path)
                if not removed then
                    os.remove(temp_path)
                    finish(self, context, "Unable to replace the resources file (" .. remove_err .. ").")
                    return
                end
                renamed, rename_err = os.rename(temp_path, path)
            end
            if not renamed then
                os.remove(temp_path)
                finish(self, context, "Unable to save the resources file (" .. rename_err .. ").")
                return
            end

            mount_zip(context, path, context.replaced_path or old_path)
        end,
        function(self, mount_err)
            os.remove(temp_path)
            finish(self, context, mount_err)
        end)
end

local start_download

local function try_mount_saved_zip(context)
    local path = sys.get_save_file(context.app_name, context.filename)
    if file_exists(path) then
        add_mount(context, path,
            function(self, old_path)
                delete_replaced_archive(context, old_path, path)
                finish(self, context)
            end,
            function(self, _, old_path)
                context.replaced_path = old_path
                os.remove(path)
                start_download(context)
            end)
        return true
    end
    return false
end

start_download = function(context)
    if liveupdate_reszip_ext.request_file then
        liveupdate_reszip_ext.request_file(
            context.url,
            function(self, loaded, total)
                if context.on_progress and total > 0 then
                    context.on_progress(self, loaded, total)
                end
            end,
            function(self, err)
                finish(self, context, err)
            end,
            function(self, data)
                store_and_mount_zip(self, context, data)
            end)
        return
    end

    http.request(context.url, "GET", function(self, _, response)
        if response.bytes_total ~= nil then
            if context.on_progress and response.bytes_total > 0 then
                context.on_progress(self, response.bytes_received, response.bytes_total)
            end
            return
        end

        if (response.status == 200 or response.status == 304) and response.error == nil then
            store_and_mount_zip(self, context, response.response)
        else
            local err = response.error or ("HTTP status " .. tostring(response.status))
            finish(self, context, "Error happened while downloading: " .. err)
        end
    end, nil, nil, { report_progress = true })
end

local M = {}

--- Checks the mounted resources version by comparing the resource file name.
-- Returns nil if it can't find the requested mount.
-- @param string filename resource file name
-- @param string mount_name optional mount name
-- @return boolean|nil whether the mounted resource file name matches
function M.version_match(filename, mount_name)
    mount_name = mount_name or MOUNT_NAME

    for _, mount in ipairs(liveupdate.get_mounts()) do
        if mount_name_matches(mount.name, mount_name) then
            return basename(mount.uri) == filename
        end
    end

    return nil
end

--- Loads and mounts a zip file from a saved file, an HTML5 preload, or a URL.
-- @param string url URL or path
-- @param table options load options
-- @field options function on_finish function(self, err)
-- @field options function|nil on_progress function(self, loaded, total)
-- @field options string|nil app_name save-file application name
-- @field options string|nil mount_name mount name
-- @field options string|nil filename saved resource file name
-- @field options boolean|nil delete_old_file delete the replaced active archive after success
-- @field options number|nil priority mount priority
local function load_and_mount_zip(url, options, restore_saved_file)
    local context = {
        url = url,
        app_name = options.app_name or APP_NAME,
        mount_name = options.mount_name or MOUNT_NAME,
        filename = options.filename or FILENAME,
        delete_old_file = options.delete_old_file or false,
        priority = options.priority or 20,
        on_finish = options.on_finish,
        on_progress = options.on_progress
    }

    if restore_saved_file and M.version_match(context.filename, context.mount_name) then
        finish(nil, context)
        return
    end

    if not restore_saved_file or not try_mount_saved_zip(context) then
        start_download(context)
    end
end

function M.load_and_mount_zip(url, options)
    load_and_mount_zip(url, options, true)
end

--- DEPRECATED: use load_and_mount_zip().
function M.request_and_load_zip(url, missing_resources, callback, progress_callback, store_callback)
    print("reszip.lua: `request_and_load_zip` is deprecated; use `reszip.load_and_mount_zip(url, options)`.")
    load_and_mount_zip(url, {
        on_finish = callback,
        on_progress = progress_callback
    }, false)
end

--- DEPRECATED: downloaded data is released automatically.
function M.clear_cache()
    print("reszip.lua: `clear_cache` is deprecated and no longer required.")
end

return M
