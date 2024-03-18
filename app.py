from pydoc import resolve
import string
from urllib import response
from urllib.parse import urlparse
import requests
import os
from dotenv import load_dotenv
from yaml import scan
import time
import argparse
import sys


from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


load_dotenv()
API_KEY = os.getenv("API")
header = {
    "Accept": "application/json",
    "X-Auth": API_KEY
}
session = requests.Session()
#######################################################################
# API


def getScan(hostname, id):
    url = "{}/api/v1/scans/{}".format(hostname, id)
    response = session.get(url, headers=header, verify=False).json()
    return response


def createTarget(hostname, target_url):
    url = "{}/api/v1/targets".format(hostname)
    body = {
        "address": target_url,
        "description": "",
        "type": "default",
        "criticality": 10
    }
    response = session.post(
        url, json=body, headers=header, verify=False).json()
    return response


def scanTarget(hostname, target_id):
    url = "{}/api/v1/scans".format(hostname)
    body = {
        "target_id": target_id,
        "profile_id": "11111111-1111-1111-1111-111111111111",
        "schedule": {
            "disable": False,
            "start_date": None,
            "time_sensitive": False
        }
    }
    response = session.post(
        url, json=body, headers=header, verify=False).json()
    return response


def configTarget(hostname, target_id, scan_speed,custom_headers=[]):
    url = "{}/api/v1/targets/{}/configuration".format(hostname, target_id)
    body = {
        "description": "Target configuration default values",
        "limit_crawler_scope": True,
        "login": {
            "kind": "none"
        },
        "sensor": False,
        "ssh_credentials": {
            "kind": "none"
        },
        "proxy": {
            "enabled": False
        },
        "authentication": {
            "enabled": False
        },
        "client_certificate_password": "",
        "scan_speed": scan_speed,
        "case_sensitive": "auto",
        "technologies": [],
        "custom_headers": custom_headers,
        "custom_cookies": [],
        "excluded_paths": [],
        "user_agent": "",
        "debug": False
    }
    response = session.patch(
        url, json=body, headers=header, verify=False).status_code
    return response

# def configContinuousScan(hostname, target_id,mode):
#     url = "{}/api/v1/targets/{}/continuous_scan".format(hostname, target_id)
#     body = {
#     "enabled": mode
#     }
#     response = session.post(
#         url,json=body, headers=header, verify=False).status_code
#     return response
def getUploadURL(hostname, target_id,filename,filesize):
    url = "{}/api/v1/targets/{}/configuration/imports".format(hostname, target_id)
    body = {
        "name": filename,
        "size": filesize
    }
    response = session.post(
        url, json=body, headers=header, verify=False).json()
    return response["upload_url"]
#######################################################################
# User


def writeToFile(filename, strings):
    file = open(filename, 'w+')
    for string in strings:
        file.write(string+'\n')
    file.close()


def readFile(filename):
    with open(filename) as file:
        strings = file.readlines()
    return [string.strip('\n') for string in strings]


def configScan(target_id, mode,headers):
    response = configTarget(SERVER, target_id,mode,headers)
    return response


def createTargetAndScan(target_url, mode="fast", headers=[]):
    target_id = createTarget(SERVER, target_url)["target_id"]
    #config target
    if (mode != "fast" or headers!=[]):
        configScan(target_id, mode,headers)
    domain = getDomain(target_url)
    if(WAYMORE_DIR):
        slash ="" if WAYMORE_DIR[-1] =="/" else "/"
        waymore_file=WAYMORE_DIR+slash+domain+"/waymore.txt"
        print("[DEBUG]:",waymore_file)
        if(WAYMORE_DIR!= "" and os.path.exists(waymore_file)):
            uploadFileToServer(target_id,waymore_file)
            print("[DEBUG]: UPLOADED")
    scan_id = scanTarget(SERVER, target_id)["scan_id"]
    return scan_id


def isScanComplete(scan_id):
    result = getScan(SERVER, scan_id)["current_session"]["status"]
    if (result == "processing"):
        return False
    return True

def getAddress(scan_id):
    result = getScan(SERVER, scan_id)["target"]["address"]
    return result

def writeAppend(filename, string):
    file = open(filename, 'a')
    file.write(string+'\n')
    file.close()

def uploadFileToServer(target_id,file_location):
    file_size = os.path.getsize(file_location)
    file_name = os.path.basename(file_location)
    upload_url = SERVER + getUploadURL(SERVER,target_id,file_name,file_size)
    headers = {'Content-Type': 'application/octet-stream','Content-Disposition': 'attachment; filename="'+file_name+'"'}
    
    # proxies = {'http':'http://192.168.9.212:8081/','https':'http://192.168.9.212:8081/'}
    
    chunk_size = 1048576
    with open(file_location,'rb') as file:
        start_byte = 0
        while True:
            chunk = file.read(chunk_size)
            end_byte = start_byte + chunk_size
            if(end_byte>file_size):end_byte=file_size 
            if not chunk:
                break  # End of file
            headers.update({"Content-Range":"bytes "+str(start_byte)+"-"+str(end_byte - 1)+"/"+str(file_size)})
            # Send the POST request
            response = requests.post(upload_url, data=chunk, headers=headers,verify=False)

            # Check if the request was successful
            if response.status_code != 201 and response.status_code != 202 and response.status_code != 204:
                print(f"Failed to upload chunk ({file.tell()} bytes): {response.text}")
                return False

            start_byte = end_byte        
        
    return True
        
def getDomain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def main():
    running_threads = []
    stack_file = "AutoAcu_stacks_running"
    max_thread = MAX_THREAD
    if os.path.exists(stack_file):
        running_threads = readFile(stack_file)
        remove_threads=[]
        for thread in running_threads:
            if (isScanComplete(thread)):
                remove_threads.append(thread)
        
        for thread in remove_threads:
            running_threads.remove(thread)

        running_threads_number = len(running_threads)
        if(running_threads_number == MAX_THREAD):
            return

        max_thread -= running_threads_number
    if os.path.exists(TARGET_LIST):
        targets = readFile(TARGET_LIST)
    else:
        print("Missing urls file!")
        exit()

    for target in targets[:max_thread]:
        thread = createTargetAndScan(target,SPEED,HEADERS)
        running_threads.append(thread)
    writeToFile(stack_file, running_threads)
    writeToFile(TARGET_LIST, targets[max_thread:])

def getArgs():
    parser = argparse.ArgumentParser(description='Make the automatic task more automatic.')
    parser.add_argument('urls_file',metavar="URLs_File", type=argparse.FileType('r'),help='List of urls')
    parser.add_argument('--threads', type=int, default=3, help='Number of tasks that run simultaneously.')
    parser.add_argument("--speed", default="fast",help='The speed of the scan.')
    parser.add_argument("--host", default="https://localhost:13443",help='The host of the acunetix.')
    parser.add_argument("--header", action="append",default=[],help='Add 1 custom header.')
    parser.add_argument("--waymore_dir",metavar="waymore_dir",help='API crawler\'s result directory.')

    args = parser.parse_args()
    return args

def setGlobal(args):
    global TARGET_LIST
    global MAX_THREAD
    global SERVER
    global SPEED
    global HEADERS
    global WAYMORE_DIR

    threads = args.threads
    target_file=args.urls_file.name
    host=args.host
    speed = args.speed
    headers=args.header
    waymore_dir = args.waymore_dir

    if(speed != "fast" and speed != "moderate"and speed != "slow"and speed != "sequential"):
        print("Wrong speed!")
        exit()
    
    TARGET_LIST = target_file
    MAX_THREAD = threads
    SERVER = host
    SPEED = speed
    HEADERS=headers
    WAYMORE_DIR = waymore_dir



if __name__ == "__main__":
    args = getArgs()
    setGlobal(args)
    print("""Script running...
    Ctrl + C to stop.
    """)
    while True:
        try:
            main()
            time.sleep(300)
        except KeyboardInterrupt:
            print("stop!")
            exit()
