#!/bin/bash
set -e

# --- Default values ---
DEFAULT_POOL_NAME="github"
DEFAULT_PROVIDER_NAME="github-actions"
DEFAULT_REPO_OWNER="ChrisW-priv"

# --- Interactive Variable Setup ---
# These variables require your input.
while [[ -z "$PROJECT_ID" ]]; do
  read -p "Enter your GCP Project ID: " PROJECT_ID
done

while [[ -z "$PROJECT_NUMBER" ]]; do
  read -p "Enter your GCP Project Number: " PROJECT_NUMBER
done

read -p "Enter your GitHub repository owner (username or organization): " REPO_OWNER
REPO_OWNER=${REPO_OWNER:-$DEFAULT_REPO_OWNER}

# --- These variables most likely do not need to be edited ---
# You can press Enter to accept the default values.
DEFAULT_BUCKET_NAME="tf-state-$PROJECT_ID"
read -p "Enter the GCS bucket name for Terraform state [$DEFAULT_BUCKET_NAME]: " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-$DEFAULT_BUCKET_NAME}

read -p "Enter the Workload Identity Pool name [$DEFAULT_POOL_NAME]: " POOL_NAME
POOL_NAME=${POOL_NAME:-$DEFAULT_POOL_NAME}

read -p "Enter the Workload Identity Provider name [$DEFAULT_PROVIDER_NAME]: " PROVIDER_NAME
PROVIDER_NAME=${PROVIDER_NAME:-$DEFAULT_PROVIDER_NAME}

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
gcloud storage buckets create gs://$BUCKET_NAME --project=$PROJECT_ID --location=EU --uniform-bucket-level-access

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

# --- PRINT WIF PROVIDER RESOURCE NAME ---
echo ""
echo "Your WIF provider resource is:"
gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --format="value(name)"
