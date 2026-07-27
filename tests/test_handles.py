from swatch_update.handles import normalize_metaobject_handle


def test_normalize_metaobject_handle_for_slash_containing_label() -> None:
    assert (
        normalize_metaobject_handle("Ivy Green / Vintage Ripstop")
        == "ivy-green-vintage-ripstop"
    )


def test_normalize_metaobject_handle_collapses_symbols_and_accents() -> None:
    assert normalize_metaobject_handle("Écru & Navy  /  Ripstop") == "ecru-navy-ripstop"
