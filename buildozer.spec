[app]
title = My Assistant
package.name = myassistant
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy,plyer,pyjnius
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.build_tools = 34.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
