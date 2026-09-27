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

[buildozer]
log_level = 2
warn_on_root = 1
