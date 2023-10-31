#define LIB_NAME "liveupdate_reszip_ext"
#define MODULE_NAME "liveupdate_reszip_ext"

#include <dmsdk/sdk.h>

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

// Functions exposed to Lua
static const luaL_reg Module_methods[] = {
#if defined(DM_PLATFORM_HTML5)
                                          {"request_file", RequestFile},
#endif
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
