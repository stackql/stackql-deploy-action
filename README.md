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
        uses: stackql/setup-deploy@v1.0.1
        with:
          command: 'build'
          stack-dir: 'examples/k8s-the-hard-way'
          stack-env: 'dev'
          env-vars: 'GOOGLE_PROJECT=stackql-k8s-the-hard-way-demo'
```

this example shows how to test stack for a given environment:

```yaml
...
      - name: Test a Stack
        uses: stackql/setup-deploy@v1.0.1
        with:
          command: 'test'
          stack-dir: 'examples/k8s-the-hard-way'
          stack-env: 'sit'
          env-vars: 'GOOGLE_PROJECT=stackql-k8s-the-hard-way-demo'
```
