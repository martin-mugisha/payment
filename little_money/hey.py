#!/usr/bin/env python3
"""
LipaPay Airtel Prepaid Bill API Script
This script calls the LipaPay API to get prepaid bill information using Airtel as the channel.
"""

import hashlib
import time
import requests
import json
from typing import Dict, Any

class LipaPayAPI:
    def __init__(self, merchant_id: int, private_key: str, environment: str = "development"):
        """
        Initialize LipaPay API client
        
        Args:
            merchant_id: Your merchant ID provided by LipaPay
            private_key: Your private key for signature generation
            environment: 'development' or 'production'
        """
        self.merchant_id = merchant_id
        self.private_key = private_key
        
        # Set API endpoints
        if environment == "production":
            self.base_url = "https://pay.lipapayug.com/api/pay/bill"
        else:
            self.base_url = "http://dev.pay.lipapayug.com/api/pay/bill"
    
    def generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate MD5 signature for the API request
        
        Args:
            params: Dictionary of request parameters (excluding Sign)
            
        Returns:
            MD5 hash signature as string
        """
        # Create signature string by concatenating parameters in order
        signature_parts = []
        for key, value in params.items():
            signature_parts.append(f"{key}={value}")
        
        # Add private key at the end
        signature_string = "&".join(signature_parts) + f"&privateKey={self.private_key}"
        
        # Generate MD5 hash
        signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        
        return signature
    
    def get_prepaid_bill(self, phone_number: str, amount_cents: int, transaction_type: int = 1) -> Dict[str, Any]:
        """
        Get prepaid bill information using Airtel channel
        
        Args:
            phone_number: Phone number (TraderID) for the transaction
            amount_cents: Transaction amount in cents (e.g., 50000 for 500 shillings)
            transaction_type: Transaction type (1 = collections, 2 = disbursement)
            
        Returns:
            API response as dictionary
        """
        # Prepare request parameters
        params = {
            "Version": "v1.0",
            "MchID": self.merchant_id,
            "TimeStamp": int(time.time()),
            "Channel": 2,  # Airtel channel
            "TransactionType": transaction_type,
            "TraderID": phone_number,
            "Amount": amount_cents
        }
        
        # Generate signature
        signature = self.generate_signature(params)
        
        # Add signature to request
        request_data = params.copy()
        request_data["Sign"] = signature
        
        # Print request details for debugging
        print("=== Request Details ===")
        print(f"URL: {self.base_url}")
        print(f"Request Data: {json.dumps(request_data, indent=2)}")
        
        # Make API request
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                self.base_url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            print(f"\n=== Response Details ===")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            # Parse response
            if response.status_code == 200:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)}")
                return response_data
            else:
                print(f"Error Response: {response.text}")
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {
                "error": True,
                "message": f"Request failed: {str(e)}"
            }

def main():
    """
    Main function to demonstrate the API usage
    """
    # Configuration - Replace with your actual values
    MERCHANT_ID = 100001  # Replace with your merchant ID
    PRIVATE_KEY = "your_private_key_here"  # Replace with your actual private key
    ENVIRONMENT = "production"  # Change to "production" for live environment
    
    # Transaction details
    PHONE_NUMBER = "0759451067"  # Replace with actual phone number
    AMOUNT_CENTS = 50000  # 500 shillings in cents
    
    # Create API client
    api_client = LipaPayAPI(
        merchant_id=MERCHANT_ID,
        private_key=PRIVATE_KEY,
        environment=ENVIRONMENT
    )
    
    print("LipaPay Airtel Prepaid Bill API Call")
    print("=" * 40)
    
    # Make API call
    result = api_client.get_prepaid_bill(
        phone_number=PHONE_NUMBER,
        amount_cents=AMOUNT_CENTS,
        transaction_type=1  # Collections
    )
    
    print("\n=== Final Result ===")
    if result.get("error"):
        print("❌ API call failed!")
        print(f"Error: {result.get('message')}")
    else:
        print("✅ API call successful!")
        print("Bill information retrieved successfully.")

if __name__ == "__main__":
    main()