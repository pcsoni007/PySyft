# stdlib
import base64
import os
import platform
from re import sub
import signal
import subprocess
import sys
import tarfile
import zipfile

# third party
from oblv import OblvClient
import requests

# relative
from ..core.node.common.exceptions import OblvEnclaveError
from ..core.node.common.exceptions import OblvEnclaveUnAuthorizedError
from ..core.node.common.exceptions import OblvError
from .constants import ENCODE_BLACK
from .constants import ENCODE_BOLD
from .constants import ENCODE_NO_STYLE
from .constants import ENCODE_RED

# from ..logger import debug


def check_oblv_proxy_installation_status():
    try:
        result = subprocess.run(["oblv","-V"], capture_output=True, text=True)
        if result.stderr:
            raise subprocess.CalledProcessError(
                    returncode = result.returncode,
                    cmd = result.args,
                    stderr = result.stderr
                    )
        result = result.stdout.strip()
        return result
    except Exception as e:
        if e.__class__==FileNotFoundError:
            system_name = platform.system()
            result = "Oblv Proxy Not Installed. Call the method install_oblv_proxy "
            if system_name=="Windows":
                result += "to install the proxy for this session. If you already have the proxy installed, add it to your PATH." 
            elif system_name=="Linux":
                result += "to install the proxy globally. If you already have the proxy installed, create a link to the installation as /usr/local/bin/oblv" 
            # exp = Exception(result)
            # exp.__suppress_context__ = True
            # exp.__traceback__=None
            # exp.__cause__ = None
            # raise exp
            print(ENCODE_RED+ENCODE_BOLD+"Exception"+ENCODE_BLACK+ENCODE_NO_STYLE+": "+result,file=sys.stderr)
        else:
            raise Exception(e)   
    
def install_oblv_proxy(with_package: bool = False):
    """_summary_

    Args:
        with_package (bool, optional): Only available for .msi, .deb, .rpm. Defaults to False.
    """
    system_name = platform.system()
    if system_name=="Windows":
        windows_proxy_installation(with_package)
    elif system_name=="Linux":
        linux_proxy_installation(with_package)
    elif system_name=="Darwin":
        darwin_proxy_installation()

def windows_proxy_installation(with_package: bool = False):
    try:
        if with_package:
            url='https://api.oblivious.ai/oblv-ccli/0.4.0/packages/oblv-0.4.0-x86_64.msi'
            res = requests.get(url)
            path = os.path.join(os.path.expanduser("~"),"oblv-0.4.0-x86_64.msi")
            with open(path,"wb") as f:
                f.write(res.content)
            os.system('msiexec /I {} /quiet /QB-!'.format(path))
        else:
            url='https://api.oblivious.ai/oblv-ccli/0.4.0/oblv-ccli-0.4.0-x86_64-pc-windows-msvc.zip'
            res = requests.get(url)
            path = os.getcwd().replace('\\','/')+"/oblv-ccli-0.4.0-x86_64-pc-windows-msvc.zip"
            with open(path,"wb") as f:
                f.write(res.content)
            with  zipfile.ZipFile(path, 'r') as zipObj:
                zipObj.extractall()
            os.environ["PATH"] += ";"+os.getcwd() + "\\oblv-ccli-0.4.0-x86_64-pc-windows-msvc;"
    except Exception as e:
        print(ENCODE_RED+ENCODE_BOLD+"Exception"+ENCODE_BLACK+ENCODE_NO_STYLE+": "+e.__cause__,file=sys.stderr)

def linux_proxy_installation(with_package: bool = False):
    try:
        if with_package:
            try:
                os.system("dpkg")
            except Exception as e:
                url='https://api.oblivious.ai/oblv-ccli/0.4.0/packages/oblv-0.4.0-1.x86_64.rpm'
                res = requests.get(url)
                path = os.path.join(os.path.expanduser("~"),"oblv-0.4.0-1.x86_64.rpm")
                with open(path,"wb") as f:
                    f.write(res.content)
                os.system('rpm -i {}'.format(path))
            else:
                url='https://api.oblivious.ai/oblv-ccli/0.4.0/packages/oblv_0.4.0_amd64.deb'
                res = requests.get(url)
                path = os.path.join(os.path.expanduser("~"),"oblv_0.4.0_amd64.deb")
                with open(path,"wb") as f:
                    f.write(res.content)
                os.system('dpkg -i {}'.format(path))
        else:
            url='https://api.oblivious.ai/oblv-ccli/0.4.0/oblv-ccli-0.4.0-x86_64-unknown-linux-musl.tar.gz'
            res = requests.get(url)
            path = os.getcwd()+"/oblv-ccli-0.4.0-x86_64-unknown-linux-musl"
            file = tarfile.open(fileobj=res.content)
            file.extractall(path)
            os.symlink('/usr/local/bin/oblv', os.getcwd()+"/oblv-ccli-0.4.0-x86_64-unknown-linux-musl/oblv")    
    except Exception as e:
        print(ENCODE_RED+ENCODE_BOLD+"Exception"+ENCODE_BLACK+ENCODE_NO_STYLE+": "+e.__cause__,file=sys.stderr)
    # with open(path,"wb") as f:
    #     f.write(res.content)
    # with  zipfile.ZipFile(path, 'r') as zipObj:
    #     zipObj.extractall()
    

def darwin_proxy_installation():
    url='https://api.oblivious.ai/oblv-ccli/0.4.0/oblv-ccli-0.4.0-x86_64-apple-darwin.tar.gz'
    res = requests.get(url)
    path = os.getcwd()+"/oblv-ccli-0.4.0-x86_64-apple-darwin"
    file = tarfile.open(fileobj=res.content)
    file.extractall(path)
    # with open(path,"wb") as f:
    #     f.write(res.content)
    # with  zipfile.ZipFile(path, 'r') as zipObj:
        # zipObj.extractall()
    ###Need to test this out
    os.symlink('/usr/local/bin/oblv', os.getcwd()+"/oblv-ccli-0.4.0-x86_64-apple-darwin/oblv")
    
def create_oblv_key_pair(key_name):
    if check_oblv_proxy_installation_status()==None:
        return
    try:
        file_path=os.path.join(os.path.expanduser('~'),'.ssh',key_name)
        result = subprocess.run(["oblv", "keygen", "--key-name", key_name,"--output",file_path],capture_output=True)
        if result.stderr:
            raise subprocess.CalledProcessError(
                    returncode = result.returncode,
                    cmd = result.args,
                    stderr = result.stderr
                    )
        result = result.stdout.strip()
        return get_oblv_public_key(key_name)
    except Exception as e:
        raise Exception(e)   

def get_oblv_public_key(key_name):
    try:
        filepath = os.path.join(os.path.expanduser('~'),'.ssh',key_name,key_name+'_public.der')
        with open(filepath,'rb') as f:
            public_key=f.read()
        public_key = base64.encodebytes(public_key).decode("UTF-8").replace("\n","")
        return public_key
    except FileNotFoundError:
        print(ENCODE_RED+ENCODE_BOLD+"Exception"+ENCODE_BLACK+ENCODE_NO_STYLE+": "+"No key found with given name",file=sys.stderr)
    except Exception as e:
        raise Exception(e)