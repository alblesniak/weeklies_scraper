import subprocess
import argparse
import json
import re
import time
import logging
import os
from scrapy.crawler import CrawlerRunner
from scrapy.spiderloader import SpiderLoader
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
# from twisted.internet import asyncioreactor
# asyncioreactor.install()


# Set up the logger
configure_logging()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class GCloudManager:
    # Initialize the GCloudManager instance with the specified project ID, instance group name, and zone.
    def __init__(self, project_id, instance_group_name, zone):
        self.project_id = project_id
        self.instance_group_name = instance_group_name
        self.zone = zone

        # Set the project using the `gcloud config set` command.
        logging.info(f'Starting GCP project: {self.project_id}')
        command = f"gcloud config set project {self.project_id}  > /dev/null"
        subprocess.run(command, shell=True)

    # Resize the instance group to the specified size using the `gcloud compute instance-groups managed resize` command.
    def resize(self, size):
        logging.info(
            f'Resizing instance group: {self.instance_group_name}, zone: {self.zone}, size: {size}')
        command = f"gcloud compute instance-groups managed resize {self.instance_group_name} --zone {self.zone} --size={size} > /dev/null"
        subprocess.run(command, shell=True)

    # Wait for the virtual machines to be set up by checking the status of the instance group using the `gcloud compute instance-groups managed describe` command.
    def wait_for_vm_setup(self):
        while True:
            # Get the information about instance groups
            command = f"gcloud compute instance-groups managed describe {self.instance_group_name} --zone {self.zone}"
            output = subprocess.run(command, shell=True, capture_output=True)
            # Compile the regular expression to search for the `isStable` field in the output.
            pattern = re.compile(r"isStable:\s+(true)")
            # Search the text for the regular expression
            match = pattern.search(str(output.stdout))
            # Check if a match was found
            if match:
                # Extract the captured group
                status = match.group(1)
                logging.info(f'Proxy servers running up. Status: {status}')
                break
            else:
                logging.info('Waiting for proxy server to run up.')
                time.sleep(2)

    # Get the list of proxy instances using the `gcloud compute instances list` command and return them as a string.
    def listproxy(self):
        # Wait for the virtual machines to be set up
        self.wait_for_vm_setup()

        # Get the list of instances and extract the external IP addresses
        command = "gcloud compute instances list | awk '/RUNNING/ { print $5 }'"
        output = subprocess.run(command, shell=True, capture_output=True)
        proxies = output.stdout.decode().strip()
        logging.info(f'Proxy servers:\n{proxies}')
        return proxies


def parse_args():
    # Create an ArgumentParser object to hold the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--gcloud-config-file", type=str,
                        help="Directory containing the JSON config file for proxy servers", default="gcloud_proxies_config.json")
    parser.add_argument("--spider", nargs="?", type=str,
                        help="The name of the spider to run")
    parser.add_argument("--all", action="store_true",
                        help="Run all available spiders")
    parser.add_argument("--spider-dir", type=str, help="Directory containing the spiders",
                        default=os.path.abspath("./weeklies_scraper/spiders/"))
    args = parser.parse_args()
    return args


def load_and_run_spiders(spiders_names, settings):
    runner = CrawlerRunner(settings)
    loader = SpiderLoader(settings=settings)
    for spider_name in spiders_names:
        spider = loader.load(spider_name)
        runner.crawl(spider)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())
    reactor.run()


def main():
    # Parse the command line arguments
    args = parse_args()
    with open(args.gcloud_config_file, "r") as f:
        config = json.load(f)
        logging.info('GCLOUD configuration for proxy servers loaded.')

    # Start GCP proxy servers
    for project in config["projects"]:
        # Create a GCloudManager instance
        manager = GCloudManager(project_id=project["project_id"],
                                instance_group_name=project["instance_group"],
                                zone=project["zone"])
        # Start and get GCP proxy servers
        manager.resize(size=8)
        proxies = manager.listproxy()
        # Provide data for proxy servers and append them to the text file
        with open(config['proxy_config']['proxy_servers_file'], 'a') as f:
            # lines = [
            # f'''{line}:{config['proxy_config']['proxy_port']}:{config['proxy_config']['proxy_login']}:{config['proxy_config']['proxy_pass']}\n''' for line in proxies.split('\n')]
            lines = [
                f'''{config['proxy_config']['proxy_login']}:{config['proxy_config']['proxy_pass']}@{line}:{config['proxy_config']['proxy_port']}\n''' for line in proxies.split('\n')]
            f.writelines(lines)

    # Get the Scrapy settings
    settings = get_project_settings()

    # If the --all argument is specified, get a list of all available spiders in the specified directory
    if args.all:
        spiders_names = [spider.rstrip('.py') for spider in os.listdir(
            args.spider_dir) if spider.endswith(".py") and not spider.startswith("__")]
    # If the spider name is specified include the only one in the list
    elif args.spider:
        spiders_names = [args.spider]
    # If no spider is specified, raise an error
    else:
        raise ValueError(
            "You must specify a spider to run or use the --all argument to run all available spiders")

    load_and_run_spiders(spiders_names=spiders_names, settings=settings)

    # Stop GCP proxy servers
    for project in config["projects"]:
        # Create a GCloudManager instance
        manager = GCloudManager(project_id=project["project_id"],
                                instance_group_name=project["instance_group"],
                                zone=project["zone"])
        # Start and get GCP proxy servers
        manager.resize(size=0)
    logging.info('Proxy servers stopped.')

    # Remove file with proxy servers
    os.remove(config['proxy_config']['proxy_servers_file'])


if __name__ == "__main__":
    main()
