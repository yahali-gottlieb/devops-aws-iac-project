variable "aws_region" {
  description = "The AWS region to deploy our infrastructure"
  type        = string
  default     = "us-east-1" 
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID (Change based on your region)"
  type        = string
  default     = "ami-0c7217cdde317cfec" 
}

variable "key_name" {
  description = "The name of the AWS Key Pair for SSH access"
  type        = string
  default     = "yahali test key"
}