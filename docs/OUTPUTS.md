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

## Features

- **Automatic Summary**: When an output file is specified, the action automatically adds the JSON output to the GitHub Step Summary
- **File Artifact**: The output file path is available for uploading as an artifact or further processing
- **JSON Parsing**: The outputs can be easily parsed using `jq` or other JSON tools in subsequent steps
- **Conditional Logic**: Use `contains()` or other GitHub Actions expressions to create conditional logic based on output values

## Error Handling

- If the `output_file` parameter is specified but the file is not created by `stackql-deploy`, the action will continue without setting the output variables
- The action will only process outputs if the `stackql-deploy` command completes successfully
- Invalid JSON in the output file will not cause the action to fail, but the outputs may not be set correctly