# Shopify Custom-App Setup Research Notes

Shopify’s current guidance for a single-store integration is to create the app in the **Dev Dashboard**, create and release an app version with the required Admin API scopes, install the app on the target store, and authenticate with a client-credentials grant. The Dev Dashboard is specifically positioned for quick integrations with an existing system. [1]

| Requirement | Verified current guidance |
|---|---|
| App creation | Create the app from the Dev Dashboard, rather than creating a new legacy custom app in Shopify Admin. [1] |
| Version | A version is required before installation. For this non-embedded command-line integration, Shopify permits the default app URL. [1] |
| Product lookup | `read_products` is required to resolve each imported product by handle. [7] |
| Product updates | `write_products` covers the option-value changes used by the linking mutation. [2] |
| Metaobject access | `read_metaobjects` is required to resolve each Color & pattern handle to a Shopify metaobject ID. [2] |
| Authentication | The app’s Client ID and Client secret request an access token from Shopify’s OAuth endpoint with `grant_type=client_credentials`; the token expires after 24 hours. [1] [3] [4] |
| Token constraint | Client credentials work only when the app and target store belong to the same Shopify organization in the Dev Dashboard. [4] |
| Linking mutation | `productOptionUpdate` requires `write_products` and supports updating the linked metaobject value for an existing option value. [5] |
| Handle resolution | `metaobjectByHandle` requires `read_metaobjects`; a metaobject handle is unique within its type and returns the GID required for the linkage. [6] |

## References

[1]: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard "Shopify Developer — Create apps using the Dev Dashboard"
[2]: https://shopify.dev/docs/api/usage/access-scopes "Shopify Developer — Shopify API access scopes"
[3]: https://shopify.dev/docs/apps/build/authentication-authorization/client-secrets "Shopify Developer — About client credentials"
[4]: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens "Shopify Developer — Get API access tokens for Dev Dashboard apps"
[5]: https://shopify.dev/docs/api/admin-graphql/latest/mutations/productOptionUpdate "Shopify Developer — productOptionUpdate"
[6]: https://shopify.dev/docs/api/admin-graphql/latest/queries/metaobjectByHandle "Shopify Developer — metaobjectByHandle"
[7]: https://shopify.dev/docs/api/admin-graphql/latest/queries/productByIdentifier "Shopify Developer — productByIdentifier"
