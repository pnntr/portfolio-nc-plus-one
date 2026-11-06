provider "aws" {
  region = "eu-west-2"

  default_tags {
    tags = {
      Project = "nc-plus-one"
      Terraform = true
    }
  }
}

terraform {
  backend "s3" {
    bucket = "nc-general-bucket"
    key    = "nc_plus_one/terraform.tfstate"
    region = "eu-west-2"
  }
}

data "http" "my_public_ip" {
  url = "https://ifconfig.co/json"
  request_headers = {
    Accept = "application/json"
  }
}

# locals {
#   ifconfig_co_json = jsondecode(data.http.my_public_ip.response_body)
# }
#
# output "my_ip_addr" {
#   value = local.ifconfig_co_json.ip
# }
locals {
  my_ip = "149.40.105.34"
}
