#!/bin/bash
set -e

while [[ -z "$PROJECT_ID" ]]; do
  read -p "Enter your GCP Project ID: " PROJECT_ID
done

while [[ -z "$PROJECT_NUMBER" ]]; do
  read -p "Enter your GCP Project Number: " PROJECT_NUMBER
done

while [[ -z "$GOOGLE_REGION" ]]; do
  DEFAULT_GOOGLE_REGION="europe-west4"
  read -p "Enter your prefered google region [$DEFAULT_GOOGLE_REGION]: " GOOGLE_REGION
  GOOGLE_REGION=${GOOGLE_REGION:-$DEFAULT_GOOGLE_REGION}
done

while [[ -z "$REPO_NAME" ]]; do
  DEFAULT_REPO_NAME=$PROJECT_ID
  read -p "Enter your GitHub repository name [$DEFAULT_REPO_NAME]: " REPO_NAME
  REPO_NAME=${REPO_NAME:-$DEFAULT_REPO_NAME}
done

while [[ -z "$REPO_OWNER" ]]; do
  DEFAULT_REPO_OWNER="ChrisW-priv"
  read -p "Enter GitHub repository owner [$DEFAULT_REPO_OWNER]: " REPO_OWNER
  REPO_OWNER=${REPO_OWNER:-$DEFAULT_REPO_OWNER}
done

while [[ -z "$BUCKET_NAME" ]]; do
  DEFAULT_BUCKET_NAME="tf-state-$PROJECT_ID"
  read -p "Enter the GCS bucket name for Terraform state [$DEFAULT_BUCKET_NAME]: " BUCKET_NAME
  BUCKET_NAME=${BUCKET_NAME:-$DEFAULT_BUCKET_NAME}
done

while [[ -z "$POOL_NAME" ]]; do
  DEFAULT_POOL_NAME="github"
  read -p "Enter the Workload Identity Pool name [$DEFAULT_POOL_NAME]: " POOL_NAME
  POOL_NAME=${POOL_NAME:-$DEFAULT_POOL_NAME}
done

while [[ -z "$PROVIDER_NAME" ]]; do
  DEFAULT_PROVIDER_NAME="github-actions"
  read -p "Enter the Workload Identity Provider name [$DEFAULT_PROVIDER_NAME]: " PROVIDER_NAME
  PROVIDER_NAME=${PROVIDER_NAME:-$DEFAULT_PROVIDER_NAME}
done


# --- DEFINE ROLES TO ASSIGN TO WIF PRINCIPAL ---
WIF_ROLES=(
  "roles/storage.objectAdmin"          # Full access to GCS objects (Terraform state)
  "roles/artifactregistry.admin"
  "roles/run.admin"
  "roles/compute.networkAdmin"
  "roles/editor"
  "roles/pubsub.admin"
  "roles/secretmanager.admin"
  "roles/iam.serviceAccountUser"
  "roles/storage.admin"
  "roles/storage.objectViewer"
)

# --- CREATE RESOURCES ---
echo "Creating GCS bucket for Terraform state..."
gcloud storage buckets create gs://$BUCKET_NAME --project=$PROJECT_ID --location=$GOOGLE_REGION --uniform-bucket-level-access

echo "Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

echo "Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub Actions Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == '$REPO_OWNER'"

# --- GRANT ROLES TO WIF PRINCIPAL ---
WIF_PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository_owner/$REPO_OWNER"

echo "Granting permissions to WIF principal..."
for ROLE in "${WIF_ROLES[@]}"; do
  echo "  Granting $ROLE on project $PROJECT_ID"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$WIF_PRINCIPAL" \
    --role="$ROLE"
done

echo "Granting storage.objectAdmin on the state bucket..."
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --member="$WIF_PRINCIPAL" \
  --role="roles/storage.objectAdmin"

# Enable the services required for Terraform to be able to take over the setup
gcloud services enable \
    serviceusage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project ${PROJECT_ID}

# --- CAPTURE AND PRINT WIF PROVIDER RESOURCE NAME ---
echo ""
echo "Capturing WIF provider resource name..."
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --format="value(name)")
echo "Your WIF provider resource is: $WIF_PROVIDER"

gcloud artifacts repositories create ghcr \
  --project=$PROJECT_ID \
  --repository-format="docker" \
  --location=$GOOGLE_REGION \
  --no-immutable-tags \
  --description="Repository link to the Github Container Repository" \
  --mode="remote-repository" \
  --remote-repo-config-desc="GitHub Container Repository" \
  --remote-docker-repo="https://ghcr.io"

# --- AUTOMATICALLY UPDATE CONFIGURATION FILES ---
echo ""
echo "Updating configuration files..."

# Note: The -i.bak flag creates a backup of the original file.
# The script is assumed to be run from the 'infrastructure' directory.

# Update .github/workflows/terraform.yml
echo "Updating ../.github/workflows/terraform.yml..."
sed -i.bak \
    -e "s|<{PROJECT_ID_TO_CHANGE}>|$PROJECT_ID|g" \
    -e "s|<{WIF_PROVIDER_TO_CHANGE}>|$WIF_PROVIDER|g" \
    ../.github/workflows/terraform.yml

# Update infrastructure/backend.tf
echo "Updating backend.tf..."
sed -i.bak "s|<{BUCKET_NAME_TO_CHANGE}>|$BUCKET_NAME|g" backend.tf

# Update infrastructure/environments/deployed.tfvars
echo "Updating environments/deployed.tfvars..."
sed -i.bak \
    -e "s|<{PROJECT_ID_TO_CHANGE}>|$PROJECT_ID|g" \
    -e "s|<{PROJECT_NUMBER_TO_CHANGE}>|$PROJECT_NUMBER|g" \
    -e "s|<{REPO_OWNER_TO_CHANGE}>|$REPO_OWNER|g" \
    -e "s|<{REPO_NAME_TO_CHANGE}>|$REPO_NAME|g" \
    environments/deployed.tfvars

echo ""
echo "Configuration files updated successfully!"
echo "Backup files with the .bak extension have been created in their respective directories."
