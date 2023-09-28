from typing import List, Optional
import asyncio
import os
import concurrent.futures
import requests
import re
import random
import time
from tqdm import tqdm
import socket
import logging
import traceback
from functools import lru_cache
from colorama import Fore, Style, init
import pyfiglet
from termcolor import cprint
from pyfiglet import figlet_format
import sys
import aiohttp
import os.path
from prettytable import PrettyTable
from termcolor import colored
from collections import deque

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s [%(levelname)s] - %(message)s',  # Set the log message format
    filename='proxy_checker.log'  # Set the log file
)

# Initialize the latencies dictionary
latencies = {}

# Initialize colorama
init(autoreset=True)

def configure_logging(log_level: str = 'INFO') -> None:
    """Configure colored logging with different colors for INFO, WARNING, and ERROR messages."""
    format_string = os.getenv('LOG_FORMAT', '[%(asctime)s] [%(levelname)s] %(message)s')
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    
    logger = logging.getLogger(__name__)
    
    console_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            console_handler = handler
            break
    if not console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level))
    
    logger.addHandler(console_handler)
    console_handler.close()

def print_colored_message(message, color):
    """Print a colored message to the console."""
    try:
        print(f"{color}{message}{Style.RESET_ALL}")
    except Exception as e:
        print(f"Error occurred during print operation: {e}")


def test_proxy_latency(proxy, proxy_type):
    'Test the latency of a proxy by making a HTTP request to httpbin.org/get and measuring the elapsed time'
    try:
        start_time = time.time()
        response = requests.get('https://httpbin.org/get', proxies={proxy_type: f"{proxy_type}://{proxy}"}, timeout=15)
        end_time = time.time()
        latency = end_time - start_time
        return proxy, latency
    except:
        return None

async def async_check_proxy(proxy, proxy_type):
    'Check if a proxy is working asynchronously using aiohttp with improved error handling'
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.get('https://httpbin.org/ip', proxy=f"{proxy_type}://{proxy}", timeout=15) as response:
                if response.status != 200:
                    return None
                latency = time.time() - start_time
                return proxy, latency
    except Exception as e:
        logging.error(f"Error checking proxy {proxy}: {str(e)}")
        logging.debug(traceback.format_exc())
        return None

def save_proxies_with_timestamp(proxy_dict):
    """Save proxies from the proxy dict to text files by type and add a timestamp"""
    for proxy_type in proxy_dict.keys():
        out_file = f'{proxy_type}.txt'
        with open(out_file, 'w') as f:
            f.write(f"# Timestamp: {time.time()}\n")
            for proxy in proxy_dict[proxy_type]:
                f.write(proxy + '\n')
        logging.info(f"Saved {len(proxy_dict[proxy_type])} {proxy_type} proxies to {out_file}")

def load_proxies_with_timestamp(proxy_type):
    """Load proxies from a text file by type and check if they were recently downloaded"""
    file_path = f"{proxy_type}.txt"
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Check if the first line is formatted correctly and contains a valid timestamp
    timestamp_line = lines[0]
    if not timestamp_line.startswith("# Timestamp: "):
        logging.warning(f"Invalid timestamp line in {file_path}: {timestamp_line}")
        return None

    try:
        timestamp = float(timestamp_line.split(": ")[1])
    except (IndexError, ValueError) as e:
        logging.warning(f"Invalid timestamp line in {file_path}: {timestamp_line}")
        return None

    if time.time() - timestamp > 3600:  # Check if the proxies were downloaded more than an hour ago
        return None

    return [line.strip() for line in lines[1:]]

class DownloadProxies:
    def __init__(self):
        logging.debug('Starting proxy checking')
        self.proxy_urls = self.read_proxy_urls_from_file("proxy_urls.txt")
        self.user_agents = self.read_user_agents_from_file("user_agents.txt")
        self.proxy_dict = {'socks4': [], 'socks5': [], 'http': [], 'https': []}
        logging.debug('Finished proxy checking')
        
    def read_proxy_urls_from_file(self, filename):
        """Read proxy urls from a text file and store them in a dictionary by type"""
        with open(filename, "r") as f:
            content = f.read()
        proxy_urls = {}
        current_type = None
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue  # Skip blank lines
            if line.endswith(":"):
                current_type = line[:-1]
                proxy_urls[current_type] = []
            else:
                proxy_urls[current_type].append(line)
        return proxy_urls

    def read_user_agents_from_file(self, filename):
        """Read user agents from a text file and store them in a list"""
        with open(filename, "r") as f:
            return [line.strip() for line in f]

    def create_proxy_file(self, proxy_type):
        """Create an empty proxy file for the specified type if it doesn't exist"""
        file_path = f"{proxy_type}.txt"
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass

    def fetch_proxies(self):
        """Fetch proxies from the sources in the proxy urls dictionary and store them in the proxy dict by type"""
        for proxy_type, sources in self.proxy_urls.items():
            for source in sources:
                try:
                    headers = {
                        "User-Agent": random.choice(self.user_agents),
                        "Referer": "https://www.google.com/",
                        "Accept-Language": "en-US,en;q=0.9",
                        "DNT": "1"
                    }
                    response = requests.get(source, headers=headers, timeout=15)
                    if response.status_code == requests.codes.ok:
                        proxies = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}', response.text)
                        self.proxy_dict[proxy_type] += list(set(proxies))
                        logging.info(f"Fetched {len(proxies)} {proxy_type} proxies from {source}")
                except requests.RequestException as e:
                    logging.warning(f"Failed to fetch proxies from {source}: {e}")

            # Create proxy file if it doesn't exist
            self.create_proxy_file(proxy_type)

        logging.info("Proxy fetching done")

    def save_proxies(self):
        """Save proxies from the proxy dict to text files by type"""
        for proxy_type in self.proxy_dict.keys():
            filtered_proxies = [proxy for proxy in self.proxy_dict[proxy_type] if '#' not in proxy and proxy != '\n']
            self.proxy_dict[proxy_type] = list(set(filtered_proxies))
            out_file = f'{proxy_type}.txt'
            with open(out_file, 'w') as f:
                for proxy in self.proxy_dict[proxy_type]:
                    f.write(proxy + '\n')
            logging.info(f"Saved {len(self.proxy_dict[proxy_type])} {proxy_type} proxies to {out_file}")

@lru_cache(maxsize=32)
def check_proxy(proxy, proxy_type):
    """Check if a proxy is working by making a HTTP request to httpbin.org/ip and return the proxy if successful"""
    try:
        response = requests.get("https://httpbin.org/ip", proxies={proxy_type: f"{proxy_type}://{proxy}"}, timeout=15)
        if response and response.status_code == 200:
            logging.info(f"Proxy {proxy} is working.")
            return proxy
        else:
            logging.warning(f"Proxy {proxy} returned a non-200 status code.")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking proxy {proxy}: {str(e)}")
        return None

def check_proxies(proxy_type, num_proxies_to_check=None):
    """Check proxies from a text file by type and return a list of working proxies"""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]

    proxy_type = proxy_type.lower()  # Ensure lowercase
    file_path = f"{proxy_type}.txt"
    with open(file_path, "r") as f:
        data = f.read().split("\n")

    if num_proxies_to_check and num_proxies_to_check < len(data):
        data = data[:num_proxies_to_check]

    total_proxies = len(data)
    logging.info(f"Checking {total_proxies} {proxy_type} proxies")

    working_proxies = []
    pbar = tqdm(total=total_proxies, miniters=1, unit="proxy", leave=False)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for proxy in data:
            future = executor.submit(check_proxy, proxy, proxy_type)
            futures.append(future)
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if result := future.result():
                working_proxies.append(result)

            # Check if latency exceeds the timeout (15 seconds) and set category to "Timeout"
            latency = latencies.get(result, {}).get("latency", float("inf"))
            if latency >= 15:
                latency_category = "Timeout"
            else:
                latency_category = categorize_latency(latency)

            pbar.bar_format = f"{colors[i % len(colors)]}{{l_bar}}{{bar}}|{{n_fmt}}/{{total_fmt}} [{Style.RESET_ALL}{{rate_fmt}}]"
            pbar.update(1)
            pbar.set_postfix({'Working Proxies': len(working_proxies)})

    pbar.close()
    logging.info(f"Found {len(working_proxies)} working {proxy_type} proxies.")
    return working_proxies


def retrieve_proxy_info(ip):
    "Retrieve the country, city, and ISP of a proxy using the ipapi service"
    try:
        url = f"https://ipapi.co/{ip}/json/"
        response = requests.get(url)
        data = response.json()
        country = data.get("country_name", "Unknown")
        city = data.get("city", "Unknown")
        isp = data.get("org", "Unknown")
        return country, city, isp
    except Exception as e:
        return "Unknown", "Unknown", "Unknown"

def get_proxy_info(proxy):
    try:
        ip = proxy.split(":")[0]
        return retrieve_proxy_info(ip)
    except Exception as e:
        logging.error(f"Error retrieving proxy info: {str(e)}")
        return "Unknown", "Unknown", "Unknown"
        
def check_proxy_anonymity(proxy, proxy_type):
    """Check the anonymity level of a proxy by sending a request to a test site and analyzing the headers"""
    try:
        response = requests.get("https://httpbin.org/headers", proxies={proxy_type: f"{proxy_type}://{proxy}"}, timeout=15)
        headers = response.json()["headers"]
        
        # Check if certain headers indicate proxy types
        proxy_types = ["X-Real-Ip", "X-Forwarded-For", "Via", "Proxy-Connection"]
        if any(header in headers for header in proxy_types):
            return "Transparent"
        elif not any(header in headers for header in proxy_types[:2]) and any(header in headers for header in proxy_types[2:]):
            return "Anonymous"
        else:
            return "Elite"
    except Exception as e:
        logging.exception(f"An exception occurred while checking proxy anonymity: {e}")

def check_proxy_latencies(working_proxies, proxy_type):
    """Check the latencies of working proxies by type and return a dictionary of proxies and latencies."""
    logging.info(f"Testing latencies of working {proxy_type} proxies")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(test_proxy_latency, proxy, proxy_type) for proxy in working_proxies]

        latencies = {}
        pbar = tqdm(total=len(futures), desc="Checking proxy latencies")
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            pbar.update(1)
            if result:
                proxy, latency = result
                latency_category = categorize_latency(latency)  # Categorize latency
                future_info = executor.submit(get_proxy_info, proxy)  # Retrieve proxy information concurrently
                future_anonymity = executor.submit(check_proxy_anonymity, proxy, proxy_type)  # Check proxy anonymity concurrently
                country, city, isp = future_info.result()
                anonymity = future_anonymity.result()
                latencies[proxy] = {
                    "latency": latency,
                    "latency_category": latency_category,  # Include latency category
                    "country": country,
                    "city": city,
                    "isp": isp,
                    "anonymity": anonymity
                }

    return latencies

    
def categorize_latency(latency_ms: float) -> str:
    """
    Categorize latencies into descriptive categories based on their values.

    Args:
        latency_ms (float): The latency value in milliseconds.

    Returns:
        str: A string representing the category of the latency value. Possible values are "Very Low", "Low", "Medium", or "High".

    Raises:
        ValueError: If latency_ms is not a number.
    """
    if not isinstance(latency_ms, (int, float)):
        raise ValueError("Latency must be a number")

    if latency_ms < 50:
        return "Very Low"
    elif latency_ms < 100:
        return "Low"
    elif latency_ms < 300:
        return "Medium"
    else:
        return "High"

class ProxyRotator:
    """
    The `ProxyRotator` class is used to manage a list of proxies and rotate through them.
    """

    def __init__(self, proxies: List[str]):
        """
        Initializes the `ProxyRotator` object with a list of proxies.

        Args:
            proxies (List[str]): A list of proxies.
        """
        self.proxies = deque(proxies)

    def remove_proxy(self, proxy: str) -> None:
        """
        Removes a specific proxy from the list of proxies.

        Args:
            proxy (str): The proxy to be removed.
        """
        self.proxies.remove(proxy)

    def get_next_proxy(self) -> Optional[str]:
        """
        Returns the next proxy in the rotation.

        Returns:
            Optional[str]: The next proxy in the rotation, or None if there are no more proxies.
        """
        if self.proxies:
            proxy = self.proxies.popleft()
            self.proxies.append(proxy)
            return proxy
        return None

if __name__ == '__main__':
    configure_logging()
    text = "Proxy Scraper Checker"
    cprint(figlet_format(text, font="standard"), "red")

    # Load previously downloaded proxies if available
    loaded_proxies = {}
    for proxy_type in ['http', 'https', 'socks4', 'socks5']:
        loaded_proxies[proxy_type] = load_proxies_with_timestamp(proxy_type)

    # If no previously downloaded proxies are available or they are outdated, download new ones
    if not all(loaded_proxies.values()):
        print_colored_message("No recently downloaded proxies found. Downloading new ones...", Fore.YELLOW)
        proxy_downloader = DownloadProxies()
        proxy_downloader.fetch_proxies()
        save_proxies_with_timestamp(proxy_downloader.proxy_dict)
        loaded_proxies.update(proxy_downloader.proxy_dict)

    initial_thread_workers = 2
    max_thread_workers = min(os.cpu_count() * 2, 20)

    # Shuffle proxies to avoid consistent order
    for proxy_type in loaded_proxies.keys():
        random.shuffle(loaded_proxies[proxy_type])

    proxy_types = ['http', 'https', 'socks4', 'socks5']
    print_colored_message("Available proxy types: " + ", ".join(proxy_types), Fore.GREEN)

    while True:
        proxy_type_to_check = input(Fore.YELLOW + "Choose a proxy type to check (http/https/socks4/socks5): ").strip().lower()
        if proxy_type_to_check in proxy_types:
            break
        else:
            print(Fore.RED + "Invalid proxy type. Please choose from http/https/socks4/socks5.")

    num_proxies_to_check = int(input(Fore.YELLOW + "How many proxies do you want to check? (Enter a number or leave empty to check all): ") or len(loaded_proxies[proxy_type_to_check]))
    working_proxies = check_proxies(proxy_type_to_check, num_proxies_to_check)
    print_colored_message("Working proxies: " + ", ".join(working_proxies), Fore.GREEN)

    with concurrent.futures.ThreadPoolExecutor(max_workers=initial_thread_workers) as executor:
        logging.info("Available proxy types: " + ", ".join(proxy_types))
        latencies = check_proxy_latencies(working_proxies, proxy_type_to_check)
        
        # Create latencies table
        table = PrettyTable()
        table.field_names = ["Proxy", "Latency (ms)", "Country", "City", "ISP", "Anonymity"]
        # Sort working proxies by latency
working_proxies.sort(key=lambda proxy: latencies.get(proxy, {}).get("latency", float("inf")))

for proxy in working_proxies:
    latency = latencies.get(proxy, {}).get("latency", float("inf"))

    # Define the color of latency based on its value
    if latency < 1:
        latency_color = "green"
    elif latency < 5:
        latency_color = "yellow"
    else:
        latency_color = "red"

    # Fetch the various other details of the proxy
    country = latencies.get(proxy, {}).get("country", "Unknown")
    city = latencies.get(proxy, {}).get("city", "Unknown")
    isp = latencies.get(proxy, {}).get("isp", "Unknown")
    anonymity = latencies.get(proxy, {}).get("anonymity", "Unknown")

    # Add a row of proxy details to the table
    table.add_row([
        colored(proxy, "cyan"),
        colored(f"{latency:.2f}", latency_color),
        colored(country, "magenta"),
        colored(city, "blue"),
        colored(isp, "yellow"),
        colored(anonymity, "green")
    ])
# categorize proxies based on their latency
low_latency_proxies = [proxy for proxy in working_proxies if latencies.get(proxy, {}).get("latency", float("inf")) < 100]
medium_latency_proxies = [proxy for proxy in working_proxies if 100 <= latencies.get(proxy, {}).get("latency", float("inf")) <= 300]
high_latency_proxies = [proxy for proxy in working_proxies if latencies.get(proxy, {}).get("latency", float("inf")) > 300]

# select proxies
selected_proxies = low_latency_proxies + medium_latency_proxies + high_latency_proxies

# Output file for saving proxies
out_file = f'selected_{proxy_type_to_check}.txt'

# Open the file for writing
with open(out_file, 'w') as f:
    for proxy in selected_proxies:
        f.write(proxy + '\n')
    # Log the number of saved proxies
    logging.info(f"Saved {len(selected_proxies)} selected {proxy_type_to_check} proxies to {out_file}")
    # Print the table
    print(table)