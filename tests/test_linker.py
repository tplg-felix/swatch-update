from swatch_update.linker import link_rows
from swatch_update.models import LinkRow


class FakeShopifyClient:
    def __init__(self) -> None:
        self.update_calls = []
        self.product = {
            "id": "gid://shopify/Product/1",
            "handle": "card-sacoche",
            "options": [
                {
                    "id": "gid://shopify/ProductOption/2",
                    "name": "Color",
                    "linkedMetafield": {"namespace": "shopify", "key": "color-pattern"},
                    "optionValues": [
                        {
                            "id": "gid://shopify/ProductOptionValue/3",
                            "name": "Ivy Green / Vintage Ripstop",
                            "linkedMetafieldValue": None,
                        }
                    ],
                }
            ],
        }
        self.metaobject = {
            "id": "gid://shopify/Metaobject/4",
            "handle": "ivy-green-vintage-ripstop",
            "type": "shopify--color-pattern",
        }

    def get_product_by_handle(self, handle: str):
        assert handle == "card-sacoche"
        return self.product

    def get_metaobject_by_handle(self, handle: str):
        assert handle == "ivy-green-vintage-ripstop"
        return self.metaobject

    def update_option_values(self, product_id: str, option: dict, values: list[dict]):
        self.update_calls.append((product_id, option, values))
        return []


def _row() -> LinkRow:
    return LinkRow(
        source_excel_row=4,
        product_handle="card-sacoche",
        product_title="Card Sacoche",
        variant_sku="TP-WBA-CSC-IGN-55",
        option_name="Color",
        option_value="Ivy Green / Vintage Ripstop",
        metaobject_handle="ivy-green-vintage-ripstop",
        expected_source_color="Ivy Green",
        expected_source_material="Vintage Ripstop",
    )


def test_dry_run_never_calls_shopify_mutation() -> None:
    client = FakeShopifyClient()

    results = link_rows([_row()], client, execute=False)

    assert results[0].status == "WOULD_LINK"
    assert results[0].action == "LINK"
    assert client.update_calls == []


def test_execute_calls_shopify_mutation_after_validation() -> None:
    client = FakeShopifyClient()

    results = link_rows([_row()], client, execute=True)

    assert results[0].status == "LINKED"
    assert len(client.update_calls) == 1
    _, _, values = client.update_calls[0]
    assert values == [
        {
            "id": "gid://shopify/ProductOptionValue/3",
            "linkedMetafieldValue": "gid://shopify/Metaobject/4",
        }
    ]
