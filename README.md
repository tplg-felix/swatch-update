# Shopify Swatch Update

`shopify-swatch-linker` is a small, manually triggered Python application for a specific Shopify and Matrixify workflow. It preserves a customer-facing variant label such as `Ivy Green / Vintage Ripstop`, derives the intended Color & pattern handle `ivy-green-vintage-ripstop`, and explicitly links the existing Color option value to the matching `shopify--color-pattern` metaobject.

The tool is designed for values that contain `/` and therefore cannot safely rely on Shopify’s convenience matching between a display label and a metaobject handle. It does not alter Matrixify labels, product titles, SKUs, or ordinary variant metafields.

> Shopify currently labels the linked-product-option input used by this workflow as **early access**. Use the dry run first, then test the first live update on one non-critical or duplicate product before applying a full seasonal batch. [6]

## Workflow

| Stage | What happens | Does it modify Shopify? |
|---|---|---:|
| Build manifest | Read the Matrixify workbook and generate an audited list of slash-containing Color values plus expected metaobject handles. | No |
| Matrixify import | Create or update products and variants through the normal Matrixify workflow. | Yes, by Matrixify |
| Dry run | Resolve products, Color option values, and Color & pattern metaobjects; write a result report. | No |
| Live execution | Update only reviewed option values with explicit metaobject references. | Yes, only with `--execute` and the required confirmation text |

## Prerequisites

You need Python 3.11 or later, a Matrixify `.xlsx` or `.xlsm` export, and a Shopify Dev Dashboard app that is installed on the target store. Shopify’s current Dev Dashboard flow uses a Client ID and Client secret to request short-lived access tokens for a store you own; those tokens are not copied from the Shopify Admin UI. [1] [2]

The Shopify app needs only the following Admin API scopes.

| Scope | Reason |
|---|---|
| `read_products` | Read the imported product, its Color option, and its existing option-value IDs. The underlying product lookup requires this scope. [3] |
| `write_products` | Explicitly update existing Color option values. The underlying `productOptionUpdate` mutation requires this scope. [4] |
| `read_metaobjects` | Resolve the `shopify--color-pattern` entry by its type and handle. [5] |

Follow the complete [Shopify custom-app setup guide](docs/SHOPIFY_CUSTOM_APP_SETUP.md) before running a Shopify command.

## Local installation

Clone the repository, create an isolated environment, and install the application in editable mode.

```bash
git clone https://github.com/tplg-felix/swatch-update.git
cd swatch-update
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

Create the local credentials file. The `.gitignore` file excludes `.env`, so it must remain only on your computer.

```bash
cp .env.example .env
```

Set the permanent Shopify domain and the Dev Dashboard credentials in `.env`.

```dotenv
SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
SHOPIFY_CLIENT_ID=replace_with_your_client_id
SHOPIFY_CLIENT_SECRET=replace_with_your_client_secret
SHOPIFY_API_VERSION=2026-07
```

> Never commit `.env`, client secrets, access tokens, Matrixify exports, or result reports. Shopify explicitly advises storing the Client secret in a `.env` file and excluding it from version control. [2]

## Runbook for each Matrixify upload

### 1. Generate the manifest before importing products

Place the Matrixify source workbook outside the repository or in the ignored `input/` folder. The command reads the `Product` worksheet without modifying it. It selects rows where `Option 1 Name` is `Color` and `Option 1 Value` contains `/`.

```bash
swatch-linker build-manifest \
  input/INTLwebFW26newlisting.xlsx \
  --manifest output/color_pattern_link_manifest.csv \
  --preflight output/color_pattern_metaobject_preflight.csv
```

The command produces two CSV files. The manifest contains one expected reference per affected Matrixify row. The preflight file collapses this to one row per distinct `shopify--color-pattern` handle so that you can confirm the required metaobjects exist before importing the products.

### 2. Import the original Matrixify `Product` worksheet normally

Do not replace a visible option value such as `Ivy Green / Vintage Ripstop` with `ivy-green-vintage-ripstop`. The first is the display label; the second is a stable metaobject identity. The application deliberately keeps those roles separate.

### 3. Run the no-write dry run

Run this only after Matrixify has completed. It makes read-only GraphQL requests, checks each product, confirms the Color option and its value exist, resolves the target metaobject handle, and writes a timestamped report in `reports/`.

```bash
swatch-linker link \
  --manifest output/color_pattern_link_manifest.csv \
  --output-dir reports
```

Review the result report before proceeding. A clean first pass should mainly contain `WOULD_LINK` or `ALREADY_LINKED` values.

| Status | Meaning | Required response |
|---|---|---|
| `WOULD_LINK` | The no-write validation found a valid product, option value, and target metaobject. | Review it, then it is eligible for live execution. |
| `ALREADY_LINKED` | The imported option value is already connected to the expected metaobject. | No action is needed. |
| `ERROR` | A product, option, option value, handle, scope, or Shopify configuration requirement was not satisfied. | Correct the issue, regenerate or revise the manifest, and rerun the dry run. |
| `SKIPPED` | Another value in the same product’s Color option failed validation. The tool intentionally refuses a partial option update. | Resolve the associated `ERROR` first. |

### 4. Apply reviewed links

Proceed only when the dry-run report contains no `ERROR` or `SKIPPED` rows. The explicit confirmation string is a deliberate safeguard against accidental writes.

```bash
swatch-linker link \
  --manifest output/color_pattern_link_manifest.csv \
  --output-dir reports \
  --execute \
  --confirm APPLY_COLOR_PATTERN_LINKS
```

The live command uses Shopify’s `productOptionUpdate` mutation to write the `linkedMetafieldValue` reference. The product option is linked to `shopify.color-pattern` only if it is currently unlinked; the tool stops rather than overriding a differently linked option. [4]

## Behavior and safeguards

The tool follows a **validate first, mutate second** model. It never sends a mutation unless both `--execute` and the exact confirmation text are present. It resolves a real metaobject GID from the expected handle before updating the option value. Metaobject handles are unique within a type, which makes `shopify--color-pattern` plus a handle the appropriate stable lookup key. [5]

A live update is all-or-nothing for each product’s Color option. If one candidate value on that product has an error, the tool skips the other pending values for the same option. Existing links that already match the intended target are left unchanged. A Color option that is already linked to another metafield is treated as an error and is never overwritten automatically.

## Development checks

Run the test suite and lint checks before committing repository changes.

```bash
pytest
ruff check .
```

## Project structure

| Path | Purpose |
|---|---|
| `src/swatch_update/manifest.py` | Reads Matrixify workbooks and produces manifest and preflight CSVs. |
| `src/swatch_update/shopify.py` | Handles Dev Dashboard client-credentials token exchange and Shopify GraphQL requests. |
| `src/swatch_update/linker.py` | Validates and applies explicit metaobject links with per-product safety boundaries. |
| `src/swatch_update/cli.py` | Provides the `swatch-linker` commands. |
| `docs/SHOPIFY_CUSTOM_APP_SETUP.md` | Step-by-step Shopify setup guide. |
| `tests/` | Unit tests for handle derivation, manifest generation, and write safeguards. |

## References

[1]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[2]: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens "Shopify Developer — Get API access tokens for Dev Dashboard apps"
[3]: https://shopify.dev/docs/api/admin-graphql/latest/queries/productByIdentifier "Shopify Developer — productByIdentifier"
[4]: https://shopify.dev/docs/api/admin-graphql/latest/mutations/productOptionUpdate "Shopify Developer — productOptionUpdate"
[5]: https://shopify.dev/docs/api/admin-graphql/latest/queries/metaobjectByHandle "Shopify Developer — metaobjectByHandle"
[6]: https://shopify.dev/docs/api/admin-graphql/latest/input-objects/LinkedMetafieldUpdateInput "Shopify Developer — LinkedMetafieldUpdateInput"
