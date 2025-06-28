**LipaPay Integration Guide for Deposits and Withdrawals**

---

**1. Overview**

This guide explains how to integrate LipaPay into your website or app to handle **Deposits**, **Withdrawals**, **Payment Status checks**, and **Balance/Statement queries**. It includes explanations, sample requests/responses, and visual flow diagrams to help you prepare for discussions with the LipaPay technical team.

---

**2. Key APIs**

| Operation                       | API Name                             |
| ------------------------------- | ------------------------------------ |
| Deposit (User pays to Merchant) | Unifiedorder                         |
| Withdrawal (Merchant pays User) | Unifiedorder (Disbursement type)     |
| Check Payment Result            | Payment Result Query                 |
| Receive Payment Notification    | Payment Result Callback Notification |
| Pre-check before creating Order | Prepaid Bill                         |
| Get Current Balance             | Get Balance                          |
| Get Transaction Statements      | Get Statement of Account             |

---

**3. Flow Diagrams**

**Deposit (User to Merchant)**

```mermaid
graph TD
    A[User clicks 'Deposit' on your website] --> B[Your server calls Unifiedorder API (collections type)]
    B --> C[LipaPay generates TransactionId]
    C --> D[LipaPay sends Payment URL / USSD Push to User's phone]
    D --> E[User completes payment on phone]
    E --> F[LipaPay sends Payment Result Callback Notification to your server]
    F --> G[Your server updates user wallet balance]
    G --> H[You display success message to user]
```

**Withdrawal (Merchant to User)**

```mermaid
graph TD
    A[User clicks 'Withdraw' on your website] --> B[Your server checks balance]
    B --> C[Your server calls Unifiedorder API (disbursement type)]
    C --> D[LipaPay processes payout to user phone]
    D --> E[LipaPay sends Payment Result Callback Notification to your server]
    E --> F[Your server updates wallet balance and shows confirmation]
```

---

**4. API Examples**

---

**Unifiedorder - Deposit (Collection)**

**Request:**

```json
{
  "Version": "v1.0",
  "MchID": 100001,
  "TimeStamp": 1694776093,
  "Channel": 1, // MTN or Airtel
  "TransactionType": 1, // collections = 1
  "TraderID": "0750000000",
  "Amount": 50000,
  "OutTradeNo": "DEPOSIT-20240617-00001",
  "Sign": "SIGNATURE"
}
```

**Response:**

```json
{
  "StatusCode": 200,
  "Data": {
    "TransactionId": "txn-uuid",
    "PayStatus": 0, // processing
    "Amount": 50000
  },
  "Succeeded": true
}
```

---

**Unifiedorder - Withdrawal (Disbursement)**

**Request:**

```json
{
  "Version": "v1.0",
  "MchID": 100001,
  "TimeStamp": 1694776093,
  "Channel": 1,
  "TransactionType": 2, // disbursement = 2
  "TraderID": "0750000000",
  "Amount": 50000,
  "OutTradeNo": "WITHDRAW-20240617-00001",
  "Sign": "SIGNATURE"
}
```

**Response:**

```json
{
  "StatusCode": 200,
  "Data": {
    "TransactionId": "txn-uuid",
    "PayStatus": 0
  },
  "Succeeded": true
}
```

---

**5. Payment Result Callback Notification**

After a payment is completed (deposit or withdrawal), LipaPay will **notify your server** asynchronously:

**Notification Example:**

```json
{
  "PayStatus": 1, // 1 = success, 2 = failed
  "PayTime": "2025-06-17 15:05:00",
  "OutTradeNo": "DEPOSIT-20240617-00001",
  "TransactionId": "txn-uuid",
  "Amount": 50000,
  "ActualPaymentAmount": 50000,
  "ActualCollectAmount": 49500,
  "PayerCharge": 0,
  "PayeeCharge": 500,
  "PayMessage": "SUCCESS",
  "Sign": "SIGNATURE"
}
```

Your server must respond:

```text
SUCCESS
```

---

**6. Payment Result Query (Check Status)**

You can actively query payment status:

**Request:**

```json
{
  "Version": "v1.0",
  "MchID": 100001,
  "TimeStamp": 1694776093,
  "OutTradeNo": "DEPOSIT-20240617-00001",
  "Sign": "SIGNATURE"
}
```

**Response:**

```json
{
  "StatusCode": 200,
  "Data": {
    "PayStatus": 1, // success
    "PayTime": "2025-06-17 15:05:00",
    "OutTradeNo": "DEPOSIT-20240617-00001",
    "TransactionId": "txn-uuid",
    "Amount": 50000
  },
  "Succeeded": true
}
```

---

**7. Get Balance**

**Request:**

```json
{
  "Version": "v1.0",
  "MchID": 100001,
  "TimeStamp": 1694776093,
  "Sign": "SIGNATURE"
}
```

**Response:**

```json
{
  "StatusCode": 200,
  "Data": {
    "Balance": 18910.0
  },
  "Succeeded": true
}
```

---

**8. Get Statement of Account**

**Request:**

```json
{
  "Version": "v1.0",
  "MchID": 100001,
  "TimeStamp": 1694776093,
  "StartTime": "20250615",
  "EndTime": "20250617",
  "Sign": "SIGNATURE"
}
```

**Response:**

```json
{
  "StatusCode": 200,
  "Data": {
    // List of transactions
  },
  "Succeeded": true
}
```

---

**9. Important Notes**

- Always verify `Sign` signatures using your private key.
- Respond **SUCCESS** for callbacks to avoid duplicate retries.
- Withdrawal and Deposit both use Unifiedorder, but the `TransactionType` value is what matters (1 or 2).
- Use **Payment Result Query** API to double-check status if callback delays occur.
- Get Balance helps ensure enough funds before sending withdrawals.
- Statement is useful for daily reconciliation.

---

**10. Summary**

| Action        | API/Flow                         |
| ------------- | -------------------------------- |
| Deposit       | Unifiedorder (type 1) + Callback |
| Withdrawal    | Unifiedorder (type 2) + Callback |
| Check Status  | Payment Result Query             |
| Check Balance | Get Balance                      |
| Daily Report  | Get Statement of Account         |

---

This guide should help you be well prepared to talk to LipaPay's technical team tomorrow. If you need, we can also add more **sample code (PHP, Node.js, Python)** to help speed up your integration!
