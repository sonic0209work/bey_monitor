# bey_monitor

監控 [funbox 戰鬥陀螺分類頁](https://shop.funbox.com.tw/categories/XI/KB) 是否有新商品上架，一偵測到就透過 LINE / Telegram / Email 發通知。

## 運作方式

網站是 Cyberbiz 平台架設的商店，分類頁本身是用 Vue 前端呼叫下面這支 JSON API 渲染商品列表：

```
GET https://shop.funbox.com.tw/category_products/XI/KB.json?limit=50&page=1&sort_by=sell_from-desc
```

`monitor.py` 直接打這支 API（比整頁爬蟲穩定很多），依照商品各 variant 的 `inventory_quantity` 判斷是否有貨（邏輯與網站前端的 `isAvailable` 完全一致），並把「目前有貨商品 id 集合」存進 `state/state.json`。每次執行只在集合出現**新的** id 時才發通知（避免重複打擾），同時也會在 log 裡標出下架/售完的商品。

## 安裝

```bash
cd bey_monitor
cp .env.example .env   # 填入你要啟用的通知管道憑證
```

不需要額外安裝套件，`monitor.py` 只使用 Python 標準函式庫。

## 手動執行

```bash
python3 monitor.py
```

## 通知管道設定

`.env` 裡任一管道沒填憑證就會自動略過，可以只設定其中一個先測試。

- **LINE**：LINE Notify 已於 2025-03-31 停用，改用 LINE Messaging API 官方帳號推播訊息，需要 `LINE_CHANNEL_ACCESS_TOKEN` + `LINE_USER_ID`（步驟見 `.env.example` 註解）。
- **Telegram**：跟 [@BotFather](https://t.me/BotFather) 建立機器人取得 token，再取得你的 chat id。
- **Email**：用 Gmail SMTP，需要先開兩步驟驗證並建立「應用程式密碼」當作 `SMTP_PASSWORD`。

## 測試

```bash
python3 -m pytest tests/ -v
```

`is_available` 等核心邏輯有涵蓋測試；由於分類頁目前實際是空的（沒有商品），無法用真實資料測試「偵測到新商品」的完整流程，測試用假資料模擬。

## 排程（GitHub Actions）

用 `.github/workflows/poll.yml` 每 10 分鐘觸發一次（GitHub Actions cron 最小粒度是 5 分鐘，且偶爾會因平台負載延遲幾分鐘）：

- Repo 必須是**公開**的，否則 Actions 分鐘數會很快超過免費額度（10 分鐘一次一個月約 2880 分鐘，遠超私有 repo 免費的 2000 分鐘/月；公開 repo 則不限）。程式碼公開沒關係，通知密鑰是分開存放的。
- 密鑰存在 GitHub repo 的 Encrypted Secrets（`gh secret set ...`），不會出現在程式碼或 log 裡。
- 每次執行完會自動把 `state/state.json` commit + push 回 repo，這樣才能記住哪些商品已經看過，同時也讓 repo 保持活躍（避免 GitHub 60 天無活動自動停用排程）。
- 想調整頻率：修改 `.github/workflows/poll.yml` 裡的 `cron: "*/10 * * * *"`。
- 想立即手動觸發一次：到 repo 的 Actions 分頁，選這個 workflow，按 "Run workflow"。

需要在 repo 設定以下 Secrets（哪個沒設，對應通知管道就自動略過）：
`LINE_CHANNEL_ACCESS_TOKEN`、`LINE_USER_ID`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`、`SMTP_USER`、`SMTP_PASSWORD`
