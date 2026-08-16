resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    local.common_tags,
    {
      Name = "vpc-${local.name_prefix}"
    }
  )
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    local.common_tags,
    {
      Name = "igw-${local.name_prefix}"
    }
  )
}

resource "aws_subnet" "public_a" {
  vpc_id = aws_vpc.this.id

  cidr_block = cidrsubnet(
    var.vpc_cidr,
    8,
    1
  )

  availability_zone = data.aws_availability_zones.available.names[0]

  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    {
      Name                     = "snet-${local.name_prefix}-public-a"
      "kubernetes.io/role/elb" = "1"
    }
  )
}

resource "aws_subnet" "public_b" {
  vpc_id = aws_vpc.this.id

  cidr_block = cidrsubnet(
    var.vpc_cidr,
    8,
    2
  )

  availability_zone = data.aws_availability_zones.available.names[1]

  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    {
      Name                     = "snet-${local.name_prefix}-public-b"
      "kubernetes.io/role/elb" = "1"
    }
  )
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(
    local.common_tags,
    {
      Name = "rt-${local.name_prefix}-public"
    }
  )
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}