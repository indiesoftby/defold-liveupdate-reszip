#!/bin/bash

# Download bob.jar as described at https://defold.com/manuals/bob/.

# Plus, the script uses https://www.npmjs.com/package/http-server to serve local files.

set -e

PLATFORM=wasm-web
LIVEUPDATE_INI="liveupdate.generated.settings"
RESZIP_INI="reszip.ini"
cleanup() {
    rm -f "${RESZIP_INI}" "${LIVEUPDATE_INI}"
    sed -i 's/"enabled", true/"enabled", false/' example/level2/set_alt_text.script
}
trap cleanup EXIT

mkdir -p public

# BUNDLE 1
BUNDLE_DIR=bundle-1
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate]\nsettings = /${LIVEUPDATE_INI}\n\n[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"
echo -e "[liveupdate]\nmode = Zip\nzip-filepath = build/liveupdate_output\nzip-filename = ${RESOURCES_ZIP}\nsave-zip-in-bundle-folder = 1\npublickey = liveupdate_public.der\nprivatekey = liveupdate_private.der\n\n" > "${LIVEUPDATE_INI}"
sed -i 's/"enabled", true/"enabled", false/' example/level2/set_alt_text.script

rm -rf build
rm -rf "dist/${BUNDLE_DIR}"
mkdir -p "dist/${BUNDLE_DIR}"
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output "dist/${BUNDLE_DIR}/${PLATFORM}" --build-report-html "dist/${BUNDLE_DIR}/build_report_${BUNDLE_DIR}.html" --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv "dist/${BUNDLE_DIR}"/*.html "public/"
rm -rf "public/${BUNDLE_DIR}"
cp -R "dist/${BUNDLE_DIR}/${PLATFORM}/liveupdate_reszip_demo" "public/${BUNDLE_DIR}"

# BUNDLE 2
BUNDLE_DIR=bundle-2
RESOURCES_ZIP="resources_$(date +%s).zip"
echo -e "[liveupdate]\nsettings = /${LIVEUPDATE_INI}\n\n[liveupdate_reszip]\nfilename = ${RESOURCES_ZIP}\npreload_file = ${RESOURCES_ZIP}\n\n" > "${RESZIP_INI}"
echo -e "[liveupdate]\nmode = Zip\nzip-filepath = build/liveupdate_output\nzip-filename = ${RESOURCES_ZIP}\nsave-zip-in-bundle-folder = 1\npublickey = liveupdate_public.der\nprivatekey = liveupdate_private.der\n\n" > "${LIVEUPDATE_INI}"
sed -i 's/"enabled", false/"enabled", true/' example/level2/set_alt_text.script

rm -rf build
rm -rf "dist/${BUNDLE_DIR}"
mkdir -p "dist/${BUNDLE_DIR}"
java -jar bob.jar --email f@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output "dist/${BUNDLE_DIR}/${PLATFORM}" --build-report-html "dist/${BUNDLE_DIR}/build_report_${BUNDLE_DIR}.html" --platform ${PLATFORM} --architectures ${PLATFORM} --archive --liveupdate yes --variant debug resolve build bundle
mv "dist/${BUNDLE_DIR}"/*.html "public/"
rm -rf "public/${BUNDLE_DIR}"
cp -R "dist/${BUNDLE_DIR}/${PLATFORM}/liveupdate_reszip_demo" "public/${BUNDLE_DIR}"

# DONE
# http-server -c-
