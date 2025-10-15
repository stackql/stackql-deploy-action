[![StackQL Deploy Actions Test](https://github.com/stackql/stackql-deploy-action/actions/workflows/stackql-deploy-actions-test.yml/badge.svg)](https://github.com/stackql/stackql-deploy-action/actions/workflows/stackql-deploy-actions-test.yml)
[![StackQL](https://stackql.io/img/stackql-logo-bold.png)](https://github.com/stackql/stackql)

# stackql-deploy
Github Action to execute `stackql-deploy` to deploy or test a stack.  [`stackql-deploy`](https://github.com/stackql/stackql-deploy) is a declarative, state-file-less IaC framework, based upon [`stackql`](https://github.com/stackql/stackql) queries.

# Usage

## Provider Authentication
Authentication to StackQL providers is done via environment variables source from GitHub Actions Secrets.  To learn more about authentication, see the setup instructions for your provider or providers at the [StackQL Provider Registry Docs](https://stackql.io/registry).  

## Inputs
- **`command`** - stackql-deploy command to run (__`build`__ or __`test`__)
- **`stack_dir`** - repo directory containing `stackql_manifest.yml` and `resources` dir
- **`stack_env`** - environment to deploy or test (e.g., `dev`, `prod`)
- **`env_vars`** - (optional) environment variables or secrets imported into a stack (format: __`KEY=value,KEY2=value2`__)
- **`env_file`** - (optional) environment variables sourced from a file 
- **`show_queries`** - (optional) show queries run in the output logs
- **`log_level`** - (optional) set the logging level (__`INFO`__ or __`DEBUG`__, defaults to __`INFO`__)
- **`dry_run`** - (optional) perform a dry run of the operation
- **`custom_registry`** - (optional) custom registry URL to be used for stackql
- **`on_failure`** - (optional) action on failure (*not implemented yet*)
- **`output_file`** - (optional) output file to capture deployment outputs (JSON format)

## Outputs
- **`deployment_outputs`** - JSON string containing all deployment outputs from stackql-deploy
- **`deployment_outputs_file`** - Path to the deployment outputs file

## Examples

### Deploy a stack

this example shows how to build a stack (`examples/k8s-the-hard-way`) for a `dev` environment:

```yaml
...
jobs:
  stackql-actions-test:
    name: StackQL Actions Test
    runs-on: ubuntu-latest
    env:
      GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }} # add additional cloud provider creds here as needed
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy a Stack
        uses: stackql/stackql-deploy-action@v1.0.2
        with:
          command: 'build'
          stack_dir: 'examples/k8s-the-hard-way'
          stack_env: 'dev'
          env_vars: 'GOOGLE_PROJECT=stackql-k8s-the-hard-way-demo'
```

### Deploy a stack with outputs

this example shows how to deploy a stack and capture outputs for use in subsequent steps:

```yaml
...
jobs:
  deploy:
    name: StackQL Deploy with Outputs
    runs-on: ubuntu-latest
    env:
      GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy a Stack
        id: stackql-deploy
        uses: stackql/stackql-deploy-action@v1.0.2
        with:
          command: 'build'
          stack_dir: 'examples/k8s-the-hard-way'
          stack_env: 'prod'
          output_file: 'deployment-outputs.json'
          env_vars: 'GOOGLE_PROJECT=stackql-k8s-the-hard-way-demo'

      - name: Use deployment outputs
        run: |
          echo "Deployment outputs: ${{ steps.stackql-deploy.outputs.deployment_outputs }}"
          
          # Parse specific values from JSON output
          WORKSPACE_NAME=$(echo '${{ steps.stackql-deploy.outputs.deployment_outputs }}' | jq -r '.databricks_workspace_name // "N/A"')
          echo "Workspace Name: $WORKSPACE_NAME"
          
          # Add to GitHub Step Summary
          echo "## Deployment Results" >> $GITHUB_STEP_SUMMARY
          echo "Workspace: $WORKSPACE_NAME" >> $GITHUB_STEP_SUMMARY

      - name: Conditional step based on outputs
        if: contains(steps.stackql-deploy.outputs.deployment_outputs, 'RUNNING')
        run: echo "Workspace is running, proceeding with next steps..."
```

### Test a stack

this example shows how to test stack for a given environment:

```yaml
...
      - name: Test a Stack
        uses: stackql/stackql-deploy-action@v1.0.2
        with:
          command: 'test'
          stack_dir: 'examples/k8s-the-hard-way'
          stack_env: 'sit'
          env_vars: 'GOOGLE_PROJECT=stackql-k8s-the-hard-way-demo'
```
