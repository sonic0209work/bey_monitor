"""Monitor a Cyberbiz category listing (shop.funbox.com.tw) for newly
available products and send notifications when new stock appears.

Run once per invocation; intended to be triggered on a schedule (cron /
cloud scheduler). Each run:
  1. Fetches every page of the category's JSON product feed.
  2. Works out which products are currently purchasable (in stock).
  3. Compares that set against the previous run's state.
  4. Notifies (LINE / Telegram / Email) about products that newly became
     available, then persists the new state.
"""
import json
import logging
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

import config
from notifiers import notify_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("monitor")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_page(page: int) -> list:
    url = f"{config.CATEGORY_JSON_URL}?limit={config.PAGE_LIMIT}&page={page}&sort_by=sell_from-desc"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_products() -> list:
    products = []
    for page in range(1, config.MAX_PAGES + 1):
        batch = fetch_page(page)
        if not batch:
            break
        products.extend(batch)
        if len(batch) < config.PAGE_LIMIT:
            break
    return products


def is_available(product: dict) -> bool:
    """Mirrors the site's own Vue `isAvailable` computed property:
    any variant with inventory_quantity === null is treated as unlimited
    stock; otherwise availability is the sum of variant quantities != 0.
    """
    variants = product.get("variants") or []
    if not variants:
        return False
    total = 0
    for v in variants:
        qty = v.get("inventory_quantity")
        if qty is None:
            return True
        total += qty
    return total != 0


def product_url(product: dict) -> str:
    url = product.get("url") or ""
    if url.startswith("http"):
        return url
    return config.SHOP_BASE_URL.rstrip("/") + "/" + url.lstrip("/")


def load_state() -> dict:
    if config.STATE_FILE.exists():
        try:
            return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("state.json 損毀，視為初次執行")
    return {"available_ids": []}


def save_state(available_ids: list) -> None:
    config.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.STATE_FILE.write_text(
        json.dumps(
            {
                "available_ids": sorted(available_ids),
                "last_checked": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def format_message(new_products: list) -> str:
    lines = [f"🎉 偵測到 {len(new_products)} 件商品上架！", ""]
    for p in new_products:
        price = p.get("price")
        lines.append(f"・{p.get('title')}（NT${price}）\n  {product_url(p)}")
    lines.append("")
    lines.append(config.CATEGORY_PAGE_URL)
    return "\n".join(lines)


def run() -> int:
    try:
        products = fetch_all_products()
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        log.error("抓取商品清單失敗: %s", e)
        return 1

    available = {str(p["id"]): p for p in products if is_available(p)}
    log.info("目前上架/有貨商品數: %d（共取得 %d 筆）", len(available), len(products))

    state = load_state()
    previous_ids = set(state.get("available_ids", []))
    current_ids = set(available.keys())

    new_ids = current_ids - previous_ids
    gone_ids = previous_ids - current_ids
    if gone_ids:
        log.info("已下架/售完商品數: %d", len(gone_ids))

    if new_ids:
        new_products = [available[pid] for pid in new_ids]
        log.info("新上架商品: %s", [p.get("title") for p in new_products])
        message = format_message(new_products)
        notify_all("商品上架通知 - Beyblade監控", message)
    else:
        log.info("無新上架商品")

    save_state(list(current_ids))
    return 0


if __name__ == "__main__":
    sys.exit(run())
