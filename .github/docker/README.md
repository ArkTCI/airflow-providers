# Dependencies Docker Image

This Docker image contains all dependencies required for the Filemaker Provider, and is automatically built whenever the requirements files change.

## Image Details

- Registry: `ghcr.io`
- Image Name: `ghcr.io/OWNER/REPO/filemaker-dependencies:latest`
- Tags: 
  - `latest`: Latest successful build
  - `sha-COMMIT_SHA`: Specific commit's dependencies
  - `BRANCH_NAME`: Latest successful build from a branch

## Using in Other Workflows

To use this image in another GitHub workflow, you can reference it directly:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/${{ github.repository }}/filemaker-dependencies:latest  # or use specific commit SHA
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      # Your steps here - all dependencies are already installed!
      - name: Run tests
        run: pytest -v
```

## Benefits

- Faster workflow execution (no need to install dependencies every time)
- Consistent environment across workflows
- Dependencies only rebuilt when requirements change

## Manual Rebuild

The image can be manually rebuilt by triggering the workflow through the GitHub UI or API, even if the requirement files haven't changed. 