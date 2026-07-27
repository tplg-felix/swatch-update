# Shopify Custom-App Setup for the GitHub Button

This guide is the one-time Shopify configuration for the **Run Shopify Swatch Linker** workflow. You do not need to install Python or run a terminal command locally.

## 1. Create the app in Shopify Dev Dashboard

Open [Shopify Dev Dashboard](https://dev.shopify.com/dashboard/), select **Apps**, then select **Create app**. Choose **Start from Dev Dashboard**, give it an internal name such as `Swatch Update`, and create the app. Create a version and release it; Shopify requires a released version before the app can be installed on a store. [1]

## 2. Add only the required Admin API scopes

In the app version, add the following scopes. Do not request customer, order, theme, or file access.

| Scope | Purpose |
|---|---|
| `read_products` | Locate the Matrixify-imported product, Color option, and option-value IDs. |
| `write_products` | Apply the reviewed Color & pattern reference to an existing option value. |
| `read_metaobjects` | Look up a `shopify--color-pattern` entry by handle. |

Release the version after adding scopes, then install the app on the target store. [1] [2]

## 3. Copy the app credentials

In Dev Dashboard, open the app’s **Settings** section and copy its **Client ID** and **Client secret**. This integration uses Shopify’s client-credentials grant for a store in the same Shopify organization. The workflow requests its own short-lived access token when it runs; you do not need to copy an Admin API token. [3]

## 4. Place the credentials in GitHub secrets

After making this repository private, open the repository on GitHub and go to **Settings → Secrets and variables → Actions → Secrets**. Create these three repository secrets.

| GitHub secret | Value |
|---|---|
| `SHOPIFY_SHOP_DOMAIN` | The permanent `your-store.myshopify.com` domain. |
| `SHOPIFY_CLIENT_ID` | The Client ID copied from the Dev Dashboard. |
| `SHOPIFY_CLIENT_SECRET` | The Client secret copied from the Dev Dashboard. |

GitHub makes secrets available to the workflow as protected environment values. Do not paste the Client secret into the run form, commit it to the repository, or share it in chat. [4]

## 5. Verify compatibility with one small live test

Shopify currently labels the product-option linked-metafield input as **early access**. Start with a `dry-run`, then run one non-critical or duplicate product in `execute` mode. Review the result artifact before running a seasonal batch. [5]

If the run returns a `shop_not_permitted` authentication error, verify that the app and target store belong to the same Shopify organization in Dev Dashboard. This is a client-credentials requirement. [3]

For the Matrixify download-link and click-to-run instructions, return to [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md).

## References

[1]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[2]: https://shopify.dev/docs/api/usage/access-scopes "Shopify Developer — Shopify API access scopes"
[3]: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens "Shopify Developer — Get API access tokens for Dev Dashboard apps"
[4]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "GitHub Docs — Using secrets in GitHub Actions"
[5]: https://shopify.dev/docs/api/admin-graphql/latest/input-objects/LinkedMetafieldUpdateInput "Shopify Developer — LinkedMetafieldUpdateInput"
