import os
import requests
import pandas as pd
import numpy as np

def send_line_push(message_text):
    """
    透過 LINE Messaging API 發送 Push Message 給個人帳號
    """
    # 讀取在 GitHub Secrets 設定的環境變數
    access_token = os.environ.get("BPLYYKmyvJCpM0UsYsKsOEuy3Jgc+AOY61EmVpxf+ZG3lrl8pcXa5sosjhBoVFjxAwV0DvblZlufHS+NfPx1rOdbkdyH0guWvBF+Zw6K0EzixFA9PYOVfYi/M5piiJbeU0TDLm/S1zHb0V00dy0qrAdB04t89/1O/w1cDnyilFU=")
    user_id = os.environ.get("U660a3a222f70deefa056e5ec612b9bf4")
    
    # 檢查環境變數是否存在
    if not access_token or not user_id:
        print("❌ 錯誤：找不到 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID 環境變數！")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ LINE 訊息推播成功！")
        else:
            print(f"❌ LINE 發送失敗，HTTP 狀態碼：{response.status_code}")
            print(f"回應內容：{response.text}")
    except Exception as e:
        print(f"❌ 發送 LINE 訊息時發生例外錯誤：{e}")


def main():
    print("🚀 開始執行每日選股與買賣點計算...")
    
    # ==========================================
    # 💡 在這裡放你原本的選股與買賣點計算邏輯
    # ==========================================
    
    # 範例選股結果（請替換成你的實際選股運算產出）
    report = (
        "📈 【每日台股選股與風控報告】\n"
        "------------------------------\n"
        "🔥 強勢標的：2330 台積電\n"
        "🎯 建議買點：觀察 5 日線支撐\n"
        "🛑 停損位置：跌破前低關鍵價位\n"
        "------------------------------\n"
        "💡 警語：本報告僅供選股策略參考，投資前請獨立評估風險。"
    )
    
    print("📊 選股計算完成，準備發送通知...")
    
    # 發送 LINE 推播訊息
    send_line_push(report)


if __name__ == "__main__":
    main()
