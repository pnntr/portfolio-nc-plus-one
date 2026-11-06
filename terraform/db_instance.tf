resource "aws_kms_key" "rds_secret" {
  description             = "KMS key for PostgreSQL credentials"
  enable_key_rotation     = false
}

resource "aws_db_instance" "postgres" {
  # DB engine
  engine               = "postgres"
  engine_version       = "14.18"
  instance_class       = "db.t3.micro"

  # DB settings
  db_name              = "toy"
  username             = "toy"
  manage_master_user_password = true

  # Storage settings
  allocated_storage    = 10
  max_allocated_storage = 11
  skip_final_snapshot  = true

  # Networks
  publicly_accessible = false
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]

  # Availability
  multi_az = false

  tags = {
    Name = "postgres-rds"
  }
}

