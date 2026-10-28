"""
抓取 Nasdaq綜合 / S&P500 / 費城半導體 最近 7 天內的 開高低收, 產生 index.html 與 data.csv
用法: python update_data.py   (安裝: pip install yfinance pandas)
資料來源: Yahoo Finance (非官方,僅供個人參考); 日期為美股交易日。
"""
import sys
import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

INDICES = [("Nasdaq 綜合指數", "^IXIC"), ("S&P 500", "^GSPC"), ("費城半導體", "^SOX")]
WINDOW_DAYS = 7          # 只保留最近幾天內的資料 (日曆天)
DATE_FMT = "%Y/%m/%d"    # 例: 2026/10/27

def fetch(ticker):
    df = yf.Ticker(ticker).history(period="1mo", auto_adjust=False)
    if df.empty:
        raise RuntimeError("沒有資料")
    df.index = df.index.tz_localize(None).normalize()
    cutoff = df.index[-1] - timedelta(days=WINDOW_DAYS - 1)   # 以最新交易日往回算
    df = df[df.index >= cutoff][["Open", "High", "Low", "Close"]].dropna()
    return df.sort_index(ascending=True)                       # 舊的在上面,最新在最下面

tables, csv_rows, errors = [], [], []
for name, tk in INDICES:
    try:
        df = fetch(tk)
    except Exception as e:
        errors.append(f"{name} ({tk}): {e}")
        tables.append(f"<section><h2>{html.escape(name)}</h2><p class='err'>資料抓取失敗,請稍後再試。</p></section>")
        continue
    rows = ""
    for d, r in df.iterrows():
        rows += (f"<tr><td>{d.strftime(DATE_FMT)}</td><td>{r.Open:,.2f}</td>"
                 f"<td>{r.High:,.2f}</td><td>{r.Low:,.2f}</td><td>{r.Close:,.2f}</td></tr>")
        csv_rows.append([name, d.strftime(DATE_FMT), round(r.Open, 2), round(r.High, 2),
                         round(r.Low, 2), round(r.Close, 2)])
    tables.append(
        f"<section><h2>{html.escape(name)} <small>{tk}</small></h2>"
        "<div class='wrap'><table><thead><tr><th>時間</th><th>開</th><th>高</th><th>低</th><th>收</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div></section>")

if len(errors) == len(INDICES):
    print("全部抓取失敗:", *errors, sep="\n")
    sys.exit(1)

now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y/%m/%d %H:%M")
page = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>美股三大指數 近7天</title>
<style>
:root{{--bg:#fafaf8;--fg:#1c1c1a;--mute:#6b6b66;--line:#dcdcd6;--card:#fff;--head:#f0f0ea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161614;--fg:#ecece6;--mute:#9a9a92;--line:#34342f;--card:#1f1f1c;--head:#2a2a26}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font-family:system-ui,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif}}
main{{max-width:720px;margin:0 auto}}
h1{{font-size:20px;margin:4px 0 2px}} .sub{{color:var(--mute);font-size:13px;margin-bottom:16px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:14px}}
h2{{font-size:16px;margin:0 0 8px}} h2 small{{color:var(--mute);font-weight:400;font-size:12px;margin-left:6px}}
.wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:14px}}
th,td{{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}} thead th{{background:var(--head);font-weight:600}}
tbody tr:last-child td{{border-bottom:none}} .err{{color:#b3261e}}
footer{{color:var(--mute);font-size:12px;margin-top:8px;line-height:1.6}}
</style></head><body><main>
<h1>美股三大指數 近 {WINDOW_DAYS} 天</h1>
<div class="sub">最後更新(台北時間):{now}</div>
{''.join(tables)}
<footer>日期為美股交易日,最新一筆通常是台灣時間前一天收盤。資料來源 Yahoo Finance,可能有延遲或誤差,僅供參考,不構成投資建議。
<a href="data.csv">下載 CSV</a></footer>
</main></body></html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page)
pd.DataFrame(csv_rows, columns=["指數", "時間", "開", "高", "低", "收"]).to_csv(
    "data.csv", index=False, encoding="utf-8-sig")
print("已更新 index.html 與 data.csv", "| 失敗:" + "; ".join(errors) if errors else "")
