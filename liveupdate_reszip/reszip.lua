
-- Default values:
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

local function store_zip_mount(self, context, zip_data)
    -- Remove any previous mounts with the same name
    local mounts = liveupdate.get_mounts()
    for i, mount in ipairs(mounts) do
        if mount.name == context.mount_name then
            liveupdate.remove_mount(mount.name)

            if context.delete_old_file then
                local basename = mount.uri:match("^.+/(.+)$")
                local path = sys.get_save_file(context.app_name, basename)
                local ok, err = os.remove(path)
                if not ok then
                    print("reszip.lua: unable to delete old resources file `" .. path .. "`,", err)
                end
            end
        end
    end

    local disk_path = sys.get_save_file(context.app_name, context.filename)
    local file, err = io.open(disk_path, "wb")
    if not file then
        finish(self, context, "Unable to open a file for writing (" .. err .. ").")
        return
    end
    local ok, err = file:write(zip_data)
    if not ok then
        finish(self, context, "Unable to write data into the resources file (" .. err .. ").")
        return
    end
    file:close()

    zip_data = nil

    local uri = "zip:" .. disk_path
    local priority = context.priority -- It should be higher than old live update archive priority 10
    liveupdate.add_mount(context.mount_name, uri, priority, function(self, path, uri, result)
        if result == 0 then -- dmLiveUpdate::RESULT_OK = 0
            finish(self, context)
        else
            finish(self, context, "Failed to add mount `" .. path .. "` to `" .. uri .. "` with the result code " .. result)
        end
    end)
end

local function request_file_progress_handler(self, context, loaded, total)
    if context.on_progress and total > 0 then
        context.on_progress(self, loaded, total)
    end
end

local function request_file_error_handler(self, context, err)
    finish(self, context, err)
end

local function http_request_handler(self, context, id, response)
    if (response.status == 200 or response.status == 304) and response.error == nil then
        store_zip_mount(self, context, response.response)
    else
        finish(self, context, "Error happened while downloading: " .. response.status)
    end
end

--
-- Public
--

local M = {}

--- The function checks the "version" of resources by comparing the resource file names.
-- Returns nil if it can't find `reszip` mount.
-- @param filename (string)
-- @param mount_name (string) - Optional
-- @return (boolean)
function M.version_match(filename, mount_name)
    mount_name = mount_name or MOUNT_NAME

    local mounts = liveupdate.get_mounts()
    for i, mount in ipairs(mounts) do
        if mount.name == mount_name then
            local basename = mount.uri:match("^.+/(.+)$")
            return basename == filename
        end
    end

    return nil
end

--- The function makes HTTP request to load .zip file from the `url`.
-- Then it stores the file internally, and mounts to Live Update.
-- When the resources mounting process is done (or failed), it calls `on_finish`.
-- @param url (string) - URL or path
-- @param options (table) - { 
--          on_finish = function(self, err),
--          -- Optional:
--          on_progress = function(self, loaded, total),
--          app_name = string,
--          mount_name = string,
--          filename = string,
--          delete_old_file = boolean,
--          priority = number,
--        }
function M.load_and_mount_zip(url, options)
    local context = {
        app_name = options.app_name or APP_NAME,
        mount_name = options.mount_name or MOUNT_NAME,
        filename = options.filename or FILENAME,
        delete_old_file = type(options.delete_old_file) ~= "nil" and options.delete_old_file or false,
        priority = options.priority or 20,
        on_finish = options.on_finish,
        on_progress = options.on_progress
    }

    if liveupdate_reszip_ext.request_file then
        -- (HTML5 only) Load .zip file using the custom file loader
        liveupdate_reszip_ext.request_file(
            url,
            function(self, loaded, total) request_file_progress_handler(self, context, loaded, total) end,
            function(self, err) request_file_error_handler(self, context, err) end,
            function(self, response_data) store_zip_mount(self, context, response_data) end)
    else
        -- Load .zip file via Defold's `http.request`
        http.request(url, "GET", function(self, id, response) http_request_handler(self, context, id, response) end)
    end
end

--- DEPRECATED
--- The function makes HTTP request to load .zip file from the `url`.
-- Then it stores the file internally, and mounts to Live Update.
-- When the resources mounting process is done, it calls `done_callback`.
-- @param url (string) - URL or path
-- @param missing_resources (array) - DOES NOTHING
-- @param callback (function)
-- @param progress_callback (function)
-- @param store_callback (function) - DOES NOTHING
function M.request_and_load_zip(url, missing_resources, callback, progress_callback, store_callback)
    print("reszip.lua: `request_and_load_zip` function is deprecated. You can still use it if you set the game.project option `wipe_on_start = 1`, but it's better to call `reszip.load_and_mount_zip(url, opts)`.")
    M.load_and_mount_zip(url, {
        on_finish = callback,
        on_progress = progress_callback
    })
end

--- DEPRECATED
function M.clear_cache()
    print("reszip.lua: `clear_cache` function is deprecated. Do not call it anymore.")
end

return M
