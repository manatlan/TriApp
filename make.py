#!/usr/local/bin/python3.7 -u
import os,sys,subprocess,json,glob
CWD=os.path.dirname(__file__)
DOCKER="mybuildozer"

def read_spec():
    return dict([ [j.strip() for j in i.split("=",1)] for i in open(f"{CWD}/app/buildozer.spec").read().splitlines() if i.strip() and "=" in i])

def is_docker_image_exists():
    try:
        x=json.loads(subprocess.run(f"docker images {DOCKER} --format json",capture_output=True,shell=True).stdout)
    except:
        x={}
    return "ID" in x

def init():
    assert subprocess.call("which git",shell=True)==0,"install git !"
    assert subprocess.call("which docker",shell=True)==0,"install docker !"
    os.system(f"""
cd /tmp
git clone https://github.com/kivy/buildozer.git
cd buildozer
docker build --tag={DOCKER} .
""")

def build(mode="debug"):
    assert is_docker_image_exists(),"You should 'init' first !"
    os.system(f"""
cd {CWD}/app
mkdir .buildozer
docker run -v $(pwd)/.buildozer:/home/user/.buildozer -v $(pwd):/home/user/hostcwd {DOCKER} android {mode}
""")

def install():
    assert subprocess.call("which adb",shell=True)==0,"install adb !"

    x=read_spec()
    package=x["package.domain"]+"."+x["package.name"]
    name = x["package.name"]

    apks=glob.glob(f"{CWD}/app/bin/{name}-*.apk")
    if apks:
        os.system(f"""
adb uninstall {package}
adb install -r -g {apks[0]}
""")
    else:
        print("no apk in app/bin ?!")

def clean():
    os.system(f"rm -rf {CWD}/app/bin")
    os.system(f"rm -rf {CWD}/app/.buildozer")

if __name__=="__main__":
    assert os.path.isfile(f"{CWD}/app/buildozer.spec"),"wtf?"

    _,*args = sys.argv
    if args==["init"]:
        init()
    elif args==["build"]:
        build()
    elif args==["install"]:
        install()
    elif args==["clean"]:
        clean()
    else:
        print("- init: to generate the docker image")
        print("- build: to build the apk")
        print("- install: to install the apk in plugged device")
        print("- clean: delete apks and app/.buildozer")
