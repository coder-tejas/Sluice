# prod environment (scaffold only — no backend or resources configured yet).

terraform {
  required_version = ">= 1.6"
  # backend "s3" {} # Configure remote state when provisioning begins.
}
