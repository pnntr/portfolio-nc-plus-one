resource "aws_security_group" "allow_ssh" {
  name = "allow_ssh"
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "allow_ssh"
    Resource = "security_group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_ingress" {
  security_group_id = aws_security_group.allow_ssh.id
  cidr_ipv4         = "${local.my_ip}/32"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_ssh_egress" {
  security_group_id = aws_security_group.allow_ssh.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_security_group" "allow_http" {
  name = "allow_http"
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "allow_http"
    Resource = "security_group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_http_ingress" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "${local.my_ip}/32"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_http_egress" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_security_group" "postgres" {
  name = "postgres_to_ec2"
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "postgres"
    Resource = "security_group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "postgres_to_ec2_ingress" {
  security_group_id = aws_security_group.postgres.id
  referenced_security_group_id = aws_security_group.allow_http.id
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}
