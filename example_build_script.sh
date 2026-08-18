#!/bin/bash

# ⚠⚠⚠ Run the script from the root directory of your project!

# Requires: curl, jq, wget, and a Java version supported by Bob.
# See https://defold.com/manuals/bob/ for current requirements.

# Stop on errors
set -e

# Change dir to script's dir
cd "$(dirname "$0")"

# The output directory - ⚠⚠⚠ add it to .gitignore and to .defignore!
BUNDLE_DIR=dist
PLATFORM=wasm-web

# Delete the build directory to force full rebuild
rm -rf build/

# Clean previous bundle result and create the bundle directory
rm -rf "${BUNDLE_DIR}/${PLATFORM}"
mkdir -p "${BUNDLE_DIR}"

# Filename of the resources archive
RESZIP_INI="reszip.ini"
LIVEUPDATE_INI="liveupdate.generated.settings"
RESOURCES_ZIP="resources_$(date +%s).zip"
trap 'rm -f "${RESZIP_INI}" "${LIVEUPDATE_INI}"' EXIT

cat > "${RESZIP_INI}" <<EOF
[liveupdate]
settings = /${LIVEUPDATE_INI}

[liveupdate_reszip]
filename = ${RESOURCES_ZIP}
preload_file = ${RESOURCES_ZIP}
EOF

cat > "${LIVEUPDATE_INI}" <<EOF
[liveupdate]
mode = Zip
zip-filepath = build/liveupdate_output
zip-filename = ${RESOURCES_ZIP}
save-zip-in-bundle-folder = 1
publickey = liveupdate_public.der
privatekey = liveupdate_private.der
EOF

# Download the latest stable Bob if it is not available locally.
BOB_SHA1=$(curl -s 'https://d.defold.com/stable/info.json' | jq -r .sha1)
BOB_LOCAL_SHA1=$(java -jar "${BUNDLE_DIR}/bob.jar" --version 2>/dev/null | cut -d' ' -f6 || true)
if [ "${BOB_LOCAL_SHA1}" != "${BOB_SHA1}" ]; then wget --progress=dot:mega -O "${BUNDLE_DIR}/bob.jar" "https://d.defold.com/archive/${BOB_SHA1}/bob/bob.jar"; fi
java -jar "${BUNDLE_DIR}/bob.jar" --version

# Build the game - the `release` variant with live update content.
java -jar "${BUNDLE_DIR}/bob.jar" --email a@b.com --auth 123 --texture-compression true --settings "${RESZIP_INI}" --bundle-output "${BUNDLE_DIR}/${PLATFORM}" --platform "${PLATFORM}" --architectures "${PLATFORM}" --archive --liveupdate yes --variant release resolve build bundle

# Done!
