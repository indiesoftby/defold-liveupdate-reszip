#!/bin/bash

# ⚠⚠⚠ Run the script from the root directory of your project!

# Requires: curl, jq, wget, awk, java >=11
# macOS: brew install jq awk wget openjdk@11
# Ubuntu/Debian/WSL: sudo apt install --no-install-recommends jq wget openjdk-11-jre-headless

# Stop on errors
set -e

# Change dir to script's dir
cd "$(dirname "$0")"

# The output directory - ⚠⚠⚠ add it to .gitignore and to .defignore!
BUNDLE_DIR=dist

# Delete the build directory to force full rebuild
rm -rf build/

# Clean previous bundle result and create the bundle directory
rm -rf "${BUNDLE_DIR}/js-web"
mkdir -p "${BUNDLE_DIR}"

# Get project's title
TITLE=$(awk -F "=" '/^title/ {gsub(/[ \r\n\t]/, "", $2); print $2}' game.project)

# Download bob.jar. It downloads bob.jar only if it's missing or if the version differs
BOB_SHA1=${DEFOLD_BOB_SHA1:-$(curl -s 'https://d.defold.com/stable/info.json' | jq -r .sha1)}
BOB_LOCAL_SHA1=$((java -jar "${BUNDLE_DIR}/bob.jar" --version | cut -d' ' -f6) || true)
if [ "${BOB_LOCAL_SHA1}" != "${BOB_SHA1}" ]; then wget --progress=dot:mega -O "${BUNDLE_DIR}/bob.jar" "https://d.defold.com/archive/${BOB_SHA1}/bob/bob.jar"; fi
java -jar "${BUNDLE_DIR}/bob.jar" --version

# Build the game - the `release` variant with live update content.
java -jar "${BUNDLE_DIR}/bob.jar" --email a@b.com --auth 123 --texture-compression true --bundle-output "${BUNDLE_DIR}/js-web" --platform js-web --archive --liveupdate yes --variant release resolve build bundle

# Move LiveUpdate .zip file into the bundle dir as "resources.zip"
mv build/liveupdate_output/*.zip "${BUNDLE_DIR}/js-web/${TITLE}/resources.zip"

# Done!

