#!/usr/bin/env bash
# deploy-dashboard.sh — Build & deploy the dashboard (frontend + API) to AWS.
#
# Prerequisites:
#   - AWS CLI configured
#   - Docker installed
#   - Node.js 18+ installed
#   - Terraform already applied (S3 bucket, ECR repo, CloudFront exist)
#
# Usage:
#   ./scripts/deploy-dashboard.sh [--api-only | --frontend-only]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-procurement-agent}"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ECR and S3 values (match Terraform outputs)
DASHBOARD_ECR="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-dashboard"
FRONTEND_BUCKET="${PROJECT_NAME}-frontend-${ACCOUNT_ID}"

deploy_api() {
    echo "══════════════════════════════════════════════════════════════"
    echo "  Deploying Dashboard API → Lambda"
    echo "══════════════════════════════════════════════════════════════"

    # 1. Authenticate Docker to ECR
    echo "→ Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" \
        | docker login --username AWS --password-stdin "$DASHBOARD_ECR"

    # 2. Build the image
    echo "→ Building Docker image..."
    cd "$PROJECT_ROOT"
    docker build --platform linux/amd64 -f Dockerfile.dashboard -t "${PROJECT_NAME}-dashboard" .

    # 3. Tag and push
    echo "→ Pushing to ECR..."
    docker tag "${PROJECT_NAME}-dashboard:latest" "${DASHBOARD_ECR}:latest"
    docker push "${DASHBOARD_ECR}:latest"

    # 4. Update Lambda
    echo "→ Updating Lambda function..."
    aws lambda update-function-code \
        --function-name "${PROJECT_NAME}-dashboard" \
        --image-uri "${DASHBOARD_ECR}:latest" \
        --region "$AWS_REGION" > /dev/null

    echo "✓ API deployed"
}

deploy_frontend() {
    echo "══════════════════════════════════════════════════════════════"
    echo "  Deploying Frontend → S3 + CloudFront"
    echo "══════════════════════════════════════════════════════════════"

    # 1. Build React app
    echo "→ Building React app..."
    cd "$PROJECT_ROOT/dashboard/frontend"
    npm ci --silent
    npm run build

    # 2. Sync to S3
    echo "→ Uploading to S3..."
    aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --region "$AWS_REGION"

    # index.html should not be cached long (SPA entry point)
    aws s3 cp dist/index.html "s3://${FRONTEND_BUCKET}/index.html" \
        --cache-control "public, max-age=60" \
        --region "$AWS_REGION"

    # 3. Invalidate CloudFront cache
    echo "→ Invalidating CloudFront cache..."
    DIST_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?contains(Aliases.Items, 'procurement-ai.click')].Id" \
        --output text)

    if [ -n "$DIST_ID" ]; then
        aws cloudfront create-invalidation \
            --distribution-id "$DIST_ID" \
            --paths "/*" > /dev/null
        echo "✓ CloudFront invalidation created"
    else
        echo "⚠ CloudFront distribution not found — skipping invalidation"
    fi

    echo "✓ Frontend deployed to https://procurement-ai.click"
}

# ── Main ──────────────────────────────────────────────────────────────────────

case "${1:-all}" in
    --api-only)     deploy_api ;;
    --frontend-only) deploy_frontend ;;
    all|*)          deploy_api; deploy_frontend ;;
esac

echo ""
echo "Done! Dashboard: https://procurement-ai.click"
echo "        API:     https://api.procurement-ai.click/api/health"
