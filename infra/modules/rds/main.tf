module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.0.0"

  identifier = "autoapply-db"

  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "autoapply_db"
  username = "dbadmin"
  port     = 5432

  iam_database_authentication_enabled = true

  vpc_security_group_ids = [var.security_group_id]
  subnet_ids             = var.private_subnets

  family = "postgres15"

  major_engine_version = "15"

  deletion_protection = false

  tags = var.tags
}
