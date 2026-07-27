# Shopify Swatch Update

This repository gives you a **GitHub Actions button** to link Matrixify-imported Color option values to Shopify Color & pattern metaobjects. Its normal use is browser-based: paste a Matrixify download link, run a dry run, review the downloadable report, and then run an explicitly confirmed live update.

For example, it keeps the visible variant label `Ivy Green / Vintage Ripstop` while explicitly connecting that existing value to the `shopify--color-pattern` entry with handle `ivy-green-vintage-ripstop`.

> **Before the first real run, make this repository private.** A Matrixify external-download link can expose a workbook, and GitHub workflow logs and artifacts are accessible to people with repository read access. [1] [2]

## Normal operation

| Step | What you do |
|---|---|
| 1 | Complete the Matrixify job and copy its direct **Download Exported File** link. |
| 2 | In GitHub, open **Actions → Run Shopify Swatch Linker → Run workflow**. |
| 3 | Paste the link, select `dry-run`, and run the workflow. |
| 4 | Download the `swatch-linker-report` artifact and resolve any `ERROR` or `SKIPPED` rows. |
| 5 | Run it again with `execute` and type `APPLY_COLOR_PATTERN_LINKS` only after the dry run is clean. |

The complete one-time setup and the exact button clicks are in **[docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)**. Before the button appears, complete the one-time workflow-file addition described there.

## What the workflow does

The workflow downloads the Matrixify `.xlsx` file from the direct link, generates a manifest for Color option values that contain `/`, resolves each expected `shopify--color-pattern` metaobject by its handle, and updates only the existing matching option values. It never changes customer-facing option labels, product titles, SKUs, or ordinary variant metafields.

| Run mode | Shopify changes | Safety behavior |
|---|---:|---|
| `dry-run` | No | Validates products, option values, and target metaobjects; provides a report artifact. |
| `execute` | Yes | Requires the exact `APPLY_COLOR_PATTERN_LINKS` confirmation text and stops a product’s Color update if any linked value fails validation. |

The workflow publishes its manifest and result CSV as a GitHub Actions artifact so you can download it from the run summary. GitHub documents workflow artifacts as the standard way to retain generated output from a workflow run. [3]

## Required one-time configuration

The GitHub workflow needs three repository secrets and a Shopify Dev Dashboard app installed on the target store.

| GitHub repository secret | Value |
|---|---|
| `SHOPIFY_SHOP_DOMAIN` | Your permanent `your-store.myshopify.com` domain. |
| `SHOPIFY_CLIENT_ID` | Shopify Dev Dashboard app Client ID. |
| `SHOPIFY_CLIENT_SECRET` | Shopify Dev Dashboard app Client secret. |

The custom app needs `read_products`, `write_products`, and `read_metaobjects`. Configure secrets under **Settings → Secrets and variables → Actions**; do not put them in the workflow form or commit them to the repository. [4] [5]

## Important compatibility note

Shopify currently marks the linked-product-option input used by this workflow as **early access**. Use the first live execution on a non-critical or duplicate product, review its report, and only then run a larger batch. [6]

## Development files

The underlying Python package is retained for testing and future maintenance, but you do not need to run Python locally during normal operation. The only manual GitHub file addition is the one-time copy of [`docs/run-swatch-linker.yml`](docs/run-swatch-linker.yml) into `.github/workflows/run-swatch-linker.yml`.

| Path | Purpose |
|---|---|
| `docs/run-swatch-linker.yml` | The ready-to-copy template for the manual **Run workflow** button. |
| `src/swatch_update/github_action.py` | Downloads the Matrixify workbook, builds the manifest, and runs the safe linker. |
| `docs/GITHUB_ACTIONS_SETUP.md` | One-time setup and exact runbook. |
| `docs/SHOPIFY_CUSTOM_APP_SETUP.md` | Shopify Dev Dashboard setup details. |

## References

[1]: https://docs.github.com/actions/managing-workflow-runs/using-workflow-run-logs "GitHub Docs — Using workflow run logs"
[2]: https://matrixify.app/tutorials/export-to-custom-file-name/ "Matrixify — Export to custom file name – predictable URL"
[3]: https://docs.github.com/en/actions/tutorials/store-and-share-data "GitHub Docs — Store and share data with workflow artifacts"
[4]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "GitHub Docs — Using secrets in GitHub Actions"
[5]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[6]: https://shopify.dev/docs/api/admin-graphql/latest/input-objects/LinkedMetafieldUpdateInput "Shopify Developer — LinkedMetafieldUpdateInput"
