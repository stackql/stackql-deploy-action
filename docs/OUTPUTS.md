# StackQL Deploy Action Outputs

This document describes the output functionality added to the `stackql-deploy-action`.

## Overview

The `stackql-deploy-action` now supports capturing deployment outputs through the `--output-file` argument of `stackql-deploy`. When an output file is specified, the action will:

1. Pass the `--output-file` argument to the `stackql-deploy` command
2. Read the JSON output file after successful execution
3. Make the outputs available as GitHub Action outputs
4. Automatically add the outputs to the GitHub Step Summary

## Input Parameter

### `output_file` (optional)
- **Description**: Output file to capture deployment outputs (JSON format)
- **Type**: string
- **Required**: false
- **Example**: `deployment-outputs.json`

## Action Outputs

### `deployment_outputs`
- **Description**: JSON string containing all deployment outputs from stackql-deploy
- **Type**: string
- **Format**: JSON string
- **Example**: `{"databricks_workspace_name": "stackql-serverless-prd-workspace", "databricks_workspace_id": "4014389171618363"}`

### `deployment_outputs_file`
- **Description**: Path to the deployment outputs file
- **Type**: string
- **Example**: `deployment-outputs.json`

## Example Output Format

The output file contains a JSON object with keys that may vary depending on your deployment:

```json
{
  "databricks_workspace_name": "stackql-serverless-prd-workspace",
  "databricks_workspace_id": "4014389171618363",
  "databricks_deployment_name": "dbc-5a3a87f7-6914",
  "databricks_workspace_status": "RUNNING"
}
```

## Usage Examples

### Basic Usage with Outputs

```yaml
- name: Deploy Stack
  id: deploy
  uses: stackql/stackql-deploy-action@main
  with:
    command: 'build'
    stack_dir: './my-stack'
    stack_env: 'prod'
    output_file: 'outputs.json'

- name: Use outputs
  run: |
    echo "Outputs: ${{ steps.deploy.outputs.deployment_outputs }}"
```

### Parsing Specific Output Values

```yaml
- name: Parse outputs
  run: |
    WORKSPACE_ID=$(echo '${{ steps.deploy.outputs.deployment_outputs }}' | jq -r '.databricks_workspace_id')
    echo "Workspace ID: $WORKSPACE_ID"
```

### Conditional Logic Based on Outputs

```yaml
- name: Check if workspace is running
  if: contains(steps.deploy.outputs.deployment_outputs, 'RUNNING')
  run: echo "Workspace is running!"
```

### Using Outputs in GitHub Step Summary

The action automatically adds a formatted summary to `$GITHUB_STEP_SUMMARY`, but you can also create custom summaries:

```yaml
- name: Custom summary
  run: |
    echo "## Custom Deployment Summary" >> $GITHUB_STEP_SUMMARY
    echo "Workspace: $(echo '${{ steps.deploy.outputs.deployment_outputs }}' | jq -r '.databricks_workspace_name')" >> $GITHUB_STEP_SUMMARY
```

### Sharing Outputs Between Jobs

```yaml
jobs:
  deploy:
    outputs:
      deployment_data: ${{ steps.deploy.outputs.deployment_outputs }}
    steps:
      - name: Deploy
        id: deploy
        uses: stackql/stackql-deploy-action@main
        with:
          output_file: 'outputs.json'
          # ... other parameters

  use-outputs:
    needs: deploy
    steps:
      - name: Use outputs from previous job
        run: |
          echo "Data from deploy job: ${{ needs.deploy.outputs.deployment_data }}"
```

### Complete Workflow Example

The following workflow brings the patterns above together. The `deploy` job deploys a stack, prints the outputs, parses individual values with `jq`, writes a table to the step summary, gates a follow-up step on an output value, and uploads the output file as a workflow artifact. A second `post-deploy` job downloads the artifact and reads the file directly.

The JSON is passed to the shell through a step-level `env` variable rather than interpolated with `${{ }}` inside the script, so quotes in output values do not break the command.

```yaml
name: StackQL Deploy with Outputs

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }} # add additional cloud provider creds here as needed

    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Deploy with StackQL
        id: stackql-deploy
        uses: stackql/stackql-deploy-action@v2
        with:
          command: 'build'
          stack_dir: './my-stack'
          stack_env: 'prod'
          output_file: 'deployment-outputs.json'
          env_vars: |
            PROJECT_ID=${{ secrets.GOOGLE_PROJECT_ID }}
            REGION=us-central1

      - name: Display deployment outputs
        env:
          DEPLOYMENT_OUTPUTS: ${{ steps.stackql-deploy.outputs.deployment_outputs }}
        run: |
          echo "Deployment completed successfully!"
          echo "Raw outputs: $DEPLOYMENT_OUTPUTS"

      - name: Parse specific output values
        env:
          DEPLOYMENT_OUTPUTS: ${{ steps.stackql-deploy.outputs.deployment_outputs }}
        run: |
          WORKSPACE_NAME=$(echo "$DEPLOYMENT_OUTPUTS" | jq -r '.databricks_workspace_name // "N/A"')
          WORKSPACE_ID=$(echo "$DEPLOYMENT_OUTPUTS" | jq -r '.databricks_workspace_id // "N/A"')
          WORKSPACE_STATUS=$(echo "$DEPLOYMENT_OUTPUTS" | jq -r '.databricks_workspace_status // "N/A"')

          echo "Workspace Name: $WORKSPACE_NAME"
          echo "Workspace ID: $WORKSPACE_ID"
          echo "Workspace Status: $WORKSPACE_STATUS"

          # Add to GitHub Step Summary
          echo "## Deployment Results" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Workspace Name | $WORKSPACE_NAME |" >> $GITHUB_STEP_SUMMARY
          echo "| Workspace ID | $WORKSPACE_ID |" >> $GITHUB_STEP_SUMMARY
          echo "| Workspace Status | $WORKSPACE_STATUS |" >> $GITHUB_STEP_SUMMARY

      - name: Use outputs in another step
        if: contains(steps.stackql-deploy.outputs.deployment_outputs, 'RUNNING')
        run: |
          echo "Workspace is running, proceeding with post-deployment tasks..."
          # Add your post-deployment logic here

      - name: Upload deployment outputs as artifact
        uses: actions/upload-artifact@v4
        with:
          name: deployment-outputs
          path: deployment-outputs.json # same value as output_file above
          retention-days: 30

  post-deploy:
    needs: deploy
    runs-on: ubuntu-latest
    if: success()
    steps:
      - name: Download deployment outputs
        uses: actions/download-artifact@v4
        with:
          name: deployment-outputs

      - name: Process outputs in separate job
        run: |
          echo "Processing deployment outputs in a separate job..."
          if [ -f "deployment-outputs.json" ]; then
            cat deployment-outputs.json
            # Process the outputs as needed
          fi
```

Uploading the file as an artifact is an alternative to declaring job outputs (see [Sharing Outputs Between Jobs](#sharing-outputs-between-jobs)). The artifact remains downloadable after the run finishes and is not subject to the size limit on job outputs.

## Features

- **Automatic Summary**: When an output file is specified, the action automatically adds the JSON output to the GitHub Step Summary
- **File Artifact**: The output file path is available for uploading as an artifact or further processing
- **JSON Parsing**: The outputs can be easily parsed using `jq` or other JSON tools in subsequent steps
- **Conditional Logic**: Use `contains()` or other GitHub Actions expressions to create conditional logic based on output values

## Error Handling

- If the `output_file` parameter is specified but the file is not created by `stackql-deploy`, the action will continue without setting the output variables
- The action will only process outputs if the `stackql-deploy` command completes successfully
- Invalid JSON in the output file will not cause the action to fail, but the outputs may not be set correctly