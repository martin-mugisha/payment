from config.models import BalanceRequest, OrderQueryRequest, PrepaidBillRequest, StatementRequest, UnifiedOrderRequest
from . import base as settings
from .utils import generate_signature, generate_timestamp, generate_unique_id, verify_signature
import requests
import json
import time
from typing import Dict, Any

merchant_id = settings.PAYMENT_MERCHANT_ID
apikey = settings.PAYMENT_AGGREGATOR_API_KEY
notifyurl = settings.PAYMENT_AGGREGATOR_WEBHOOK_URL
base_url = settings.PAYMENT_AGGREGATOR_BASE_URL


class UnifiedOrder:
    def __init__(self):
        pass

    def create_order(self, trader_id: str, amount: int, channel: int, transaction_type: int, name: str, message: str) -> dict:
        timestamp = generate_timestamp()
        out_trade_no = generate_unique_id()

        request_data = {
            "Version": "v1.0",
            "MchID": merchant_id,
            "TimeStamp": timestamp,
            "Channel": channel,
            "OutTradeNo": out_trade_no,
            "Amount": amount,
            "TransactionType": transaction_type,
            "TraderID": trader_id,
            "TraderFullName": name,
            "Description": message,
            "NotifyUrl": notifyurl,
        }
        request_data["Sign"] = generate_signature(request_data, apikey)

        url = f"{base_url}/unifiedorder"
        headers = {
            'Content-Type': 'application/json',
        }

        order = UnifiedOrderRequest(
            timestamp=timestamp,
            channel=channel,
            out_trade_no=out_trade_no,
            amount=amount,
            transaction_type=transaction_type,
            trader_id=trader_id,
            trader_full_name=name,
            description=message,
            notify_url=notifyurl
        )
        order.save()
        try:
            resp = requests.post(url, json=request_data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json(), resp.status_code
        except requests.RequestException as e:
            return {"error": f"Failed to connect to aggregator: {str(e)}"}, 503
        except json.JSONDecodeError:
            return {"error": "Invalid response from aggregator"}, 502


class PaymentResults:
    def __init__(self):
        pass

    def get_result(self, unique_id: str) -> dict:
        timestamp = generate_timestamp()
        request_data = {
            "Version": "v1.0",
            "MchID": merchant_id,
            "TimeStamp": timestamp,
            "OutTradeNo": unique_id,
        }
        request_data["Sign"] = generate_signature(request_data, apikey)

        url = f"{base_url}/orderquery"
        headers = {
            'Content-Type': 'application/json',
        }
        get_result=OrderQueryRequest(
            timestamp=timestamp,
            out_trade_no=unique_id
        )
        get_result.save()
        try:
            resp = requests.post(url, json=request_data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json(), resp.status_code
        except requests.RequestException as e:
            return {"error": f"Failed to connect to aggregator: {str(e)}"}, 503
        except json.JSONDecodeError:
            return {"error": "Invalid response from aggregator"}, 502


class PaymentResultsCallback:
    def __init__(self, apikey: str):
        self.apikey = apikey
        self.order_status = {}

    def handle_notification(self, data: Dict[str, Any]) -> str:
        if not data:
            print("No data received in notification.")
            return "FAILED"

        if not verify_signature(data, self.apikey):
            print("Signature verification failed.")
            return "FAILED"

        order_id = data.get("OutTradeNo")
        if not order_id:
            print("Missing OutTradeNo.")
            return "FAILED"

        if self.is_duplicate(order_id):
            print(f"Duplicate notification for {order_id}. Ignoring.")
            return "SUCCESS"

        try:
            pay_status = int(data.get("PayStatus", -1))
        except (ValueError, TypeError):
            print("Invalid PayStatus value.")
            return "FAILED"

        if pay_status == 1:
            self.order_status[order_id] = "processed"
            print(f"Payment for order {order_id} processed successfully.")
            return "SUCCESS"
        elif pay_status == 2:
            self.order_status[order_id] = "failed"
            print(f"Payment for order {order_id} failed.")
            return "FAILED"
        else:
            print(f"Unhandled PayStatus: {pay_status}")
            return "FAILED"

    def is_duplicate(self, order_id: str) -> bool:
        return self.order_status.get(order_id) == "processed"


class PrepaidBill:
    def __init__(self):
        pass

    def get_bill(self, trader_id: str, amount: int, channel: int, transaction_type: int) -> dict:
        timestamp = generate_timestamp()
        request_data = {
            "Version": "v1.0",
            "MchID": merchant_id,
            "TimeStamp": timestamp,
            "Channel": channel,
            "TransactionType": transaction_type,
            "TraderID": trader_id,
            "Amount": amount
        }
        request_data["Sign"] = generate_signature(request_data, apikey)

        url = f"{base_url}/bill"
        headers = {
            'Content-Type': 'application/json',
        }
        get_bill_request = PrepaidBillRequest(
            timestamp=timestamp,
            channel=channel,
            transaction_type=transaction_type,
            trader_id=trader_id,
            amount=amount
        )
        get_bill_request.save()
        try:
            resp = requests.post(url, json=request_data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": f"Connection failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from aggregator"}


class GetBalance:
    def __init__(self):
        pass

    def get_balance(self) -> dict:
        timestamp = generate_timestamp()
        request_data = {
            "Version": "v1.0",
            "MchID": merchant_id,
            "TimeStamp": timestamp
        }
        request_data["Sign"] = generate_signature(request_data, apikey)

        url = f"{base_url}/balance"
        headers = {
            'Content-Type': 'application/json',
        }

        get_baalance_request = BalanceRequest(
            timestamp=timestamp
        )
        get_baalance_request.save()
        try:
            resp = requests.post(url, json=request_data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": f"Connection failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from aggregator"}


class GetStatementOfAccount:
    def __init__(self):
        pass

    def fetch(self, start_date: str = None, end_date: str = None) -> dict:
        timestamp = generate_timestamp()
        request_data = {
            "Version": "v1.0",
            "MchID": merchant_id,
            "TimeStamp": timestamp
        }

        if start_date:
            request_data["StartTime"] = start_date
        if end_date:
            request_data["EndTime"] = end_date

        request_data["Sign"] = generate_signature(request_data, apikey)


        url = f"{base_url}/statement"
        headers = {
            'Content-Type': 'application/json',
        }

        fetch = StatementRequest(
            timestamp=timestamp,
            start_time=start_date,
            end_time=end_date
        )
        fetch.save()
        try:
            resp = requests.post(url, json=request_data, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": f"Connection failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from aggregator"}