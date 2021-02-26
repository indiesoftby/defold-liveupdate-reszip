local M = {}

local function call_callback_and_cleanup(self, err)
    M._resources_zip = nil
    M._missing_resources = nil
    M._callback(self, err)
    M._callback = nil
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

local function http_request_handler(self, id, response)
    if (response.status == 200 or response.status == 304) and response.error == nil then
        -- print("DEBUG: Resources ZIP loaded, validating...")
        M._resources_zip = response.response
        if liveupdate_reszip_ext.validate_zip(M._resources_zip) then
            store_missing_resource_from_zip(self, nil, true)
        else
            call_callback_and_cleanup(self, "Invalid format of the ZIP file")
        end
    else
        call_callback_and_cleanup(self, "Error happened while downloading:" .. response.status)
    end
end

function M.request_and_load_zip(filename, missing_resources, callback)
    M._callback = callback
    M._missing_resources = missing_resources

    http.request(filename, "GET", http_request_handler)
end

return M