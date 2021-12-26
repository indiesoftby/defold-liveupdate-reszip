#define LIB_NAME "liveupdate_reszip_ext"
#define MODULE_NAME "liveupdate_reszip_ext"

#include "miniz.h"

#include <dmsdk/sdk.h>
#include <stdint.h>
#include <string.h>

namespace dmLiveUpdate
{
    void AsyncUpdate();
}

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

static int ListResources(lua_State *L) {
    size_t buf_len = 0;
    const char *buf = luaL_checklstring(L, 1, &buf_len);

    mz_zip_archive zip_archive;
    memset(&zip_archive, 0, sizeof(zip_archive));

    if (!mz_zip_reader_init_mem(&zip_archive, buf, buf_len, 0)) {
        dmLogError("mz_zip_reader_init_mem() failed!");

        lua_pushnil(L);
        return 1;
    }

    uint32_t file_count = mz_zip_reader_get_num_files(&zip_archive);
    lua_createtable(L, file_count, 0);

    if (file_count > 0) {
        uint32_t fi = 1;
        for (uint32_t i = 0; i < file_count; i++) {
            mz_zip_archive_file_stat file_stat;
            if (!mz_zip_reader_file_stat(&zip_archive, i, &file_stat))
                continue;
            if (mz_zip_reader_is_file_a_directory(&zip_archive, i))
                continue; // skip directories
            if (strlen(file_stat.m_filename) != 40)
                continue; // not a resource

            lua_pushnumber(L, fi);
            lua_pushstring(L, file_stat.m_filename);
            lua_settable(L, -3);

            fi++;
        }
    }

    mz_zip_reader_end(&zip_archive);

    return 1;
}

#if defined(DM_PLATFORM_HTML5)

namespace ResZip {
struct RequestFileContext {
    dmScript::LuaCallbackInfo *m_CallbackProgress;
    dmScript::LuaCallbackInfo *m_CallbackError;
    dmScript::LuaCallbackInfo *m_CallbackLoad;
};

typedef void (*OnProgress)(void *context, const int loaded, const int total);
typedef void (*OnError)(void *context, const char *error);
typedef void (*OnLoad)(void *context, const uint8_t *content, const int content_size);
} // namespace ResZip

extern "C" void dmResZipRequestFileAsync(const char *url, void *context, ResZip::OnProgress onprogress,
                                         ResZip::OnError onerror, ResZip::OnLoad onload);

static void OnHttpProgress(void *arg_context, const int loaded, const int total) {
    ResZip::RequestFileContext *context = (ResZip::RequestFileContext *)arg_context;

    if (!dmScript::IsCallbackValid(context->m_CallbackProgress)) {
        return;
    }

    lua_State *L = dmScript::GetCallbackLuaContext(context->m_CallbackProgress);

    if (!dmScript::SetupCallback(context->m_CallbackProgress)) {
        dmScript::DestroyCallback(context->m_CallbackProgress);
        context->m_CallbackProgress = 0x0;
        return;
    }

    lua_pushinteger(L, loaded);
    lua_pushinteger(L, total);
    dmScript::PCall(L, 3, 0);

    dmScript::TeardownCallback(context->m_CallbackProgress);
}

static void OnHttpError(void *arg_context, const char *error) {
    ResZip::RequestFileContext *context = (ResZip::RequestFileContext *)arg_context;

    if (dmScript::IsCallbackValid(context->m_CallbackError)) {
        lua_State *L = dmScript::GetCallbackLuaContext(context->m_CallbackError);

        if (dmScript::SetupCallback(context->m_CallbackError)) {
            lua_pushstring(L, error);
            dmScript::PCall(L, 2, 0);

            dmScript::TeardownCallback(context->m_CallbackError);
        }
    }

    if (context->m_CallbackProgress)
        dmScript::DestroyCallback(context->m_CallbackProgress);
    if (context->m_CallbackError)
        dmScript::DestroyCallback(context->m_CallbackError);
    if (context->m_CallbackLoad)
        dmScript::DestroyCallback(context->m_CallbackLoad);

    free(context);
}

static void OnHttpLoad(void *arg_context, const uint8_t *content, const int content_size) {
    ResZip::RequestFileContext *context = (ResZip::RequestFileContext *)arg_context;

    if (dmScript::IsCallbackValid(context->m_CallbackLoad)) {
        lua_State *L = dmScript::GetCallbackLuaContext(context->m_CallbackLoad);

        if (dmScript::SetupCallback(context->m_CallbackLoad)) {
            lua_pushlstring(L, (char *)content, content_size);
            dmScript::PCall(L, 2, 0);

            dmScript::TeardownCallback(context->m_CallbackLoad);
        }
    }

    if (context->m_CallbackProgress)
        dmScript::DestroyCallback(context->m_CallbackProgress);
    if (context->m_CallbackError)
        dmScript::DestroyCallback(context->m_CallbackError);
    if (context->m_CallbackLoad)
        dmScript::DestroyCallback(context->m_CallbackLoad);

    free(context);
}

static int RequestFile(lua_State *L) {
    int top = lua_gettop(L);

    size_t buf_len = 0;
    const char *buf = luaL_checklstring(L, 1, &buf_len);

    ResZip::RequestFileContext *context = (ResZip::RequestFileContext *)calloc(1, sizeof(ResZip::RequestFileContext));

    if (top > 1 && lua_isfunction(L, 2))
        context->m_CallbackProgress = dmScript::CreateCallback(L, 2);
    if (top > 2 && lua_isfunction(L, 3))
        context->m_CallbackError = dmScript::CreateCallback(L, 3);
    if (top > 3 && lua_isfunction(L, 4))
        context->m_CallbackLoad = dmScript::CreateCallback(L, 4);

    dmResZipRequestFileAsync(buf, context, OnHttpProgress, OnHttpError, OnHttpLoad);

    return 0;
}

#endif

static int UpdateJobQueue(lua_State *L)
{
    dmLiveUpdate::AsyncUpdate();
    return 0;
}

// Functions exposed to Lua
static const luaL_reg Module_methods[] = {{"extract_file", ExtractFile},
                                          {"validate_zip", ValidateZip},
                                          {"list_resources", ListResources},
#if defined(DM_PLATFORM_HTML5)
                                          {"request_file", RequestFile},
#endif
                                          {"update_job_queue", UpdateJobQueue},
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
