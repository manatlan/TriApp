# make.py : a command line to build/install the apk

It's a command line for the full process ! You will need a linux host where docker, git & adb are installed.

Give the "execution" rights to make.py :
```bash 
chmod +x ./make.py
```

# `./make.py init`
Initialize the buildozer docker image from buildozer's git. It will be mandated to be able to build the apk !

# `./make.py build`
Build the apk in `app/bin` folder ! (debug mode)

# `./make.py install`
Plug you device (with usb cable), and it will install the apk on the device

# `./make.py clean`
clean all (delete apks and app/.buildozer)