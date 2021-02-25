mergeInto(LibraryManager.library, {
    HashSHA1: function (str) {
        var pStr = allocate(intArrayFromString(str), "i8", ALLOC_NORMAL);
        var pHash = _ResZip_HashSHA1(pStr);
        _free(pStr);
        return UTF8ToString(pHash);
    },
});
