import subprocess
import argparse
import json
import re
import time
import logging
import concurrent.futures
import importlib
import os
import scrapy

from google.auth import compute_engine
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from scrapy.crawler import CrawlerProcess
from scrapy.utils.spider import iter_spider_classes
from scrapy.utils.project import get_project_settings


# Set up the logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class GCloudManager:
    # Initialize the GCloudManager instance with the specified project ID, instance group name, and zone.
    def __init__(self, project_id, instance_group_name, zone):
        '''
        Sets up parameters for the GCloudManager
        Parameters:
        - project_id (str): The ID of the project.
        - instance_group_name (str): The name of the instance group.
        - zone (str): The zone where the instance group is located.
        '''

        self.project_id = project_id
        self.instance_group_name = instance_group_name
        self.zone = zone

    def resize_instance_group(self, target_size):
        """
        Resizes an instance group to the specified size.

        Parameters:
        - size (int): The new size of the instance group.

        Returns:
        - operation (Dict[str, Any]): The operation that resizes the instance group.
        """
        credentials = compute_engine.Credentials(
            quota_project_id=self.project_id)
        # Build the compute service client
        service = build(
            'compute', 'v1', credentials=credentials)
        print(service)
        # Get the instance group resource
        instance_group = service.instanceGroups().get(
            project=self.project_id,
            zone=self.zone,
            instanceGroup=self.instance_group_name
        ).execute()

        # Set the target size of the instance group
        instance_group['targetSize'] = target_size

        # Resize the instance group
        response = service.instanceGroups().resize(
            project=self.project_id,
            zone=self.zone,
            instanceGroup=self.instance_group_name,
            size=target_size
        ).execute()

        return response

    def get_proxies(self):
        # Authenticate and create a service client
        service = build('compute', 'v1', credentials=self.creds)
        # Retrieve the instance group and its instances
        instance_group = service.instanceGroups().get(project=self.project_id, zone=self.zone,
                                                      instanceGroup=self.instance_group_name).execute()
        instances = service.instanceGroups().listInstances(project=self.project_id, zone=self.zone,
                                                           instanceGroup=self.instance_group_name, filter='all').execute()['items']

        # Wait for the instance group to be fully created
        while instance_group['status'] != 'RUNNING':
            logging.info('Waiting for instance group to be created...')
            time.sleep(3)
            instance_group = service.instanceGroups().get(project=self.project_id, zone=self.zone,
                                                          instanceGroup=self.instance_group_name).execute()

        # Retrieve the external IP addresses of the instances
        external_ips = []
        for instance in instances:
            instance_info = service.instances().get(project=self.project_id, zone=self.zone,
                                                    instance=instance['instance']).execute()
            external_ips.append(
                instance_info['networkInterfaces'][0]['accessConfigs'][0]['natIP'])

        return external_ips


def parse_args(settings):
    # Create an ArgumentParser object to hold the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--gcloud-config-file", type=str,
                        help="Directory containing the JSON config file for proxy servers", default=settings['GCLOUD_CONFIG_FILE'])
    parser.add_argument("--gcloud-key", type=str,
                        help="Directory containing JSON file with authentication keys for GCP", default=settings['GCLOUD_KEYS_FILE'])
    parser.add_argument("--project-id", required=False,
                        help="The ID of the Google Cloud Platform project")
    parser.add_argument("--instance-group", required=False,
                        help="The name of the instance group to manage")
    parser.add_argument("--zone", required=False,
                        help="The zone of the instance group")
    parser.add_argument("--size", required=False, type=int,
                        help="The new size of the instance group")
    parser.add_argument("--spider", nargs="?", type=str,
                        help="The name of the spider to run")
    parser.add_argument("--all", action="store_true",
                        help="Run all available spiders")
    parser.add_argument("--spider-dir", type=str, help="Directory containing the spiders",
                        default=os.path.abspath("weeklies_scraper/spiders/"))
    args = parser.parse_args()
    return args


def run_spider(spider):
    # Create a CrawlerProcess instance to run the Scrapy spider
    process = CrawlerProcess(settings={
        'LOG_LEVEL': 'ERROR'
    })
    # Add the spider to the process
    process.crawl(spider)
    # Start the spider
    process.start()


def main():

    # Get the Scrapy settings
    settings = get_project_settings()
    # Parse the command line arguments
    args = parse_args(settings)
    # Check if GCLOUD_CONFIG_FILE is specified in settings.py
    if args.gcloud_config_file is not None:
        # Load proxy servers configuration from a JSON file
        with open(args.gcloud_config_file, "r") as f:
            config = json.load(f)
        logging.info('GCLOUD configuration for proxy servers loaded.')
    else:
        # Check if the arguments for proxy servers are specified in the command line
        if all(args.project_id, args.instance_group, args.zone) is not None:
            config = {
                "projects": [
                    {
                        "project_id": args.project_id,
                        "instance_group": args.instance_group,
                        "zone": args.zone

                    }
                ]
            }
            logging.info('GCLOUD configuration for proxy servers loaded.')
        # If no arguments for proxy servers are specified, raise an error
        else:
            raise ValueError(
                "You must specify either the proxy configuration file or parametrs for it.")

    # Start GCP proxy servers
    for project in config["projects"]:
        # Create a GCloudManager instance
        manager = GCloudManager(project_id=project["project_id"],
                                instance_group_name=project["instance_group"],
                                zone=project["zone"])
        # Start and get GCP proxy servers
        manager.resize_instance_group(target_size=8)
        proxies = manager.listproxy()
        # Provide data for proxy servers and append them to the text file
        with open(settings['PROXY_SERVERS_FILE'], 'a') as f:
            lines = [
                f'''{line}:{settings['PROXY_PORT']}:{settings['PROXY_LOGIN']}:{'PROXY_PASSWORD'}\n''' for line in proxies.split('\n')]
            f.writelines(lines)

    # If the --all argument is specified, get a list of all available spiders in the specified directory
    if args.all:
        # Create an empty list to hold the spiders
        spiders = []
        # Get the directory containing the spiders from the command line arguments
        spider_dir = args.spider_dir
        print(spider_dir)
        # Iterate over all modules in the specified directory
    #     for module_name in os.listdir(spider_dir):
    #         # Ignore modules that don't end with ".py"
    #         if not module_name.endswith(".py"):
    #             continue
    #         # Import the module
    #         module = importlib.import_module(module_name[:-3])
    #         # Iterate over the spider classes in the module
    #         for spider_class in iter_spider_classes(module):
    #             # Add an instance of the spider class to the list
    #             spiders.append(spider_class())
    # # If the spider name is specified, import the module that contains the spider and get the spider class
    # elif args.spider:
    #     spider_module = __import__(args.spider)
    #     spider_class = getattr(spider_module, args.spider)
    #     # Create a list with a single instance of the spider
    #     spiders = [spider_class()]
    # # If no spider is specified, raise an error
    # else:
    #     raise ValueError(
    #         "You must specify a spider to run or use the --all argument to run all available spiders")

    # # Use a concurrent.futures.ProcessPoolExecutor to run the spiders concurrently
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     # Map the run_spider function to the list of spiders
    #     results = [executor.submit(run_spider, spider)
    #                for spider in spiders]
    #     # Wait for all the tasks to complete
    #     concurrent.futures.wait(results)

    # Stop GCP proxy servers
    manager.resize_instance_group(size=0)
    logging.info('Proxy servers stopped.')


if __name__ == "__main__":
    main()
