local M = {}

local function call_callback_and_cleanup(self, err)
    M._missing_resources = nil
    M._callback(self, err)
    M._callback = nil
    M._progress_callback = nil
end

local function store_missing_resource_from_zip(self, hexdigest, status)
    if status then
        if next(M._missing_resources) ~= nil then
            -- Loading next missing resource from the ZIP archive
            local res_hash = table.remove(M._missing_resources)

            local data = liveupdate_reszip_ext.extract_file(M._resources_zip, res_hash)
            if data then
                resource.store_resource(resource.get_current_manifest(), data, res_hash, store_missing_resource_from_zip)
            else
                call_callback_and_cleanup(self, "Can't extract file " .. res_hash)
            end
        else
            -- SUCCESS!
            call_callback_and_cleanup(self, nil)
        end
    else
        call_callback_and_cleanup(self, "Error happened while storing resource: " .. hexdigest)
    end
end

local function request_file_progress_handler(self, loaded, total)
    if M._progress_callback and total > 0 then
        M._progress_callback(self, loaded, total)
    end
end

local function request_file_error_handler(self, err)
    call_callback_and_cleanup(self, err)
end

local function request_file_load_handler(self, response)
    M._resources_zip = response
    if liveupdate_reszip_ext.validate_zip(M._resources_zip) then
        if M._missing_resources == nil then
            M._missing_resources = liveupdate_reszip_ext.list_resources(M._resources_zip)
        end

        store_missing_resource_from_zip(self, nil, true)
    else
        M._resources_zip = nil
        call_callback_and_cleanup(self, "Invalid format of the ZIP file")
    end
end

local function http_request_handler(self, id, response)
    if (response.status == 200 or response.status == 304) and response.error == nil then
        request_file_load_handler(self, response.response)
    else
        call_callback_and_cleanup(self, "Error happened while downloading: " .. response.status)
    end
end

--
-- PUBLIC
--

function M.request_and_load_zip(filename, missing_resources, callback, progress_callback)
    M._callback = callback
    M._progress_callback = progress_callback
    M._missing_resources = missing_resources

    if not M._resources_zip then
        if liveupdate_reszip_ext.request_file then
            -- (HTML5 only) Load .zip file using the custom file loader
            liveupdate_reszip_ext.request_file(
                filename,
                request_file_progress_handler,
                request_file_error_handler,
                request_file_load_handler)
        else
            -- Load .zip file via Defold's `http.request`
            http.request(filename, "GET", http_request_handler)
        end
    else
        store_missing_resource_from_zip(self, nil, true)
    end
end

function M.clear_cache()
    M._resources_zip = nil
end

return M