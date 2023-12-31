# Proxy Scraper, Checker, Latency Checker.

A Python script for collecting proxies from various sources, checks proxies and checks the latency of the proxies, shows them in a table format with proxy information and saves them in there respective text files. 

![Proxy Checker and Latency Analyzer](proxy-checker.png)

## Features

- **Proxy Fetching:** The script can fetch proxies from user-defined sources, making it easy to update and customize the proxy list.

- **Latency Checking:** It tests the latency of proxies by making HTTP requests and categorizes them as Very Low, Low, Medium, or High based on their response times.

- **Anonymity Level Detection:** The script checks the anonymity level of proxies by analyzing HTTP headers.

- **User Agent Rotation:** To mimic real user behavior, the script randomly selects User Agents from a provided list during proxy checking.

- **Logging:** Creates Proxy_Checker.log, customizable, which is placed in the root directory for easy debugging. 

- **Customization:** Users can easily customize the sources of proxy lists, User Agents, and other parameters.

- **Proxy Rotation** 

## Prerequisites

- Python 3.6 or above
- Dependencies: `requests`, `aiohttp`, `tqdm`, `pyfiglet`, `termcolor`, `colorama`, `prettytable`

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Dunamisss/Proxy-Fetcher-Checker-and-Latency-Analyzer.git
    cd proxy-checker
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Execute the script:

    ```bash
    python main.py
    ```

2. Follow the interactive prompts, what type of proxies, How many proxies.

3. Save selected proxies to a file for later use.

## Customization

To customize the script, you can:

- Edit `proxy_urls.txt` to define the sources of proxy lists.
- Modify `user_agents.txt` to add or change User Agents.

## Examples

- Check 100 HTTP proxies and save the results to a file:

    ```bash
    python main.py --proxy-type http --count 100 --output proxies.txt
    ```

- Check 50 SOCKS5 proxies with custom user agents:

    ```bash
    python main.py --proxy-type socks5 --count 50 --user-agents user_agents.txt
    ```

## Contribution

Feel free to contribute, report issues, or suggest improvements! Follow these steps to contribute:

1. Fork the repository.

2. Create a new branch for your feature or bug fix:

    ```bash
    git checkout -b my-feature
    ```

3. Make your changes and commit them:

    ```bash
    git commit -m "Add new feature"
    ```

4. Push your changes to your forked repository:

    ```bash
    git push origin my-feature
    ```

5. Open a pull request on the original repository and provide a detailed description of your changes.

## License

This project is licensed under the [MIT License](LICENSE).
