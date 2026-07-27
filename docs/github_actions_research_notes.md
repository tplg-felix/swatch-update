# GitHub Actions Research Notes

GitHub’s `workflow_dispatch` event creates the **Run workflow** button in the Actions tab. The workflow file must be present on the repository’s default branch, and a person needs write access to run it. The button can present up to 25 typed inputs, but the documented UI accepts workflow inputs rather than acting as a general spreadsheet upload form. [1]

The planned workflow should therefore accept a reviewed, download-ready input URL, then publish the generated result report as a downloadable workflow artifact. The Matrixify spreadsheet should not be committed to this public repository unless it contains no confidential product data.

Matrixify documents that an external service can download an exported file after the store enables **Allow downloading your files by external services** in Matrixify security settings. The link comes from the export job’s **Download Exported File** or copy-link control. Matrixify may redirect the download to temporary S3 storage with HTTP 307, so the workflow downloader must follow redirects. [4]

| Security requirement | Verified implementation direction |
|---|---|
| Shopify credentials | Store them as repository secrets and expose them only as job environment variables. [2] |
| Avoid command-line secrets | Use job environment variables rather than command-line values, because command arguments can be exposed in logs or process listings. [2] |
| Result reports | Upload reports as artifacts with a short retention period so the person who initiated the run can download them from the workflow run. [3] |
| Live mutations | Use a typed choice input for dry run versus execute, and require a second typed confirmation input for execute. |

## References

[1]: https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow "GitHub Docs — Manually running a workflow"
[2]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "GitHub Docs — Using secrets in GitHub Actions"
[3]: https://docs.github.com/en/actions/tutorials/store-and-share-data "GitHub Docs — Store and share data with workflow artifacts"
[4]: https://matrixify.app/tutorials/export-to-custom-file-name/ "Matrixify — Export to custom file name – predictable URL"
