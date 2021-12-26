#!/bin/bash

set -e

PLATFORM=js-web

rm -rf build
mkdir -p build/public
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --bundle-output build/bundle/${PLATFORM} --build-report-html build/public/build_report_latest.html --platform ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv build/liveupdate_output/*.zip build/bundle/${PLATFORM}/liveupdate_reszip_demo/resources.zip
(cd build/bundle/${PLATFORM}/liveupdate_reszip_demo/ && http-server -c-)
