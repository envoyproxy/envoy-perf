# The S3 bucket where Terraform for the Salvo sandbox stores its state.

resource "aws_s3_bucket" "salvo_sandbox_remote_state_bucket" {
  bucket = "salvo-sandbox-tf-remote-state-us-west-1"

  tags = {
    Environment = "Production"
  }
}

resource "aws_s3_bucket_versioning" "salvo_sandbox_remote_state_bucket_versioning" {
  bucket = aws_s3_bucket.salvo_sandbox_remote_state_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "salvo_sandbox_remote_state_bucket_lifecycle" {
  bucket = aws_s3_bucket.salvo_sandbox_remote_state_bucket.id

  rule {
    id     = "keep_100_noncurrent_versions_for_a_year"
    status = "Enabled"
    noncurrent_version_expiration {
      newer_noncurrent_versions = 100
      noncurrent_days           = 365
    }
  }
}

terraform {
  backend "s3" {
    bucket = "salvo-sandbox-tf-remote-state-us-west-1"
    key    = "salvo/infra/terraform.tfstate"
    region = "us-west-1"
  }

  required_version = ">= 1.4"
}
