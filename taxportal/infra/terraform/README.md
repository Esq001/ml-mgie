# TaxPortal1040 Terraform

Baseline AWS infrastructure as a starting point. This is **not** a complete
production deployment — see the root `docs/` for the full gap list.

## Layout

```
modules/
  network/   VPC, subnets (public/private/db), NAT, route tables, VPC flow logs
  data/      KMS key, RDS PostgreSQL 16, ElastiCache Redis, S3 bucket (SSE-KMS)
envs/
  staging/     Staging workspace (smaller instance types).
  production/  Production workspace (multi-AZ, larger instances).
```

## What this module intentionally does not yet provision

- ECS Fargate service definitions (api, web, worker containers).
- CloudFront distribution + WAF.
- Route 53 hosted zone and ACM certificates.
- Secrets Manager wiring for DATABASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY.
- OIDC identity provider for GitHub Actions role assumption.

Those belong in follow-up workspaces (`envs/production/app`,
`envs/production/edge`, `envs/production/observability`). The separation keeps
blast radius small and matches the SOC 2 change-management requirement to
scope every Terraform apply to a well-defined boundary.

## Usage

```bash
cd envs/staging
terraform init -backend-config=backend.hcl
terraform plan -var-file=staging.tfvars
```
