-- zzlib - zlib decompression in Lua - Implementation-independent code
-- Copyright (c) 2016-2020 Francois Galea <fgalea at free.fr>
-- This program is free software. It comes without any warranty, to
-- the extent permitted by applicable law. You can redistribute it
-- and/or modify it under the terms of the Do What The Fuck You Want
-- To Public License, Version 2, as published by Sam Hocevar. See
-- the COPYING file or http://www.wtfpl.net/ for more details.
local zzlib = {}

local crc32_table

local function crc32(s, crc)
    if not crc32_table then
        crc32_table = {}
        for i = 0, 255 do
            local r = i
            for j = 1, 8 do
                r = bit.bxor(bit.rshift(r, 1), bit.band(0xedb88320, bit.bnot(bit.band(r, 1) - 1)))
            end
            crc32_table[i] = r
        end
    end
    crc = bit.bnot(crc or 0)
    for i = 1, #s do
        local c = s:byte(i)
        crc = bit.bxor(crc32_table[bit.bxor(c, bit.band(crc, 0xff))], bit.rshift(crc, 8))
    end
    crc = bit.bnot(crc)
    if crc < 0 then
        -- in Lua < 5.2, sign extension was performed
        crc = crc + 4294967296
    end
    return crc
end

local function arraytostr(array)
    local tmp = {}
    local size = #array
    local pos = 1
    local imax = 1
    while size > 0 do
        local bsize = size >= 2048 and 2048 or size
        local s = string.char(unpack(array, pos, pos + bsize - 1))
        pos = pos + bsize
        size = size - bsize
        local i = 1
        while tmp[i] do
            s = tmp[i] .. s
            tmp[i] = nil
            i = i + 1
        end
        if i > imax then
            imax = i
        end
        tmp[i] = s
    end
    local str = ""
    for i = 1, imax do
        if tmp[i] then
            str = tmp[i] .. str
        end
    end
    return str
end

local function int2le(str, pos)
    local a, b = str:byte(pos, pos + 1)
    return b * 256 + a
end

local function int4le(str, pos)
    local a, b, c, d = str:byte(pos, pos + 3)
    return ((d * 256 + c) * 256 + b) * 256 + a
end

function zzlib.unzip(buf, filename)
    local p = #buf - 21
    local quit = false
    if int4le(buf, p) ~= 0x06054b50 then
        -- not sure there is a reliable way to locate the end of central directory record
        -- if it has a variable sized comment field
        error(".ZIP file comments not supported")
    end
    local cdoffset = int4le(buf, p + 16)
    local nfiles = int2le(buf, p + 10)
    p = cdoffset + 1
    for i = 1, nfiles do
        if int4le(buf, p) ~= 0x02014b50 then
            error("invalid central directory header signature")
        end
        local namelen = int2le(buf, p + 28)
        local name = buf:sub(p + 46, p + 45 + namelen)
        if name == filename then
            local flag = int2le(buf, p + 8)
            local method = int2le(buf, p + 10)
            local crc = int4le(buf, p + 16)
            local headoffset = int4le(buf, p + 42)
            p = 1 + headoffset
            if int4le(buf, p) ~= 0x04034b50 then
                error("invalid local header signature")
            end
            local csize = int4le(buf, p + 18)
            local extlen = int2le(buf, p + 28)
            p = p + 30 + namelen + extlen
            if method == 0 then
                -- no compression
                print("no compression")
                result = buf:sub(p, p + csize - 1)
            else
                -- DEFLATE compression
                print("DEFLATE")
                -- pprint(string.byte(crcbuf, 0, -1)) -- '\120\94' .. buf:sub(p, p + csize - 1), 0, -1))
                result = zlib.inflate('\120\94' .. buf:sub(p, p + csize - 1) .. '\167\228\29\145') -- + adler32????
            end
            -- DISABLED to speed up the process of decompression
            -- if crc ~= crc32(result) then
            --     error("checksum verification failed")
            -- end
            return result
        end
        p = p + 46 + namelen + int2le(buf, p + 30) + int2le(buf, p + 32)
    end
    error("file '" .. filename .. "' not found in ZIP archive")
end

return zzlib
