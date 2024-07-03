import json
import os
from datetime import datetime
import logging
import platform

# Prompt user for base_url
base_url = input("Enter the base_url: ").strip()

# Load CONFIG data from config.json
with open('config.json') as config_file:
    CONFIG = json.load(config_file)

LOG_FILE = "api_requests.log"

# Set up logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(message)s')

def check_requests_module():
    try:
        import requests
        print("requests module is already installed.")
    except ImportError:
        print("requests module is not installed. Installing...")
        try:
            install_pip_if_needed()
            os.system('pip install requests')
            print("requests module installed successfully.")
        except Exception as e:
            print("Failed to install requests module: {}".format(str(e)))

def install_pip_if_needed():
    try:
        import pip
        print("pip is already installed.")
    except ImportError:
        print("pip is not installed. Installing pip...")
        try:
            if platform.system() == 'Linux':
                install_pip_for_linux()
            elif platform.system() == 'Windows':
                install_pip_for_windows()
            elif platform.system() == 'Darwin':  # macOS
                install_pip_for_macos()
            else:
                raise RuntimeError("Unsupported operating system: {}".format(platform.system()))
            print("pip installed successfully.")
        except Exception as e:
            print("Failed to install pip: {}".format(str(e)))

def install_pip_for_linux():
    try:
        os.system('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
        os.system('python get-pip.py --user')
        os.system('rm get-pip.py')
    except Exception as e:
        raise RuntimeError("Failed to install pip: {}".format(str(e)))

def install_pip_for_windows():
    try:
        os.system('python -m ensurepip --upgrade --user')
    except Exception as e:
        raise RuntimeError("Failed to install pip: {}".format(str(e)))

def install_pip_for_macos():
    try:
        os.system('sudo easy_install pip')
    except Exception as e:
        raise RuntimeError("Failed to install pip: {}".format(str(e)))
    
check_requests_module()
import requests

def check_status_code(response_code):
    if response_code == 200:
        return "SUCCESS"
    else:
        return "FAILED ({})".format(response_code)

def get_token(config):
    token_url = base_url + config["config"]["token_url"]
    print("Getting new token from {}...".format(token_url))
    response = requests.get(token_url)
    response.raise_for_status()
    token = response.text.strip()
    if not token:
        raise ValueError("Failed to obtain token.")
    logging.info("New token obtained successfully!\n")
    print("New token obtained successfully!\n")
    return token

def make_request(url, headers, data=None):
    try:
        response = requests.post(url, headers=headers, json=data) if data else requests.get(url, headers=headers)
        response.raise_for_status()
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        return response.status_code, str(e)

def process_avs(config, token):
    avs = config["api_requests"]["avs"]
    successful_requests = 0
    failed_requests = 0
    
    def log_request(url, payload, token):
        nonlocal successful_requests, failed_requests
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }

        response_code, response_body = make_request(url, headers, payload)
        
        logging.info("URL: \n{}\n".format(url))
        logging.info("Response Code: \n{}\n".format(response_code))
        if str(response_code).startswith('2'):
            logging.info("SUCCESS\n")
            successful_requests += 1
        else:
            logging.error("Response Body:\n{}\n".format(response_body))
            logging.error("FAILED ({})\n".format(response_code))
            failed_requests += 1

        print("URL: {}, Response Code: {}".format(url, response_code))
        if str(response_code).startswith('2'):
            print("SUCCESS\n")
        else:
            print("Response Body:\n{}".format(response_body))
            print("FAILED ({})\n".format(response_code))

    for av in avs:
        av_name = av["av_name"]
        boss_query_url = base_url + config["config"]["boss_query_url"]
        hierarchy_query_url = base_url + config["config"]["hierarchy_query_url"]
        ads_data_extract_url = base_url + config["config"]["ads_data_extract_url"]
        ads_member_extract_url = base_url + config["config"]["ads_member_extract_url"]

        boss_query_payload = av["boss_query_request_payload"]
        hierarchy_query_payload_list = av["hierarchy_query_request_payload"]
        ads_data_extract_payload = av["ads_data_extract_query_request_payload"]
        ads_member_extract_payload = av["ads_member_extract_query_request_payload"]

        logging.info("%%%%%%%%%%%%%%%%%%%%%% Processing AV: {} %%%%%%%%%%%%%%%%%%%%%%%%%\n".format(av_name))
        print("%%%%%%%%%%%%%%%%%%%%%% Processing AV: {} %%%%%%%%%%%%%%%%%%%%%%%%%\n".format(av_name))
        
        logging.info("=====================================================================================================================================\n")
        logging.info("BOSS Query Response...\n".format(av_name))
        print("BOSS Query Response...\n".format(av_name))
        log_request(boss_query_url, boss_query_payload, token)
        
        logging.info("=====================================================================================================================================\n")
        logging.info("Querying Hierarchies...\n".format(av_name))
        print("Querying Hierarchies...\n".format(av_name))
        for query_payload in hierarchy_query_payload_list:
            logging.info("{}...\n".format(next(iter(query_payload['hierarchies']))))
            log_request(hierarchy_query_url, query_payload, token)
            logging.info("-------------------------------------------------------------------------------------------------------------------------------------\n")
        
        logging.info("=====================================================================================================================================\n")
        logging.info("Extract Query Response...\n".format(av_name))
        print("Extract Query Response...\n".format(av_name))
        log_request(ads_data_extract_url, ads_data_extract_payload, token)
        
        logging.info("=====================================================================================================================================\n")
        logging.info("ADS Member Extract Query Response...\n".format(av_name))
        print("ADS Member Extract Query Response...\n".format(av_name))
        log_request(ads_member_extract_url, ads_member_extract_payload, token)
        
        logging.info("=====================================================================================================================================\n")
    
    logging.info("Summary of API Requests:")
    logging.info("Successful Requests (Status 2xx): {}".format(successful_requests))
    logging.info("Failed Requests: {}\n".format(failed_requests))

    print("Summary of API Requests:")
    print("Successful Requests (Status 2xx): {}".format(successful_requests))
    print("Failed Requests: {}\n".format(failed_requests))

def main():
    token = get_token(CONFIG)
    process_avs(CONFIG, token)

if __name__ == "__main__":
    logging.info("Starting API requests...\n")
    print("Starting API requests...\n")
    print("------------------------------------")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("------------------------------------\n")
    main()
    logging.info("All API requests completed!!!\n")
    print("All API requests completed!!!\n")
