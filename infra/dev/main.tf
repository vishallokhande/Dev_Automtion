module "vpc" {
  source = "../modules/vpc"
  
  vpc_name = "autoapply-dev-vpc"
  vpc_cidr = "10.0.0.0/16"
  environment = "dev"
}

module "eks" {
  source = "../modules/eks"
  
  cluster_name = "autoapply-dev-cluster"
  vpc_id = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets
}

module "db" {
  source = "../modules/rds"
  
  security_group_id = module.eks.cluster_security_group_id
  private_subnets = module.vpc.private_subnets
  environment = "dev"
}

module "s3" {
  source = "../modules/s3"
  environment = "dev"
}
