#!/bin/bash

# Download bob.jar as described at https://defold.com/manuals/bob/.

# Plus, the script uses https://www.npmjs.com/package/http-server to serve local files.

set -e

PLATFORM=x86_64-win32
RESZIP_INI="reszip.ini"
LIVEUPDATE_INI="liveupdate.generated.settings"
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate]\nsettings = /${LIVEUPDATE_INI}\n\n[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"
echo -e "[liveupdate]\nmode = Zip\nzip-filepath = build/liveupdate_output\nzip-filename = ${RESOURCES_ZIP}\nsave-zip-in-bundle-folder = 1\npublickey = liveupdate_public.der\nprivatekey = liveupdate_private.der\n\n" > "${LIVEUPDATE_INI}"
trap 'rm -f "${RESZIP_INI}" "${LIVEUPDATE_INI}"' EXIT

rm -rf build
rm -rf dist/windows
mkdir -p dist/windows
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output dist/windows/${PLATFORM} --build-report-html dist/windows/build_report_latest.html --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
http-server -c-
