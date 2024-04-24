var LibraryResZip = {
    $ResZip: {
        //
        _preloads: {},
    },

    // FIXME: replace with `http.request`
    // file downloader
    // wraps XMLHttpRequest and adds retry support and progress updates when the
    // content is gzipped (gzipped content doesn't report a computable content length
    // on Google Chrome)
    $ResZipFileLoader: {
        options: {
            retryCount: 5,
            retryInterval: 1000,
        },
        // do xhr request with retries
        request: function(url, method, responseType, currentAttempt) {
            if (typeof method === 'undefined') throw "No method specified";
            if (typeof method === 'responseType') throw "No responseType specified";
            if (typeof currentAttempt === 'undefined') currentAttempt = 0;
            var obj = {
                send: function() {
                    var onprogress = this.onprogress;
                    var onload = this.onload;
                    var onerror = this.onerror;

                    var xhr = new XMLHttpRequest();
                    xhr.open(method, url, true);
                    xhr.responseType = responseType;
                    xhr.onprogress = function(e) {
                        if (onprogress) onprogress(xhr, e);
                    };
                    xhr.onerror = function(e) {
                        if (currentAttempt == ResZipFileLoader.options.retryCount) {
                            if (onerror) onerror(xhr, e);
                            return;
                        }
                        currentAttempt = currentAttempt + 1;
                        setTimeout(obj.send.bind(obj), ResZipFileLoader.options.retryInterval);
                    };
                    xhr.onload = function(e) {
                        if (onload) onload(xhr, e);
                    };
                    xhr.send(null);
                }
            };
            return obj;
        },
        // Do HTTP HEAD request to get size of resource
        // callback will receive size or undefined in case of an error
        size: function(url, callback) {
            var request = ResZipFileLoader.request(url, "HEAD", "text");
            request.onerror = function(xhr, e) {
                callback(undefined);
            };
            request.onload = function(xhr, e) {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        var total = xhr.getResponseHeader('content-length');
                        callback(total);
                    } else {
                        callback(undefined);
                    }
                }
            };
            request.send();
        },
        // Do HTTP GET request
        // onprogress(loaded, total)
        // onerror(error)
        // onload(response)
        load: function(url, responseType, estimatedSize, onprogress, onerror, onload) {
            var request = ResZipFileLoader.request(url, "GET", responseType);
            request.onprogress = function(xhr, e) {
                if (e.lengthComputable) {
                    onprogress(e.loaded, e.total);
                    return;
                }
                var contentLength = xhr.getResponseHeader('content-length');
                var size = contentLength != undefined ? contentLength : estimatedSize;
                if (size) {
                    onprogress(e.loaded, size);
                } else {
                    onprogress(e.loaded, e.loaded);
                }
            };
            request.onerror = function(xhr, e) {
                onerror("Error loading '" + url + "' (" + e + ")");
            };
            request.onload = function(xhr, e) {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        var res = xhr.response;
                        if (responseType == "json" && typeof res === "string") {
                            onload(JSON.parse(res));
                        } else {
                            onload(res);
                        }
                    } else {
                        onerror("Error loading '" + url + "' (" + e + ")");
                    }
                }
            };
            request.send();
        }
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

            ResZipFileLoader.load(
                url,
                "arraybuffer",
                0,
                function (loaded, total) {
                    preload.handler("onprogress", loaded, total);
                },
                function (err) {
                    preload.handler("onerror", err);
                },
                function (response) {
                    preload.handler("onload", response);
                }
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
            ResZipFileLoader.load(url, "arraybuffer", 0, callbacks.onprogress, callbacks.onerror, callbacks.onload);
        }
    },
};

autoAddDeps(LibraryResZip, "$ResZip");
autoAddDeps(LibraryResZip, "$ResZipFileLoader");
addToLibrary(LibraryResZip);
