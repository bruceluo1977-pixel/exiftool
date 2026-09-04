[app]
version = 0.1
title = EXIF水印工具
android.accept_sdk_license = True

android.entrypoint = exiftool_android_clientv1.py

package.name = exifwatermark
package.domain = org.exifwatermark.demo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin, venv, __pycache__
source.exclude_exts = spec

requirements = python3,kivy,plyer,pillow,requests,piexif
android.api = 33
android.ndk = 25b
android.target_api = 33

android.permissions = READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,INTERNET
android.uses_cleartext_traffic = True

android.allow_backup = True
orientation = portrait
fullscreen = False
log_level = debug

android.clean_before_build = True

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./buildozer
bin_dir = ./bin
