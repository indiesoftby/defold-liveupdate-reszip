#!/bin/bash

# Download bob.jar like that:
# wget "https://github.com/defold/defold/releases/download/1.6.2/bob.jar" -O bob.jar

# Plus, the script uses https://www.npmjs.com/package/http-server to serve local files.

set -e

PLATFORM=wasm-web

mkdir -p public

# BUNDLE 1
BUNDLE_DIR=bundle-1
RESZIP_INI="reszip.ini"
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"
sed -i 's/"enabled", true/"enabled", false/' example/level2/set_alt_text.script

rm -rf build
mkdir -p build/bundle
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output build/bundle/${PLATFORM} --build-report-html build/bundle/build_report_latest.html --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv build/liveupdate_output/*.zip "build/bundle/${PLATFORM}/liveupdate_reszip_demo/${RESOURCES_ZIP}"
rm -f "${RESZIP_INI}"
mv "build/bundle/${PLATFORM}/liveupdate_reszip_demo" "public/${BUNDLE_DIR}"

# BUNDLE 2
BUNDLE_DIR=bundle-2
RESZIP_INI="reszip.ini"
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"
sed -i 's/"enabled", false/"enabled", true/' example/level2/set_alt_text.script

rm -rf build
mkdir -p build/bundle
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output build/bundle/${PLATFORM} --build-report-html build/bundle/build_report_latest.html --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv build/liveupdate_output/*.zip "build/bundle/${PLATFORM}/liveupdate_reszip_demo/${RESOURCES_ZIP}"
rm -f "${RESZIP_INI}"
mv "build/bundle/${PLATFORM}/liveupdate_reszip_demo" "public/${BUNDLE_DIR}"

# DONE
# http-server -c-
