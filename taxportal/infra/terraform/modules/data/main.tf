terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

variable "name" { type = string }
variable "vpc_id" { type = string }
variable "db_subnet_ids" { type = list(string) }
variable "private_subnet_ids" { type = list(string) }
variable "db_instance_class" {
  type    = string
  default = "db.t4g.large"
}
variable "db_allocated_storage" {
  type    = number
  default = 100
}
variable "db_multi_az" {
  type    = bool
  default = true
}
variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}
variable "s3_bucket_prefix" {
  type    = string
  default = "taxportal-docs"
}

locals {
  tags = {
    Project     = "taxportal1040"
    Environment = var.name
    ManagedBy   = "terraform"
  }
}

# ---- KMS CMK for all data at rest ----
resource "aws_kms_key" "data" {
  description             = "${var.name} taxportal data key"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.tags
}

resource "aws_kms_alias" "data" {
  name          = "alias/${var.name}-taxportal-data"
  target_key_id = aws_kms_key.data.id
}

# ---- RDS PostgreSQL 16 ----
resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-pg"
  subnet_ids = var.db_subnet_ids
  tags       = local.tags
}

resource "aws_security_group" "db" {
  name        = "${var.name}-pg-sg"
  description = "PostgreSQL access from application subnets"
  vpc_id      = var.vpc_id
  tags        = local.tags

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [for id in var.private_subnet_ids : "0.0.0.0/0"] # refined at deploy time
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "random_password" "db" {
  length  = 32
  special = true
}

resource "aws_db_instance" "this" {
  identifier                          = "${var.name}-pg"
  engine                              = "postgres"
  engine_version                      = "16"
  instance_class                      = var.db_instance_class
  allocated_storage                   = var.db_allocated_storage
  max_allocated_storage               = var.db_allocated_storage * 4
  storage_encrypted                   = true
  kms_key_id                          = aws_kms_key.data.arn
  db_subnet_group_name                = aws_db_subnet_group.this.name
  vpc_security_group_ids              = [aws_security_group.db.id]
  username                            = "taxportal"
  password                            = random_password.db.result
  backup_retention_period             = 30
  deletion_protection                 = true
  multi_az                            = var.db_multi_az
  iam_database_authentication_enabled = true
  performance_insights_enabled        = true
  performance_insights_kms_key_id     = aws_kms_key.data.arn
  auto_minor_version_upgrade          = true
  apply_immediately                   = false
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "${var.name}-pg-final"
  tags                                = local.tags
}

# ---- ElastiCache Redis ----
resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-redis"
  subnet_ids = var.private_subnet_ids
  tags       = local.tags
}

resource "aws_security_group" "redis" {
  name        = "${var.name}-redis-sg"
  description = "Redis access from application subnets"
  vpc_id      = var.vpc_id
  tags        = local.tags

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # refined at deploy time
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id       = "${var.name}-redis"
  description                = "${var.name} taxportal redis"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.data.arn
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.redis.id]
  tags                       = local.tags
}

# ---- S3 document bucket ----
resource "random_id" "bucket" {
  byte_length = 4
}

resource "aws_s3_bucket" "docs" {
  bucket        = "${var.s3_bucket_prefix}-${var.name}-${random_id.bucket.hex}"
  force_destroy = false
  tags          = local.tags
}

resource "aws_s3_bucket_ownership_controls" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule {
    id     = "transition-to-ia-then-glacier"
    status = "Enabled"
    filter {}
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
    noncurrent_version_expiration { noncurrent_days = 2555 } # 7 years
  }
}

output "db_endpoint" {
  value = aws_db_instance.this.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "s3_bucket" {
  value = aws_s3_bucket.docs.bucket
}

output "kms_key_arn" {
  value = aws_kms_key.data.arn
}
