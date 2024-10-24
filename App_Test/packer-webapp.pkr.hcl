packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }
  }
}



variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "source_ami" {
  type    = string
  default = "ami-0866a3c8686eaeeba"
}

variable "aws_access_key" {
  type        = string
  description = "AWS access key"
}

variable "aws_secret_access_key" {
  type        = string
  description = "AWS secret key"
}

variable "ssh_username" {
  type    = string
  default = "ubuntu"
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "ami_name_prefix" {
  type    = string
  default = "network_fall_2024-webapp"
}

variable "DB_NAME" {
  type = string
}

variable "DB_PASSWORD" {
  type = string
}

variable "DB_USER" {
  type = string
}

source "amazon-ebs" "ubuntu-ami" {
  ami_name        = "${var.ami_name_prefix}_${formatdate("YYYY_MM_DD_hh_mm_ss", timestamp())}"
  ami_description = "AMI Network Fall 2024 [Assignment 4]"
  source_ami      = var.source_ami
  instance_type   = var.instance_type
  ssh_username    = var.ssh_username
  region          = var.aws_region

  access_key = var.aws_access_key
  secret_key = var.aws_secret_access_key




}

build {
  name    = "Assignment 4"
  sources = ["source.amazon-ebs.ubuntu-ami"]

  provisioner "file" {
    source      = "./webapp.zip"
    destination = "/tmp/webapp.zip"
  }

  provisioner "shell" {
    environment_vars = [
      "DB_PASSWORD=${var.DB_PASSWORD}",
      "DB_USER=${var.DB_USER}",
      "DB_NAME=${var.DB_NAME}"
    ]
    inline = [
      "set -ex",                       # Enable debugging and exit on error
      "sudo apt-get update -y",        # Update package list
      "sudo apt-get install unzip -y", # Install unzip utility
      "echo 'Starting provisioning script'",
      "echo 'Creating group csye6225'",
      "sudo groupadd csye6225 || echo 'Group already exists'",
      "echo 'Creating user csye6225'",
      "sudo useradd -s /bin/false -g csye6225 -d /opt/csye6225 -m csye6225 || echo 'User already exists'",
      "echo 'Creating directory /opt/csye6225'",
      "sudo mkdir -p /opt/csye6225",
      "echo 'Setting ownership of /opt/csye6225'",
      "sudo chown csye6225:csye6225 /opt/csye6225",
      "echo 'Checking for webapp.zip'",
      "if [ -f /tmp/webapp.zip ]; then",
      "  echo 'Moving webapp.zip to /opt/csye6225/'",
      "  sudo mv /tmp/webapp.zip /opt/csye6225/",
      "else",
      "  echo 'Error: /tmp/webapp.zip not found'",
      "  ls -l /tmp/",
      "  exit 1",
      "fi",
      "echo 'Changing to /opt/csye6225 directory'",
      "sudo chown csye6225:csye6225 /opt/csye6225",
      "sudo chown -R csye6225:csye6225 /opt/csye6225",
      "pwd",
      "sudo chmod 755 /opt/csye6225",
      "cd /opt/csye6225",
      "echo 'Current directory:'",
      "pwd",
      "echo 'Directory contents:'",
      "ls -al",
      "echo 'Unzipping webapp.zip'",
      "sudo unzip -v webapp.zip",
      "ls",
      "pwd",
      "echo ' Current directory owner: $(ls -ld . | awk '{print $3}')'",
      "sudo chmod 755 /opt/csye6225",
      "sudo chown $(whoami):$(whoami) /opt/csye6225",
      "sudo apt install unzip git python3 -y",
      #Unzipping
      "sudo unzip webapp.zip",
      "ls",

      #Postgres code
      "sudo apt-get install -y postgresql postgresql-contrib",
      "echo 'Starting PostgreSQL service'",
      "sudo service postgresql start",
      "echo 'Waiting for PostgreSQL to start'",
      "timeout 5 bash -c 'until sudo -u postgres psql -c \"\\l\" &>/dev/null; do sleep 1; done'",
      "echo 'Creating PostgreSQL user and database'",
      "echo \"ALTER USER postgres WITH ENCRYPTED PASSWORD '${var.DB_PASSWORD}';\" | sudo -u postgres psql", # Set the password from the environment variable
      "sudo -u postgres psql -c \"CREATE DATABASE ${var.DB_NAME};\"",                                       # Create database using environment variable
      "sudo -u postgres psql -c \"CREATE DATABASE test_database_name;\"",                                   # Replace with your actual test database name
      "echo 'List of PostgreSQL databases:'",
      "sudo -u postgres psql -l",


      "sudo apt install -y python3-venv python3-pip ",
      "echo 'DIRECTORY AFTER UNZIPPING EVERYTHINGGGGGGGGGGGG'",
      "sudo ls",
      "sudo pwd",
      "sudo chown -R csye6225:csye6225 /opt/csye6225/App_Test",
      "sudo chmod 755 /opt/csye6225/App_Test",
      # Switch to csye6225 user and create the virtual environment
      "echo 'Creating virtual environment as csye6225 user'",
      "sudo -u csye6225 python3 -m venv /opt/csye6225/App_Test/myenv",

      # Activate the virtual environment and install requirements
      "echo 'Activating virtual environment and installing requirements'",
      "sudo -u csye6225 bash -c 'source /opt/csye6225/App_Test/myenv/bin/activate && /opt/csye6225/App_Test/myenv/bin/pip install -r /opt/csye6225/App_Test/requirements.txt'",
      "sudo mv /opt/csye6225/.env /opt/csye6225/App_Test/",
      # Install psycopg2
      "echo 'installing libpq'",
      "sudo apt install -y libpq-dev",
      "echo 'Setting ownership of /opt/csye6225 contents'",
      "sudo chown -R csye6225:csye6225 /opt/csye6225",
      "echo 'Removing git'",
      "sudo apt remove git -y",
      "echo 'Final directory contents:'",
      "ls -al",
      "sudo mv /opt/csye6225/App_Test/my_fastapi_app.service /etc/systemd/system/",
      "sudo systemctl daemon-reload",
      "sudo systemctl enable my_fastapi_app",
      "sudo systemctl start my_fastapi_app",
      "echo 'Provisioning script completed'"
    ]
  }
  post-processor "amazon-ami-sharing" {
  ami_users = ["686255977156", "650251683434"]
}

}
