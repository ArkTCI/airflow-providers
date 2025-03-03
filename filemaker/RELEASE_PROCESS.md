# FileMaker Provider Release Process

This document outlines the release process for the FileMaker Provider.

## Local Development Workflow

### Regular Development

1. Make your code changes in the `filemaker` directory
2. Run local linting checks and tests using VS Code tasks
3. Push your changes to the `Dev` branch
4. GitHub Actions will automatically run linting checks

### Local Validation

Before pushing your changes, you can run the same linting checks and tests locally that will be run in the CI pipeline:

1. **Run Linting Checks**:
   - In VS Code, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Tasks: Run Task" and select it
   - Choose `Run Linting Checks`
   - This will run flake8, black, isort, and mypy

2. **Run Tests**:
   - In VS Code, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Tasks: Run Task" and select it
   - Choose `Run Tests`
   - This will run pytest with coverage reporting

### Release Process

When you're ready to create a new release:

1. **Bump Version Locally**:
   - In VS Code, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Tasks: Run Task" and select it
   - Choose one of the following tasks:
     - `Bump Version (patch)` - For bug fixes (1.0.0 → 1.0.1)
     - `Bump Version (minor)` - For new features (1.0.0 → 1.1.0)
     - `Bump Version (major)` - For breaking changes (1.0.0 → 2.0.0)

2. **Update Version Files**:
   - This will update all version references in:
     - `version.py`
     - `setup.py`
     - `provider.yaml`
     - `version.txt`

3. **Create and Push Tag**:
   - This will create a git tag with the new version and push it to GitHub
   - Format: `v1.0.0`

4. **Alternatively, Use the Combined Tasks**:
   - For a one-click solution without validation, use the `Full Release Process` task
   - For a complete solution with validation, use the `Validate and Release` task
   - These will:
     - Run linting checks and tests (Validate and Release only)
     - Bump the patch version
     - Update all version files
     - Create a release branch
     - Create and push a tag

5. **GitHub Actions Workflow**:
   - When the tag is pushed, GitHub Actions will:
     - Run linting checks
     - Run tests
     - Create a PR to merge the changes into `main`
     - Auto-approve and enable auto-merge for the PR

6. **Deployment**:
   - When the PR is merged to `main`, GitHub Actions will:
     - Publish the package to PyPI
     - Build and push a Docker image

## VS Code Tasks

The following VS Code tasks are available:

### Validation Tasks
- `Run Linting Checks` - Run flake8, black, isort, and mypy
- `Run Tests` - Run pytest with coverage reporting

### Version Management Tasks
- `Bump Version (patch)` - Bump patch version (1.0.0 → 1.0.1)
- `Bump Version (minor)` - Bump minor version (1.0.0 → 1.1.0)
- `Bump Version (major)` - Bump major version (1.0.0 → 2.0.0)
- `Update Version Files` - Update version references in all files

### Git Operations Tasks
- `Create Release Branch` - Create and push a release branch
- `Create and Push Tag` - Create and push a git tag with the new version

### Combined Tasks
- `Bump Version and Create Tag` - Combined task for version bump and tag creation
- `Full Release Process` - Complete process including branch creation
- `Validate and Release` - Run validation, bump version, create branch and tag

## Manual Workflow Triggers

You can also manually trigger the workflows from GitHub:

1. **CI/CD Workflow**:
   - Go to Actions → FileMaker Provider CI/CD
   - Click "Run workflow"
   - Choose whether to run tests and create a PR

2. **Deploy Workflow**:
   - Go to Actions → FileMaker Provider Deploy
   - Click "Run workflow"
   - Enter the version to deploy

## GitHub Workflows

The following GitHub workflows are used:

- `filemaker-ci-cd.yml` - Main CI/CD workflow triggered by pushes to `Dev` and tag pushes
- `filemaker-lint.yml` - Linting checks
- `filemaker-test.yml` - Run tests
- `filemaker-create-pr.yml` - Create PR to merge changes into `main`
- `filemaker-deploy.yml` - Deploy the package to PyPI and build Docker image
- `filemaker-build-docker.yml` - Build and push Docker image 