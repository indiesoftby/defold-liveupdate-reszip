local M = {
    RESOURCES_PER_BATCH = 1,
    BATCH_MAX_TIME = 0, -- Seconds. Set 0 or less to disable.
}

local function call_callback_and_cleanup(self, err)
    M._missing_resources = nil
    if M._callback then
        M._callback(self, err)
    end
    M._callback = nil
    M._progress_callback = nil
    M._store_callback = nil
end

local function store_missing_resource_from_zip(self, hexdigest, status)
    if status then
        if M._missing_resources ~= nil and next(M._missing_resources) ~= nil then
            if M._store_callback and M._resources_total > 0 then
                M._store_callback(self, M._resources_stored, M._resources_total)
            end

            -- Loading next missing resource from the ZIP archive
            local res_hash = table.remove(M._missing_resources)
            M._resources_stored = M._resources_stored + 1

            local data = liveupdate_reszip_ext.extract_file(M._resources_zip, res_hash)
            if data then
                resource.store_resource(resource.get_current_manifest(), data, res_hash, store_missing_resource_from_zip)
                if #M._missing_resources > 0 then
                    local time = socket.gettime()
                    local push_queue = true
                    if M.BATCH_MAX_TIME > 0 and time - M._resources_batch_time > M.BATCH_MAX_TIME then
                        push_queue = false
                    end

                    M._resources_pushed = M._resources_pushed + 1
                    if M._resources_pushed >= M.RESOURCES_PER_BATCH then
                        push_queue = false
                    end

                    if html5 and push_queue then
                        liveupdate_reszip_ext.update_job_queue()
                    else
                        M._resources_pushed = 0
                        M._resources_batch_time = time
                    end
                end
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

        M._resources_batch_time = socket.gettime()
        M._resources_pushed = 0
        M._resources_stored = 0
        M._resources_total = #M._missing_resources

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

function M.request_and_load_zip(filename, missing_resources, callback, progress_callback, store_callback)
    M._callback = callback
    M._progress_callback = progress_callback
    M._store_callback = store_callback
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
        -- "timer.delay" is necessary to get "self" and use it for callbacks (if any)
        timer.delay(0, false, function (self)
            request_file_load_handler(self, M._resources_zip)
        end)
    end
end

function M.clear_cache()
    M._resources_zip = nil
end

return M