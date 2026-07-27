# One-Button GitHub Setup

After this one-time setup, the normal process is simply **GitHub → Actions → Run Shopify Swatch Linker**. You paste the Matrixify download link, choose **Dry run** or **Execute**, and download the report from the completed workflow.

> **Make the repository private before adding real Shopify credentials or running a real Matrixify link.** GitHub requires read access to view workflow logs and artifacts, while a Matrixify external-download URL can provide access to an export file. [1] [2]

## 1. Make the repository private

Open the repository on GitHub, select **Settings**, then change repository visibility to **Private**. Do this before entering any Shopify credential or Matrixify download link. [1] [2]

## 2. Add the button workflow file once

GitHub shows the **Run workflow** button only after the workflow file exists on the default branch. The repository connection used to publish this project cannot create files inside GitHub’s special `.github/workflows` folder, so add this one prepared file through the GitHub web editor:

1. Open [`docs/run-swatch-linker.yml`](run-swatch-linker.yml) in this repository and copy its entire contents.
2. In the repository, select **Add file → Create new file**.
3. Enter this exact filename: `.github/workflows/run-swatch-linker.yml`.
4. Paste the copied content, then select **Commit new file** on `main`.

After this one-time step, GitHub recognizes the `workflow_dispatch` trigger and shows **Actions → Run Shopify Swatch Linker → Run workflow**. [3]

## 3. Create the Shopify app once

Create the custom app in the Shopify **Dev Dashboard**, create and release a version, and install it on the target store. For this integration, select these Admin API scopes:

| Scope | Why it is needed |
|---|---|
| `read_products` | Find the imported product, its Color option, and existing option values. |
| `write_products` | Apply a reviewed Color & pattern link to an existing option value. |
| `read_metaobjects` | Resolve the required `shopify--color-pattern` entry by handle. |

The app should use Shopify’s client-credentials authentication for a store in the same Shopify organization. The full Shopify guide is in [SHOPIFY_CUSTOM_APP_SETUP.md](SHOPIFY_CUSTOM_APP_SETUP.md). [4] [5]

## 4. Add three GitHub repository secrets

Open the repository’s **Settings → Secrets and variables → Actions → Secrets**, then select **New repository secret** three times. GitHub encrypts these values and the workflow reads them as environment variables; do not commit them in code or paste them into workflow inputs. [6]

| Secret name | Value |
|---|---|
| `SHOPIFY_SHOP_DOMAIN` | The permanent `your-store.myshopify.com` domain. |
| `SHOPIFY_CLIENT_ID` | The Client ID from Shopify Dev Dashboard → your app → Settings. |
| `SHOPIFY_CLIENT_SECRET` | The Client secret from the same page. |

## 5. Get the Matrixify direct-download link

In Matrixify, enable **Allow downloading your files by external services** under its Security settings. Complete the Matrixify export or import job, then copy the **Download Exported File** link from that job. The workflow follows Matrixify’s temporary redirect to the real Excel file automatically. [2]

## 6. Run the button workflow

Open the repository’s **Actions** tab. Choose **Run Shopify Swatch Linker**, select **Run workflow**, and complete the form.

| Form field | First run | Live run after review |
|---|---|---|
| `matrixify_download_url` | Paste the Matrixify direct-download link. | Paste the same or a new completed-job link. |
| `mode` | Select `dry-run`. | Select `execute`. |
| `live_confirmation` | Leave blank. | Type `APPLY_COLOR_PATTERN_LINKS` exactly. |

GitHub’s `workflow_dispatch` event creates this button and accepts the fields shown above. [3]

## 7. Download and review the report

When the workflow finishes, open its summary page and download the **swatch-linker-report** artifact. The dry-run report lists each candidate result.

| Result | Meaning | What to do |
|---|---|---|
| `WOULD_LINK` | The product, Color option value, and target Color & pattern metaobject all resolved. | Eligible for a live run after your review. |
| `ALREADY_LINKED` | The expected explicit link already exists. | No action needed. |
| `ERROR` | A required product, option value, target metaobject, scope, or configuration item was missing. | Correct the issue, then run another dry run. |
| `SKIPPED` | Another Color value on the same product failed validation, so the tool blocked a partial update. | Fix the paired error before a live run. |

## 8. Execute only after the dry run is clean

Run the same workflow again with `mode` set to `execute` and enter the exact confirmation text. The workflow preserves display labels such as `Ivy Green / Vintage Ripstop`; it links the existing option value to the `shopify--color-pattern` entry identified by `ivy-green-vintage-ripstop`.

Shopify currently labels the linked-product-option input as early access. For the first live run, use one non-critical or duplicate product and inspect the result artifact before applying a full seasonal batch. [7]

## References

[1]: https://docs.github.com/actions/managing-workflow-runs/using-workflow-run-logs "GitHub Docs — Using workflow run logs"
[2]: https://matrixify.app/tutorials/export-to-custom-file-name/ "Matrixify — Export to custom file name – predictable URL"
[3]: https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow "GitHub Docs — Manually running a workflow"
[4]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[5]: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens "Shopify Developer — Get API access tokens for Dev Dashboard apps"
[6]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "GitHub Docs — Using secrets in GitHub Actions"
[7]: https://shopify.dev/docs/api/admin-graphql/latest/input-objects/LinkedMetafieldUpdateInput "Shopify Developer — LinkedMetafieldUpdateInput"
