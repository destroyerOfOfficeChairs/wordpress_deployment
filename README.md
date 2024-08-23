# WordPress Deployment with AWS, CloudFormation, and Ansible

## Overview

This project provides a streamlined solution for deploying a WordPress site on
AWS using EC2, CloudFormation, and Ansible. The setup includes Nginx as the
web server, MariaDB as the database, and certbot for HTTPS configuration. By
following the steps below, you'll have a blank WordPress site up and running
with minimal effort.

## Features

- **Automated Deployment:** Leverage AWS CloudFormation and Ansible to automate
  the setup of your WordPress site.
- **Nginx as Web Server:** Efficient and high-performance serving of WordPress
  content.
- **MariaDB as Database:** Reliable database management with MariaDB.
- **HTTPS with Certbot:** Secure your WordPress site with SSL certificates from
  Let's Encrypt.
- **Python Script for Configuration:** Easily generate required configuration
  files with a single command.
- **Teardown Script** Another Python script, but this one does a teardown and
  deletes everything created by this project.

## Prerequisites

Before you begin, ensure you have the following:

- An AWS account with permissions to create EC2 resources
- AWS CLI installed and configured correctly
  - You should be able to enter `aws sts get-caller-identity` in your terminal
    and receive some sensible output.
- Python, boto3, and Ansible installed on your local machine

## Setup and Installation

### 1. Clone the Repository

```
git clone git@github.com:destroyerOfOfficeChairs/wordpress_deployment.git
cd wordpress_deployment
```

### 2. Run the Python Script

Use the provided Python script to generate the external_vars.yaml file, which
contains the necessary configurations for Ansible.

```
python3 deploy.py --region us-east-1 --email example@example.com --domain example.com
```

### 3. Run the first Ansible playbook

Run the first playbook to install Nginx, MariaDB, and WordPress:

```
ansible-playbook wjc_playbook.yaml
```

### 4. DNS

Manually point your DNS to the EC2 instance IP.

### 5. Run the second Ansible playbook

Run the second playbook to configure SSL with certbot and finalize the Nginx setup:

```
ansible-playbook wjc_ssl_playbook.yaml
```

### 4. Access Your WordPress Site

Once the playbooks have successfully run, your WordPress site will be
accessible at your domain!

## Teardown

If you want to delete everything that was created, all you have to do is run:
`python3 reset.py`

## Troubleshooting

- Database Connection Issues: Ensure that the WordPress database user has the
  correct permissions and that the database connection parameters in
  external_vars.yaml are correct.
- SSL Certificate Issues: Verify that your DNS settings are correctly pointing
  to your EC2 instance and that port 80/443 is open in your security group.

## Roadmap

- Add Docker support for an alternative deployment method.
- Implement automated DNS configuration.
- Explore support for additional CMS options beyond WordPress.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request
with your changes. Ensure that Ansible playbooks run idempotently.

## License

This project is licensed under the MIT License. See the LICENSE file for more
details.
