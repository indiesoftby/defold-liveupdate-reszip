#!/bin/bash

# Download bob.jar like that:
# wget "https://github.com/defold/defold/releases/download/1.6.1/bob.jar" -O bob.jar

# Plus, the script uses https://www.npmjs.com/package/http-server to serve local files.

set -e

PLATFORM=wasm-web

rm -rf build
mkdir -p build/public
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --bundle-output build/bundle/${PLATFORM} --build-report-html build/public/build_report_latest.html --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv build/liveupdate_output/*.zip build/bundle/${PLATFORM}/liveupdate_reszip_demo/resources.zip
# (cd build/bundle/${PLATFORM}/liveupdate_reszip_demo/ && http-server -c-)
http-server -c-
