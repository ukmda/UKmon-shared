resource "aws_s3_bucket" "ukmonshared" {
  bucket        = var.sharedbucket
  force_destroy = false
  tags = {
    "billingtag" = "ukmon"
  }
}

resource "aws_s3_bucket_policy" "ukmonsharedbp" {
  bucket = aws_s3_bucket.ukmonshared.id
  policy = jsonencode(
    {
      Statement = [
        {
          Action = [
            "s3:ListBucket",
            "s3:Get*",
            "s3:Put*",
            "s3:Delete*"
          ]
          Effect = "Allow"
          Principal = {
            AWS = [
              "arn:aws:iam::317976261112:role/S3FullAccess",
              "arn:aws:iam::317976261112:role/lambda-s3-full-access-role",
              "arn:aws:iam::317976261112:role/ecsTaskExecutionRole",
              "arn:aws:iam::317976261112:user/Mary",
              "arn:aws:iam::317976261112:user/Mark",
              "arn:aws:iam::317976261112:user/s3user",
            ]
          }
          Resource = [
            "arn:aws:s3:::ukmon-shared/*",
            "arn:aws:s3:::ukmon-shared",
          ]
          Sid = "DelegateS3Access"
        },
      ]
      Version = "2012-10-17"
    }
  )
}

resource "aws_s3_bucket_acl" "ukmonsharedacl" {
  bucket = aws_s3_bucket.ukmonshared.id
  access_control_policy {
    owner {
      id = data.aws_canonical_user_id.current.id
    }
    grant {
      grantee {
        id   = data.aws_canonical_user_id.current.id
        type = "CanonicalUser"
      }
      permission = "FULL_CONTROL"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ukmonsharedlcp" {
  bucket = aws_s3_bucket.ukmonshared.id
  rule {
    status = "Enabled"
    id     = "purge old versions"
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
  rule {
    status = "Enabled"
    id     = "Transition to IA"
    filter {
      prefix = "archive/"
    }

    transition {
      days          = 45
      storage_class = "STANDARD_IA"
    }
  }
  rule {
    id     = "purge athena queries"
    status = "Enabled"

    expiration {
      days                         = 2
      expired_object_delete_marker = false
    }

    filter {
      prefix = "tmp/fromglue/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 2
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "ukmonsharedcors" {
  bucket = aws_s3_bucket.ukmonshared.id
  cors_rule {
    allowed_headers = [
      "*",
    ]
    allowed_methods = [
      "HEAD",
      "GET",
      "PUT",
      "POST",
      "DELETE",
    ]
    allowed_origins = [
      "https://markmcintyreastro.co.uk",
    ]
    expose_headers = [
      "ETag",
      "x-amz-meta-custom-header",
    ]
    max_age_seconds = 0
  }
}

resource "aws_s3_bucket_ownership_controls" "ukmonshare_objownrule" {
  bucket = aws_s3_bucket.ukmonshared.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
