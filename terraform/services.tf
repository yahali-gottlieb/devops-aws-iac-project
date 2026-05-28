# 1. DB Subnet Group for RDS
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "devops-db-subnet-group"
  subnet_ids = [aws_subnet.private_subnet.id, aws_subnet.private_subnet_2.id]

  tags = {
    Name = "DevOps-DB-Subnet-Group"
  }
}

# 2. RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "14"
  instance_class         = "db.t3.micro"
  db_name                = "appdb"
  username               = "dbadmin"
  password               = "SuperSecretPassword123!" 
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot    = true # Ensures we can easily destroy it later
}

# 3. S3 Bucket
resource "aws_s3_bucket" "app_bucket" {
  bucket = "devops-project-bucket-yahali" 

  tags = {
    Name = "DevOps-App-Bucket"
  }
}

# 4. SNS Topic
resource "aws_sns_topic" "app_alerts" {
  name = "devops-app-alerts"
}

# 5. SNS Email Subscription
resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.app_alerts.arn
  protocol  = "email"
  endpoint  = "yahaligottlieb@gmail.com"
}