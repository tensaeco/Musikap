[app]

title = Amharic Music Generator
package.name = musicapp
package.domain = org.tensa

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy,requests

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 31
android.minapi = 21

[buildozer]

log_level = 2
warn_on_root = 1
