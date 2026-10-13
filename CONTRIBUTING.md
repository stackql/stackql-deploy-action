# Contributing

Read [README.md](./README.md) for usage and supported platforms. This repository
contains a Bash composite GitHub Action that installs and runs the prebuilt
`stackql-deploy` CLI.

## Repository layout

- [action.yml](./action.yml): inputs, outputs, installation, and command execution.
- [tests/test_install.py](./tests/test_install.py): installer regression tests.
- [.github/workflows](./.github/workflows): installation and AWS integration checks.
- [examples/aws-ssm-parameter](./examples/aws-ssm-parameter): the AWS integration stack.
- [docs/OUTPUTS.md](./docs/OUTPUTS.md): deployment output examples.

## Local setup and tests

Use Python 3.12, matching CI, with virtual environment support. Run the commands
below in Bash on Linux, macOS, or WSL from the repository root. The tests require
`bash`, `tar`, `unzip`, `chmod`, and `file` on the shell's `PATH`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PyYAML==6.0.3
python -m unittest discover -s tests -v
```

The tests execute the installation script from `action.yml` with mocked downloads
and platform detection. They cover architecture selection, existing installations,
unsupported platforms, and failure handling. They need no cloud credentials or
real `stackql-deploy` binary.

## CI checks

[Install Test](./.github/workflows/install-test.yml) runs the Python tests and
checks real binary installation, architecture, and reuse on Linux, macOS, and
Windows for x86_64 and ARM64. It runs on pull requests and pushes to `main`, and
can also be started manually. It needs no cloud credentials.

[AWS SSM integration tests](./.github/workflows/stackql-deploy-actions-test.yml)
deploy, test, update, and tear down an SSM parameter across the same platforms.
They also check multiline `env_vars` on Ubuntu. These tests create real AWS
resources and require:

- Repository secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, plus
  `AWS_SESSION_TOKEN` when using temporary credentials.
- Repository variable `AWS_REGION`.
- AWS permissions to deploy, read, update, and delete the example stack's resources.

GitHub does not pass repository secrets to workflows triggered by
[pull requests from forks](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflows-in-forked-repositories).
These contributions need a maintainer to arrange credentialed integration testing.

## Pull requests

- Create a branch for one coherent change and open the pull request against `main`.
- Explain the problem, the resulting behavior, and which checks you ran.
- Add or update tests for functional changes, including affected platforms.
- Update usage and output documentation when changing action inputs or outputs.
- Keep credentials, virtual environments, downloaded binaries, and generated
  deployment outputs out of commits.

## Issues and security

For bugs, include the action version, runner OS and architecture, a minimal
workflow, and relevant logs with secrets removed. Use the repository's issue
templates for bugs, feature requests, and questions.

Report suspected vulnerabilities privately as described in [SECURITY.md](./SECURITY.md).
