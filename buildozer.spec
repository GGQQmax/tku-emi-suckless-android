[app]

# (str) Title of your application
title = TKU EMI Suckless

# (str) Package name
package.name = tkuemisuckless

# (str) Package domain (needed for android/ios packaging)
package.domain = org.tku

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,html,css,js

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv, .venv, .git, .userData

# (str) Application versioning (method 1)
version = 0.1

requirements = python3,requests,beautifulsoup4,urllib3,chardet,certifi,bottle

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET

# (bool) Automatically accept Android SDK licenses
android.accept_sdk_license = True

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK API to use. This is the minimum API to build with.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) The Android architectures to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (str) The p4a bootstrap to use
p4a.bootstrap = webview

# (int) The port your local web application listens on
p4a.port = 5000

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 0

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
