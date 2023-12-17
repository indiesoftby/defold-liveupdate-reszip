#!/bin/bash

# Download bob.jar like that:
# wget "https://github.com/defold/defold/releases/download/1.6.2/bob.jar" -O bob.jar

# Plus, the script uses https://www.npmjs.com/package/http-server to serve local files.

set -e

PLATFORM=x86_64-win32
RESOURCES_ZIP="resources_$(date +%s).zip"

RESZIP_INI="reszip.ini"
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"

rm -rf build
mkdir -p build/public
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output build/public/${PLATFORM} --build-report-html build/public/build_report_latest.html --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv build/liveupdate_output/*.zip "build/public/${PLATFORM}/liveupdate_reszip_demo/${RESOURCES_ZIP}"
rm -f "${RESZIP_INI}"
http-server -c-
