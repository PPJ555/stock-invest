import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# 1. 環境變數設定
# ==========================================
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")

# 預設追蹤熱門標的清單（亦可替換為全台股代碼）
STOCK_LIST = ["2330", "2317", "2454", "2308", "2382", "3231", "2376", "6669", "3017", "2356"]

def send_line_notify(message: str):
    """發送訊息至 LINE Notify"""
    if not LINE_NOTIFY_TOKEN:
        print("未設定 LINE_NOTIFY_TOKEN，跳過 LINE 推播。")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    data = {"message": message}
    try:
        requests.post(url, headers=headers, data=data)
        print("LINE 推播成功！")
    except Exception as e:
        print(f"LINE 推播發送失敗: {e}")

def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """
    爬取個股歷史K線資料 (可替換為 FinMind 或 TWSE OpenAPI)
    這裡採用 Yahoo Finance API 示範
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.TW?range=3mo&interval=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers).json()
        result = res['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        df = pd.DataFrame({
            'date': [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in timestamps],
            'open': quote['open'],
            'high': quote['high'],
            'low': quote['low'],
            'close': quote['close'],
            'volume': quote['volume']
        }).dropna()
        return df
    except Exception as e:
        print(f"抓取 {symbol} 資料失敗: {e}")
        return pd.DataFrame()

def analyze_stock(symbol: str, df: pd.DataFrame) -> dict:
    """策略與黃金買賣點算數邏輯"""
    if len(df) < 30:
        return None

    # 計算技術指標
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol_ma5'] = df['volume'].rolling(5).mean()

    latest = df.iloc[-1]
    yesterday = df.iloc[-2]
    past_20 = df.iloc[-21:-1]

    # --- 1. 型態條件：出量突破 ---
    vol_breakout = latest['volume'] >= (yesterday['vol_ma5'] * 2.0)  # 成交量高於5日均量2倍
    price_breakout = latest['close'] > past_20['high'].max()         # 創20日新高
    is_solid_red = (latest['close'] > latest['open']) and ((latest['close'] - latest['open']) >= (latest['high'] - latest['close']))

    if not (vol_breakout and price_breakout and is_solid_red):
        return None

    # --- 2. 買賣點與風控演算法 ---
    # 建議進場價 (取 20日平台高點 與 K線實體中點/5MA 之交會支撐區)
    k_mid = (latest['open'] + latest['close']) / 2
    suggested_entry = round(min(latest['close'], max(past_20['high'].max(), k_mid, latest['ma5'])), 2)

    # 停損價 (突破K低點往下寬限 1%)
    stop_loss = round(latest['low'] * 0.99, 2)
    risk_amount = suggested_entry - stop_loss
    risk_pct = round((risk_amount / suggested_entry) * 100, 2)

    # 第一目標價 (以 1:2.0 盈虧比計算)
    target_1 = round(suggested_entry + (risk_amount * 2.0), 2)
    reward_pct = round(((target_1 - suggested_entry) / suggested_entry) * 100, 2)

    return {
        "symbol": symbol,
        "date": latest['date'],
        "close": round(latest['close'], 2),
        "suggested_entry": suggested_entry,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "risk_pct": risk_pct,
        "reward_pct": reward_pct,
        "volume_ratio": round(latest['volume'] / yesterday['vol_ma5'], 1)
    }

def main():
    results = []
    print("開始執行盤後自動選股計算...")
    
    for symbol in STOCK_LIST:
        df = fetch_stock_data(symbol)
        item = analyze_stock(symbol, df)
        if item:
            results.append(item)

    # 輸出選股結果至 daily_picks.json
    with open("daily_picks.json", "w", encoding="utf-8") as f:
        json.dump({
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "picks": results
        }, f, ensure_ascii=False, indent=2)

    # 組合 LINE 推播訊息
    if results:
        msg = f"\n🚨【今日突破精選股】({datetime.now().strftime('%m/%d')})\n-----------------------------"
        for stock in results:
            msg += (
                f"\n📈 標的：{stock['symbol']} (現價: {stock['close']})\n"
                f"🎯 建議進場：{stock['suggested_entry']} 元 (回測掛單)\n"
                f"🛡️ 防守停損：{stock['stop_loss']} 元 (-{stock['risk_pct']}%)\n"
                f"🎯 第一目標：{stock['target_1']} 元 (+{stock['reward_pct']}%)\n"
                f"-----------------------------"
            )
        send_line_notify(msg)
    else:
        print("今日無符合爆量突破標準之標的。")

if __name__ == "__main__":
    main()
