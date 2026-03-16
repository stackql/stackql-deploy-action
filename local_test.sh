#!/bin/bash
# local_test.sh - Run the same stackql-deploy steps as the GitHub Actions workflow locally.
# Prerequisites:
#   1. Run `source local_test_setup.sh` to download the stackql-deploy binary.
#   2. Ensure AWS credentials are exported (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN).
#   3. Ensure AWS_REGION is exported.
#   4. yq v4 is installed (for the manifest update step).

set -euo pipefail

STACKQL_DEPLOY="./stackql-deploy"
STACK_DIR="examples/aws-ssm-parameter"
STACK_ENV="dev"
LOG_LEVEL="info"
ENV_OPTS="-e AWS_REGION=${AWS_REGION:?AWS_REGION must be set}"

run_step() {
  local step_name="$1"
  local command="$2"
  echo ""
  echo "========================================================================"
  echo " ${step_name}"
  echo "========================================================================"
  echo "executing: ${STACKQL_DEPLOY} ${command} ${STACK_DIR} ${STACK_ENV} --log-level ${LOG_LEVEL} ${ENV_OPTS}"
  ${STACKQL_DEPLOY} ${command} ${STACK_DIR} ${STACK_ENV} --log-level ${LOG_LEVEL} ${ENV_OPTS}
}

# Step 1: Deploy
run_step "Step 1: Deploy SSM Parameter" "build"

# Step 2: Test
run_step "Step 2: Test SSM Parameter" "test"

# Step 3: Update manifest - add an extra tag
echo ""
echo "========================================================================"
echo " Step 3: Update Manifest - Add Tag"
echo "========================================================================"
MANIFEST="${STACK_DIR}/stackql_manifest.yml"
YQ_EXPR='(.resources[] | select(.name == "test_ssm_parameter") | .props[] | select(.name == "tags")).value += [{"Key": "stackql:updated", "Value": "true"}]'
echo "executing: yq -Y \"${YQ_EXPR}\" ${MANIFEST}"
yq -Y "${YQ_EXPR}" "${MANIFEST}" > "${MANIFEST}.tmp" && mv "${MANIFEST}.tmp" "${MANIFEST}"
echo ""
echo "Updated manifest:"
cat "${STACK_DIR}/stackql_manifest.yml"

# Step 4: Redeploy with updated manifest
run_step "Step 4: Redeploy SSM Parameter with Updated Tag" "build"

# Step 5: Test again after update
run_step "Step 5: Test SSM Parameter (Post-Update)" "test"

# Step 6: Teardown (always run)
teardown() {
  run_step "Step 6: Teardown SSM Parameter" "teardown"
}
trap teardown EXIT

echo ""
echo "All steps completed successfully. Teardown will run on exit."
