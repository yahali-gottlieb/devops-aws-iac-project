# 1. IAM Role for EC2
resource "aws_iam_role" "ec2_s3_sns_role" {
  name = "devops-worker-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# 2. IAM Policy (Strict Permissions for S3 PutObject and SNS Publish)
resource "aws_iam_policy" "s3_sns_policy" {
  name        = "devops-s3-sns-policy"
  description = "Allow EC2 to upload to S3 and publish to SNS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::devops-project-bucket-yahali",
          "arn:aws:s3:::devops-project-bucket-yahali/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:ListTopics"
        ]
        Resource = "*"
      }
    ]
  })
}

# 3. Attach Policy to Role
resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.ec2_s3_sns_role.name
  policy_arn = aws_iam_policy.s3_sns_policy.arn
}

# 4. Create Instance Profile (To attach to EC2)
resource "aws_iam_instance_profile" "worker_profile" {
  name = "devops-worker-profile"
  role = aws_iam_role.ec2_s3_sns_role.name
}