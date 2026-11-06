resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.0.0/24"
}

resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ig.id
  }
}

resource "aws_route_table_association" "rt_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.rt.id
}

resource "aws_internet_gateway" "ig" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "db_az_1" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.10.0/24"
  availability_zone = "eu-west-2a"
}

resource "aws_subnet" "db_az_2" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.11.0/24"
  availability_zone = "eu-west-2b"
}

resource "aws_db_subnet_group" "postgres" {
  name = "postgres_server"
  subnet_ids = [aws_subnet.db_az_1.id, aws_subnet.db_az_2.id]
}
