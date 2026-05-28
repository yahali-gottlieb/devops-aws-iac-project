# 1. Security Group for Frontend (Nginx) - Public Facing
resource "aws_security_group" "frontend_sg" {
  name        = "frontend-sg"
  description = "Allow HTTP, HTTPS and SSH from anywhere"
  vpc_id      = aws_vpc.main_vpc.id

  # HTTP for web traffic
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS for secure web traffic
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH for Ansible configuration from your Mac. 
  # Note for README: In production, we would limit this to a specific VPN or IP.
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "DevOps-Frontend-SG"
  }
}

# 2. Security Group for Backend & Worker - Internal Only
resource "aws_security_group" "backend_sg" {
  name        = "backend-sg"
  description = "Allow traffic only from within the VPC"
  vpc_id      = aws_vpc.main_vpc.id

  # Allow all internal communication within the VPC (for SSH via Bastion & App Ports)
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "DevOps-Backend-SG"
  }
}

# 3. Security Group for RDS PostgreSQL
resource "aws_security_group" "rds_sg" {
  name        = "rds-sg"
  description = "Allow PostgreSQL access strictly from app servers"
  vpc_id      = aws_vpc.main_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    # Only allow access from resources attached to these Security Groups
    security_groups = [aws_security_group.backend_sg.id, aws_security_group.frontend_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "DevOps-RDS-SG"
  }
}