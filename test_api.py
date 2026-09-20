import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("1. Testing /status")
    res = requests.get(f"{BASE_URL}/status")
    print("Status:", res.status_code, res.json())

    print("\n2. Testing /refresh_balance")
    res = requests.post(f"{BASE_URL}/refresh_balance")
    print("Refresh Balance:", res.status_code, res.json())

    print("\n3. Testing /order/manual (Paper Trading Mock Buy)")
    res = requests.post(f"{BASE_URL}/order/manual", json={"side": "buy", "quantity": 10, "price": 10000})
    print("Manual Order Buy:", res.status_code, res.json())

    print("\n4. Testing /order/manual (Paper Trading Mock Sell)")
    res = requests.post(f"{BASE_URL}/order/manual", json={"side": "sell", "quantity": 10, "price": 20000})
    print("Manual Order Sell:", res.status_code, res.json())

    print("\n5. Testing /status again to check positions")
    res = requests.get(f"{BASE_URL}/status")
    status_data = res.json()
    print("Status:", res.status_code, status_data)
    positions = status_data.get("positions", [])
    
    if positions:
        pid = positions[0]["id"]
        print(f"\n6. Testing /order/cancel (Single Cancel for id {pid})")
        res = requests.post(f"{BASE_URL}/order/cancel", json={"order_id": pid})
        print("Cancel Order:", res.status_code, res.json())
        
        print("\n7. Testing /order/cancel_list (Cancel List)")
        res = requests.post(f"{BASE_URL}/order/cancel_list", json={"ids": [p["id"] for p in positions]})
        print("Cancel List:", res.status_code, res.json())
    else:
        print("\n6. No positions to cancel.")

    print("\n8. Testing /order/cancel_all")
    res = requests.post(f"{BASE_URL}/order/cancel_all")
    print("Cancel All:", res.status_code, res.json())

    print("\n9. Testing /history")
    res = requests.get(f"{BASE_URL}/history?limit=5")
    print("History:", res.status_code, res.json())

    print("\n10. Testing /history/clear")
    res = requests.post(f"{BASE_URL}/history/clear")
    print("History Clear:", res.status_code, res.json())

if __name__ == "__main__":
    test_api()
