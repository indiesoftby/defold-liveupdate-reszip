var LibraryResZip = {
    $ResZip: {},

    dmResZipRequestFileAsync: function (url, context, onprogress, onerror, onload) {
        FileLoader.load(
            UTF8ToString(url),
            "arraybuffer",
            0,
            function (loaded, total) {
                {{{ makeDynCall('viii', 'onprogress') }}}(context, loaded, total);
            },
            function (err) {
                var pError = allocate(intArrayFromString(err), "i8", ALLOC_NORMAL);
                {{{ makeDynCall('vii', 'onerror') }}}(context, pError);
                _free(pError);
            },
            function (response) {
                var ab = new Uint8Array(response);
                var b = allocate(ab, "i8", ALLOC_NORMAL);
                {{{ makeDynCall('viii', 'onload') }}}(context, b, ab.length);
                _free(b);
            }
        );
    },
};

autoAddDeps(LibraryResZip, "$ResZip");
mergeInto(LibraryManager.library, LibraryResZip);
