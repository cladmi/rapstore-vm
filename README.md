RAPStore Virtual Machine
========================

Deployment for RAPStore using fabric.

## Setup
1. Make a copy of server_config_EXAMPLE.py and rename the copy to server_config.py
2. Replace the placeholder data i.e. like server-IP and the username for SSH with your own data
3. run one or more of the examples below
    - Run **deploy_dev:develop** to deploy development from branch "*develop*"
    - Run **deploy_staging** to deploy staging
    - Run **deploy_prod** to deploy productive
    - A full list of commands is provided by fabric. To see all available commands type **fab -l**
