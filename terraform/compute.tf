# 1. Frontend / Nginx Instance
resource "aws_instance" "frontend" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public_subnet.id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.frontend_sg.id]

  tags = {
    Name = "DevOps-Frontend-Nginx"
    Role = "Frontend"
  }
}

# 2. Backend Instance
resource "aws_instance" "backend" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.private_subnet.id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.backend_sg.id]

  tags = {
    Name = "DevOps-Backend"
    Role = "Backend"
  }
}

# 3. Worker / Service Instance
resource "aws_instance" "worker" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.private_subnet.id
  vpc_security_group_ids = [aws_security_group.backend_sg.id]
  key_name               = var.key_name

  iam_instance_profile   = aws_iam_instance_profile.worker_profile.name

  tags = {
    Name = "DevOps-Worker-Server"
  }
}