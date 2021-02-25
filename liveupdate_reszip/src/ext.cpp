#define LIB_NAME "liveupdate_reszip_ext"
#define MODULE_NAME "liveupdate_reszip_ext"

#include "miniz.h"

#include <dmsdk/sdk.h>
#include <string.h>

static int ExtractFile(lua_State *L) {
    size_t buf_len = 0;
    const char *buf = luaL_checklstring(L, 1, &buf_len);
    const char *archive_filename = luaL_checkstring(L, 2);

    mz_zip_archive zip_archive;
    memset(&zip_archive, 0, sizeof(zip_archive));

    if (!mz_zip_reader_init_mem(&zip_archive, buf, buf_len, 0)) {
        dmLogError("mz_zip_reader_init_mem() failed!");

        lua_pushnil(L);
        return 1;
    }

    size_t uncomp_size;
    void *p = mz_zip_reader_extract_file_to_heap(&zip_archive, archive_filename, &uncomp_size, 0);
    if (!p) {
        dmLogError("mz_zip_reader_extract_file_to_heap() failed!");

        mz_zip_reader_end(&zip_archive);
        lua_pushnil(L);
        return 1;
    }

    lua_pushlstring(L, (char *)p, uncomp_size);

    mz_free(p);
    mz_zip_reader_end(&zip_archive);

    return 1;
}

static int ValidateZip(lua_State *L) {
    size_t buf_len = 0;
    const char *buf = luaL_checklstring(L, 1, &buf_len);

    mz_zip_archive zip_archive;
    memset(&zip_archive, 0, sizeof(zip_archive));

    if (!mz_zip_reader_init_mem(&zip_archive, buf, buf_len, 0)) {
        dmLogError("mz_zip_reader_init_mem() failed!");

        lua_pushboolean(L, 0);
        return 1;
    }

    mz_zip_reader_end(&zip_archive);

    lua_pushboolean(L, 1);
    return 1;
}

// Functions exposed to Lua
static const luaL_reg Module_methods[] = {{"extract_file", ExtractFile},
                                          {"validate_zip", ValidateZip},
                                          /* Sentinel: */
                                          {NULL, NULL}};

static void LuaInit(lua_State *L) {
    int top = lua_gettop(L);

    // Register lua names
    luaL_register(L, MODULE_NAME, Module_methods);

    lua_pop(L, 1);
    assert(top == lua_gettop(L));
}

static dmExtension::Result InitializeExt(dmExtension::Params *params) {
    LuaInit(params->m_L);
    return dmExtension::RESULT_OK;
}

static dmExtension::Result FinalizeExt(dmExtension::Params *params) { return dmExtension::RESULT_OK; }

DM_DECLARE_EXTENSION(liveupdate_reszip_ext, LIB_NAME, 0, 0, InitializeExt, 0, 0, FinalizeExt)
