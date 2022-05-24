from pydoc import resolve
import string
from urllib import response
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


def configTarget(hostname, target_id, scan_speed):
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
        "custom_headers": [],
        "custom_cookies": [],
        "excluded_paths": [],
        "user_agent": "",
        "debug": False
    }
    response = session.patch(
        url, json=body, headers=header, verify=False).status_code
    return response

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


def slowdownScan(target_id, mode):
    response = configTarget(HOST, target_id,mode)
    return response


def createTargetAndScan(target_url, mode="fast"):
    target_id = createTarget(HOST, target_url)["target_id"]
    if (mode != "fast"):
        slowdownScan(target_id, mode)
    scan_id = scanTarget(HOST, target_id)["scan_id"]
    return scan_id


def isScanComplete(scan_id):
    result = getScan(HOST, scan_id)["current_session"]["status"]
    if (result == "processing"):
        return False
    return True


def main():
    running_threads = []
    stack_file = "AutoAcu_stacks_running"
    max_thread = MAX_THREAD
    if os.path.exists(stack_file):
        running_threads = readFile(stack_file)

        for thread in running_threads:
            if (isScanComplete(thread)):
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
        thread = createTargetAndScan(target,SPEED)
        running_threads.append(thread)
    writeToFile(stack_file, running_threads)
    writeToFile(TARGET_LIST, targets[max_thread:])
def getArgs():
    parser = argparse.ArgumentParser(description='Make the automatic task more automatic.')
    parser.add_argument('urls_file',metavar="URLs_File", type=argparse.FileType('r'),help='List of urls')
    parser.add_argument('--threads', type=int, default=3, help='Number of tasks that run simultaneously.')
    parser.add_argument("--speed", default="fast",help='The speed of the scan.')
    parser.add_argument("--host", default="https://localhost:13443",help='The host of the acunetix.')


    args = parser.parse_args()
    return args
def setGlobal(args):
    global TARGET_LIST
    global MAX_THREAD
    global HOST
    global SPEED
    threads = args.threads
    target_file=args.urls_file.name
    host=args.host
    speed = args.speed
    if(speed != "fast" and speed != "moderate"and speed != "slow"and speed != "sequential"):
        print("Wrong speed!")
        exit()
    
    TARGET_LIST = target_file
    MAX_THREAD = threads
    HOST = host
    SPEED = speed



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
