var LibraryResZip = {
    $ResZip: {
        //
        _preloads: {},
    },

    dmResZipRequestFileAsync: function (url, context, onprogress, onerror, onload) {
        var callbacks = {
            onprogress: function (loaded, total) {
                {{{ makeDynCall('viii', 'onprogress') }}}(context, loaded, total);
            },
            onerror: function (err) {
                var pError = stringToNewUTF8(err);
                {{{ makeDynCall('vii', 'onerror') }}}(context, pError);
                _free(pError);
            },
            onload: function (response) {
                var ab = new Uint8Array(response);
                var b = _malloc(ab.length);
                HEAPU8.set(ab, b);
                {{{ makeDynCall('viii', 'onload') }}}(context, b, ab.length);
                _free(b);
            },
        };

        if (context === undefined) {
            //
            // Undefined context means that the function is called from the JS.
            //
            // Let's start loading the url and keep the progress in the `_preloads` object.
            //

            var preload = {
                events: {},
                handler: function () {
                    var args = Array.prototype.slice.call(arguments);
                    var name = args.shift();
                    preload.events[name] = args;
                },
            };
            ResZip._preloads[url] = preload;

            FileLoader.load(
                url,
                "arraybuffer",
                function (loaded, total) {
                    preload.handler("onprogress", loaded, total);
                },
                function (err) {
                    preload.handler("onerror", err);
                },
                function (response) {
                    preload.handler("onload", response);
                },
                function () { }
            );
            return;
        }

        // Convert C/C++ char* to a JavaScript string
        url = UTF8ToString(url);

        // Check if data has been already preloaded
        if (ResZip._preloads[url]) {
            //
            // Preloading of this URL in progress or finished
            //
            var preload = ResZip._preloads[url];
            delete ResZip._preloads[url];

            preload.handler = function () {
                var args = Array.prototype.slice.call(arguments);
                var name = args.shift();
                callbacks[name].apply(null, args);
            };

            ["onprogress", "onerror", "onload"].forEach(function (name) {
                var args = preload.events[name];
                if (args !== undefined) {
                    callbacks[name].apply(null, args);
                }
            });
        } else {
            //
            // Normal usage - load something from URL
            //
            FileLoader.load(url, "arraybuffer", callbacks.onprogress, callbacks.onerror, callbacks.onload, function() { });
        }
    },
};

autoAddDeps(LibraryResZip, "$ResZip");
addToLibrary(LibraryResZip);
