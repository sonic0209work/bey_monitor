import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import monitor  # noqa: E402


def make_product(id_, title, qty, price=990):
    return {
        "id": id_,
        "title": title,
        "price": price,
        "url": f"/products/{id_}",
        "variants": [{"inventory_quantity": qty}],
    }


def test_is_available_in_stock():
    assert monitor.is_available(make_product(1, "A", 5)) is True


def test_is_available_out_of_stock():
    assert monitor.is_available(make_product(1, "A", 0)) is False


def test_is_available_unlimited_when_null():
    assert monitor.is_available(make_product(1, "A", None)) is True


def test_is_available_no_variants():
    assert monitor.is_available({"id": 1, "title": "A", "variants": []}) is False


def test_product_url_relative():
    p = make_product(1, "A", 1)
    assert monitor.product_url(p) == "https://shop.funbox.com.tw/products/1"


def test_diff_detects_new_arrival(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor.config, "STATE_FILE", tmp_path / "state.json")
    monitor.save_state(["1"])
    state = monitor.load_state()
    assert state["available_ids"] == ["1"]

    previous_ids = set(state["available_ids"])
    current_ids = {"1", "2"}
    assert current_ids - previous_ids == {"2"}


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
