terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = "taxportal1040"
      Environment = "production"
      ManagedBy   = "terraform"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

module "network" {
  source = "../../modules/network"
  name   = "taxportal-production"
  cidr   = "10.50.0.0/16"
}

module "data" {
  source             = "../../modules/data"
  name               = "taxportal-production"
  vpc_id             = module.network.vpc_id
  db_subnet_ids      = module.network.db_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids
  db_instance_class  = "db.r6g.large"
  db_multi_az        = true
}

output "db_endpoint" { value = module.data.db_endpoint }
output "redis_endpoint" { value = module.data.redis_endpoint }
output "s3_bucket" { value = module.data.s3_bucket }
output "kms_key_arn" { value = module.data.kms_key_arn }
