# AUTOAPPLY-OPS: Distributed Browser Automation Platform

[![GitHub Repo](https://img.shields.io/badge/GitHub-vishallokhande%2FDev__Automtion-blue?logo=github)](https://github.com/vishallokhande/Dev_Automtion)

Enterprise-grade cloud-native project for automating job application workflows using Playwright on AWS EKS.

## Architecture

![Architecture Diagram](https://mermaid.ink/img/pako:eNqVkk9vwjAMxb_KyXM7oR_QAQcO22nHHramXhInbRWpkpSkG1X97kvLGE0D7ZLEj9_zY_t5w0q1wFrh_Gv4xNoK51fWFhB-oW2jLRis0cYuY_CCd9A2S9gJq6F9W4LBUoM1-A5WwRpswA74_gD2YAI2YAs2YAd8fwR7MAIHcAAHcAQncAJncAZX8AN8fwbf4AovcAUXcAlXcAVX8AN8fwPf4AY3cAM38ANu4A7u4A7u4AEdPMADPOABHuEBHvERHuMRnuAZnuEFXuE1XuMNa_gJv-A3_IY_8EfWRPbI3skBOSRH5IgckaNsybH8I2fknJyT83JBLsgFuSQX5YpckytyTW7INbkhN-SG3JBbcksuyW25I3fkntyTe_JAHsgDeSQP5ZE8lmN5IsfylJ_yS37Lb_kjf-SvvJU38lbeyjv5K-_lr_yT__Jf_sv_-f98kC_yRb7Il_wfqf8B)
*(Note: Conceptual diagram, render in Mermaid support viewer)*

### Components
- **FastAPI Control Plane**: REST API for job management.
- **Redis Queue**: Task broker for distributing automation jobs.
- **Playwright Workers**: Scalable worker pods running headless chrome.
- **PostgreSQL**: Persistent storage for job status and results.
- **AWS S3**: Storage for resumes and execution logs.
- **AWS EKS**: Managed Kubernetes cluster for orchestration.

## Local Development Setup

1. **Prerequisites**: Docker, Docker Compose, Python 3.9+
2. **Start Services**:
    ```bash
    docker-compose up --build
    ```
3. **Access API**: `http://localhost:8000/docs`

## Infrastructure (Terraform)

Modular Terraform setup in `infra/`:
- **VPC**: Multi-AZ with Public/Private subnets.
- **EKS**: Managed Node Groups with IRSA enabled.
- **RDS**: Private PostgreSQL instance.
- **S3**: Private bucket with encryption.

**Deploy:**
```bash
cd infra/dev
terraform init
terraform apply
```

## Kubernetes Deployment

Manifests in `k8s/`:
- **Deployments**: API, Worker, Redis
- **Autoscaling**: HPA for Workers based on CPU.
- **Ingress**: ALB Ingress Controller.
- **Security**: NetworkPolicies, Non-root containers.

**Apply:**
```bash
kubectl apply -f k8s/
```

## CI/CD Pipeline

GitHub Actions workflow `.github/workflows/pipeline.yml`:
1. **Test**: Lint, Unit Tests, SonarQube.
2. **Security**: Trivy image scanning.
3. **Build**: Docker build & push to ECR.
4. **Deploy**: Update manifests -> ArgoCD syncs to EKS.

## Security Features

- **RBAC**: Least privilege IAM roles via IRSA.
- **NetworkPolicies**: Default deny, specific allow rules.
- **Secrets**: External Secrets / AWS Secrets Manager (simulated via k8s/secrets.yaml).
- **Scanning**: Container image scanning in CI.
- **Read-Only Root**: Containers configured with read-only filesystems where possible.

## Scaling Strategy

- **Horizontal Pod Autoscaling (HPA)**: Workers scale based on CPU usage.
- **Cluster Autoscaler**: EKS Node Groups scale based on pending pods.
- **Queue-based Scaling (Advanced)**: Can be enabled via KEDA to scale based on Redis list length.

## Cost Estimation (Monthly)

- **EKS Control Plane**: ~$73
- **EC2 Nodes (t3.medium x 2)**: ~$60
- **RDS (db.t3.micro)**: ~$12
- **NAT Gateway**: ~$32
- **Load Balancer**: ~$16
- **Total**: ~$200/month (Optimize by using Spot Instances and removing NAT Gateway in Dev)

## Production Hardening

- Enable WAF on ALB.
- Use Spot Instances for Worker Node Groups.
- Implement Grid-based browser execution (Selenium Grid / Moon) for massive scale.
- Enable CloudTrail and GuardDuty.

---
**AUTOAPPLY-OPS** - *Automating the Future of Work*.
