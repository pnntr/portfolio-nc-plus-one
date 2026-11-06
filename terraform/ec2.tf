data "aws_ami" "ubuntu" {
  most_recent = true
  # Canonical: <https://repost.aws/questions/QUqu_UF2q8Q8-b0YbjtClmow/linux-kernel-source-used-in-amazon-provided-ubuntu-ami>
  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu*26.04*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_instance" "web_server" {
  ami           = "${data.aws_ami.ubuntu.id}"
  instance_type = "t3.micro"
  key_name = "aws_nc_sprint2"
  associate_public_ip_address = true
  vpc_security_group_ids = [aws_security_group.allow_ssh.id, aws_security_group.allow_http.id]
  subnet_id = aws_subnet.public.id
  iam_instance_profile = aws_iam_instance_profile.instance.name

  user_data_replace_on_change = true
  user_data = <<-EOF
    #!/bin/bash
    cat > /tmp/init-script.sh <<'INIT_SCRIPT'
    ${file("${path.module}/init-script.sh")}
    INIT_SCRIPT
    chmod +x /tmp/init-script.sh
    export SECRET_ARN="${aws_db_instance.postgres.master_user_secret[0].secret_arn}"
    export DB_HOST="${aws_db_instance.postgres.address}"
    bash /tmp/init-script.sh
  EOF

  tags = {
    Name = "main-backend"
  }
}

output "instance_connection" {
  value = "ssh -i '~/.ssh/aws_nc_sprint2.pem' ubuntu@${aws_instance.web_server.public_ip}"
}

output "secret_arn" {
  value = "${aws_db_instance.postgres.master_user_secret[0].secret_arn}"
}
