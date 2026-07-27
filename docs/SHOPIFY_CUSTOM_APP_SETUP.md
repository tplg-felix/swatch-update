# Shopify Custom-App Setup

**Purpose.** This guide configures the single-store Shopify app used by `shopify-swatch-linker`. It creates no storefront interface, receives no webhooks, and runs only when you manually start the local command-line tool.

> New custom apps are now created in Shopify’s **Dev Dashboard**, rather than through the legacy Shopify Admin custom-app screen. For a store you own, Shopify documents the Dev Dashboard client-credentials flow as the simplest authentication method. [1] [2]

## Before you begin

You need access to the Shopify organization that owns the target store, plus permission to develop apps. The account creating the app must be able to manage products and variants because this tool uses `productOptionUpdate`. The project should remain local until the `.env` file is configured; client secrets must never be committed to Git. [1] [3]

| Item | Required value or condition |
|---|---|
| Target store identity | Its permanent `your-store.myshopify.com` domain, not a custom storefront domain. |
| App type | A Dev Dashboard app for this store only. |
| Authentication | Client ID and Client secret, exchanged programmatically for short-lived access tokens. |
| Required scopes | `read_products`, `write_products`, and `read_metaobjects`. |
| Expected metaobject type | `shopify--color-pattern`. |
| Local secrets file | `.env`, excluded from Git by this repository’s `.gitignore`. |

## Important compatibility note

Shopify currently labels the `LinkedMetafieldUpdateInput` API used to link a product option as **early access**. Your store’s existing Color & pattern UI configuration indicates that linked options are available, but you should still run the first live command against one non-critical or duplicate product and inspect the result report before applying a seasonal batch. If Shopify returns a user error related to linked options, stop the run and retain the dry-run report for review. [7]

## Step 1 — Create the app in the Dev Dashboard

Open [Shopify Dev Dashboard](https://dev.shopify.com/dashboard/), select **Apps**, then select **Create app**. Choose **Start from Dev Dashboard**, name the app `Swatch Update` or another internal name, and select **Create**. Shopify uses app versions to capture configuration changes, so the new app must have a released version before it can be installed. [1]

## Step 2 — Create and release version 1

Open the app’s **Versions** area and create a version. This is a non-embedded, local utility, so you may retain Shopify’s default app URL: `https://shopify.dev/apps/default-app-home`. Select the current Webhooks API version even though this first release does not subscribe to webhooks.

Under Admin API scopes, select the following three scopes. Do not request additional customer, order, theme, or file scopes.

| Scope | Why the tool needs it |
|---|---|
| `read_products` | Finds the imported product, its Color option, and the existing option-value IDs. Shopify documents `productByIdentifier` as requiring this scope. [4] |
| `write_products` | Updates the existing Color option values using `productOptionUpdate`. Shopify documents this mutation as requiring this scope. [5] |
| `read_metaobjects` | Resolves `shopify--color-pattern` entries by handle, such as `ivy-green-vintage-ripstop`. Shopify documents this query as requiring this scope. [6] |

Release the version. If you later add or change scopes, create and release another version, then approve the new permissions for the installed store. [1]

## Step 3 — Install the app on the target store

In the app’s **Home** area, select **Install app**, select the target store, and approve the installation. Install this app only on the store whose Matrixify imports it will update. The linker uses the app’s access only during the local command you run.

## Step 4 — Copy credentials securely

Open the app’s **Settings** area. Copy the **Client ID** and **Client secret**. Do not paste either credential into this chat, into a spreadsheet, or into a committed source file. The local tool exchanges these credentials for a short-lived Admin API access token when it runs; Shopify documents that these client-credentials tokens expire after 24 hours. [2] [3]

In your cloned repository, create a local `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` locally and enter the permanent Shopify domain and the two values from Dev Dashboard:

```dotenv
SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
SHOPIFY_CLIENT_ID=replace_with_your_client_id
SHOPIFY_CLIENT_SECRET=replace_with_your_client_secret
SHOPIFY_API_VERSION=2026-07
```

The tool obtains and caches a short-lived access token itself. You should not look for or copy a static Admin API token for a newly created Dev Dashboard app. [3]

## Step 5 — Confirm the organization requirement before your first run

The client-credentials grant works only when the app and the target store belong to the same Shopify organization in Dev Dashboard. If Shopify returns `shop_not_permitted`, verify that the app and store appear in the same Dev Dashboard organization and that `SHOPIFY_SHOP_DOMAIN` is the exact `*.myshopify.com` domain. If the app needs to serve a store in a different organization or a different merchant, this lightweight design must be replaced with an OAuth-based app flow. [3]

## Step 6 — Generate the manifest and run a dry run

After you have configured `.env`, use the application workflow in the repository’s [README](../README.md). The default `link` command is a **no-write dry run**. It resolves every product, Color option value, and metaobject handle, then writes a timestamped report. Do not continue if the report contains any `ERROR` rows.

## Step 7 — Apply only a reviewed, clean run

After you have reviewed the dry-run report and verified a sample product, use the exact live command below. The confirmation text is deliberately required so a casual invocation cannot update Shopify.

```bash
swatch-linker link \
  --manifest output/color_pattern_link_manifest.csv \
  --execute \
  --confirm APPLY_COLOR_PATTERN_LINKS
```

The tool does not change a display label such as `Ivy Green / Vintage Ripstop`. It resolves the target Color & pattern handle `ivy-green-vintage-ripstop` to Shopify’s metaobject GID, then writes that explicit reference to the existing Color option value.

## References

[1]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[2]: https://shopify.dev/docs/apps/build/authentication-authorization/client-secrets "Shopify Developer — About client credentials"
[3]: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens "Shopify Developer — Get API access tokens for Dev Dashboard apps"
[4]: https://shopify.dev/docs/api/admin-graphql/latest/queries/productByIdentifier "Shopify Developer — productByIdentifier"
[5]: https://shopify.dev/docs/api/admin-graphql/latest/mutations/productOptionUpdate "Shopify Developer — productOptionUpdate"
[6]: https://shopify.dev/docs/api/admin-graphql/latest/queries/metaobjectByHandle "Shopify Developer — metaobjectByHandle"
[7]: https://shopify.dev/docs/api/admin-graphql/latest/input-objects/LinkedMetafieldUpdateInput "Shopify Developer — LinkedMetafieldUpdateInput"
