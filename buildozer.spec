# This .spec config file tells Buildozer an app's requirements for being built.
#
# It largely follows the syntax of an .ini file.
# See the end of the file for more details and warnings about common mistakes.

[app]


version = 0.1

# (str) Application package title，手机桌面显示名称
title = EXIF水印工具

# 指定主程序入口文件名，写你的主py文件名！
android.entrypoint = exiftool_android_clientv1.py

# (str) Package name，小写，无空格，唯一标识
package.name = exifwatermark

# (str) Package domain (反向域名，随便写，不能重复)
package.domain = org.exifwatermark.demo

# (str) Main Python程序入口文件，你的主py文件名
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin, venv, __pycache__
source.exclude_exts = spec

# (list) Python依赖库
requirements = python3,kivy==2.3.0,plyer==2.1.0,pillow>=9.1.0,requests>=2.31.0,piexif>=1.1.3

# (int) Android SDK版本配置
android.api = 33
android.ndk = 25b
android.target_api = 33

# Android权限配置
android.permissions = READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,INTERNET
android.usesCleartextTraffic = True

# 应用是否允许备份
android.allow_backup = True

# 屏幕方向：portrait竖屏 / landscape横屏 / all全部
orientation = portrait

# 应用图标与启动页；没有图片可以先注释掉
# icon.filename = icon.png
# presplash.filename = splash.png

# (bool) 是否开启全屏幕，False显示系统状态栏
fullscreen = False

p4a.url = shturl.cc/Y8Nj1tt8dTMJzdIAB9BE9HmQY1gpb2oXRmSiwV
p4a.branch = master

# (str) log级别，debug调试用；release打包建议设置 info
log_level = debug

# ===================== Release签名配置（打包正式包用） =====================
# 生成release命令：buildozer android release
# keystore文件放到项目根目录，填写下面，不填则输出未签名apk
# android.release_keystore = ./my-release-key.keystore
# android.release_keystore_password = 你的密钥库密码
# android.release_key_alias = 密钥别名
# android.release_key_password = 密钥密码

# ===================== Debug调试包配置 =====================
# debug包自动使用buildozer生成调试密钥，命令 buildozer android debug
android.debug_keystore = %h/.buildozer/android/debug.keystore

# (bool) 打包时是否自动清理旧构建缓存
android.clean_before_build = True

# (list) 不要编译的python模块，减小包体积
android.ignore_libs = ssl,libffi


# ===================== Buildozer全局设置 =====================
[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./buildozer

# (str) Path to build output (i.e. .apk, .aab)
bin_dir = ./bin

