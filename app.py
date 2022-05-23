from pydoc import resolve
from urllib import response
import requests
import os
from dotenv import load_dotenv
from yaml import scan
import time

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


load_dotenv()
API_KEY = os.getenv("API")
header = {
    "Accept": "application/json",
    "X-Auth": API_KEY
}
session = requests.Session()


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


def writeToFile(filename, strings):
    file = open(filename, 'w+')
    for string in strings:
        file.write(string+'\n')
    file.close()


def readFile(filename):
    with open(filename) as file:
        strings = file.readlines()
    return [string.strip('\n') for string in strings]


def createTargetAndScan(target_url):
    target_id = createTarget(HOST, target_url)["target_id"]
    scan_id = scanTarget(HOST, target_id)["scan_id"]
    return scan_id


def isScanComplete(scan_id):
    result = getScan(HOST, scan_id)["current_session"]["status"]
    if (result == "completed"):
        return True
    return False


TARGET_LIST = "urls.txt"
MAX_THREAD = 3
HOST = "https://localhost:13443"


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
        thread = createTargetAndScan(target)
        running_threads.append(thread)
    writeToFile(stack_file, running_threads)
    writeToFile(TARGET_LIST, targets[max_thread:])


if __name__ == "__main__":
    # print(getScan(HOST,"1a990c5b-44a0-4778-91da-30209230f756"))
    print("running...")
    while True:
        try:
            main()
            time.sleep(300)
        except KeyboardInterrupt:
            print("stop!")
            exit()