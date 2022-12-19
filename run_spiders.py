import subprocess
import argparse
import json
import re
import time
import logging
from .weeklies_scraper import settings

# Set up the logger
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
            # Get information about instance groups
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


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=False,
                        help="The ID of the Google Cloud Platform project")
    parser.add_argument("--instance-group", required=False,
                        help="The name of the instance group to manage")
    parser.add_argument("--zone", required=False,
                        help="The zone of the instance group")
    parser.add_argument("--size", required=False, type=int,
                        help="The new size of the instance group")
    args = parser.parse_args()

    # Load proxy servers configuration from a JSON file
    with open(settings['GCLOUD_CONFIG_FILE'], "r") as f:
        config = json.load(f)

    # Start GCP proxy servers
    for project in config["projects"]:
        # Create a GCloudManager instance
        manager = GCloudManager(project_id=project["project_id"],
                                instance_group_name=project["instance_group"],
                                zone=project["zone"])

        # Start GCP proxy servers
        manager.resize(size=8)

        # List the proxy instances
        proxies = manager.listproxy()

        # Get the file name, open port and credentials for proxy servers
        proxy_file = settings['PROXY_SERVERS_FILE']
        proxy_port = settings['PROXY_PORT']
        proxy_login = settings['PROXY_LOGIN']
        proxy_password = settings['PROXY_PASSWORD']

        # Append proxy list to the text file
        with open(proxy_file, 'a') as f:
            # Convert the list of strings to a list of bytes objects
            lines = [
                f'{line}:{proxy_port}:{proxy_login}:{proxy_password}\n' for line in proxies.split('\n')]
            # Write the lines to the file
            f.writelines(lines)

        # Stop GCP proxy servers
        manager.resize(size=0)
        logging.info('Proxy servers stopped.')


if __name__ == "__main__":
    main()
