import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


import unittest
from unittest.mock import patch
import json
from decimal import Decimal
from app.main import app
import base64

import werkzeug
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

"""
Integration test case for a customer to test below scenario,
1. Customer check the current balance
2. Decide to deposit money to the account
3. Withdraw money
4. Decides to make another withdraw but not enough money in account
5. Mistakenly inputs incorrect account 
6. Retrieve the current balance eventually

This test case mocks valid values to the account -
and verify if the behaviour is accurate.

:param mock_get: Mock values from Accounts table
"""
class TestFullIntegration(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.account_id = "12345"
        self.initial_balance = 2000.0

        # Mocking credentials
        self.username = "user"  # nosec B105
        self.password = "pass" # nosec B105

        patcher = patch("app.main.get_credentials", return_value=(self.username, self.password))
        self.mock_get_credentials = patcher.start()
        self.addCleanup(patcher.stop)

        from app import main
        main.USERNAME, main.PASSWORD = main.get_credentials()

        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.auth_header = {"Authorization": f"Basic {token}"}

    @patch("app.main.table.update_item")
    @patch("app.main.table.get_item")
    def test_account_flow(self, mock_get, mock_update):
        current_balance = {"value": float(self.initial_balance)}

        def mock_get_item(Key):
            return {
                "Item": {
                    "account_id": Key["account_id"],
                    "current_balance": current_balance["value"],
                    "first_name": "John",
                    "last_name": "Doe"
                }
            }

        def mock_update_item(Key, UpdateExpression, ExpressionAttributeValues, ConditionExpression, ReturnValues):
            val = ExpressionAttributeValues[":val"]

            if isinstance(val, Decimal):
                val = float(val)

            if ConditionExpression.endswith(">= :val") and val > current_balance["value"]:
                from botocore.exceptions import ClientError
                raise ClientError(
                    {"Error": {"Code": "ConditionalCheckFailedException"}}, 
                    "UpdateItem"
                )

            if " + :val" in UpdateExpression:
                current_balance["value"] += val
            else:
                current_balance["value"] -= val

            return {"Attributes": {"account_id": Key["account_id"], "current_balance": current_balance["value"]}}

        mock_get.side_effect = mock_get_item
        mock_update.side_effect = mock_update_item

        # 1. Check balance
        response = self.client.get(f"/balance/{self.account_id}", headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        balance = response.get_json()["current_balance"]
        print(f"Initial balance: {balance}")

        # 2. Deposit
        deposit_amount = 500
        response = self.client.post(
            "/deposit",
            data=json.dumps({"account_id": self.account_id, "amount": deposit_amount}),
            content_type="application/json",
            headers=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        balance = response.get_json()["current_balance"]
        print(f"Balance after deposit: {balance}")

        # 3. Withdraw
        withdraw_amount = 300
        response = self.client.post(
            "/withdraw",
            data=json.dumps({"account_id": self.account_id, "amount": withdraw_amount}),
            content_type="application/json",
            headers=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        balance = response.get_json()["current_balance"]
        print(f"Balance after withdrawal: {balance}")

        # 4. Attempt over-withdraw
        large_withdraw = balance + 1500
        response = self.client.post(
            "/withdraw",
            data=json.dumps({"account_id": self.account_id, "amount": large_withdraw}),
            content_type="application/json",
            headers=self.auth_header
        )
        self.assertEqual(response.status_code, 404)
        print(f"Attempt to withdraw {large_withdraw}: {response.get_json()['error']}")

        # 5. Invalid account access
        response = self.client.get("/balance/invalid123", headers=self.auth_header)
        self.assertEqual(response.status_code, 400)
        print("Invalid account access returned 400 as expected.")

        # 6. Retrieve final balance
        response = self.client.get(f"/balance/{self.account_id}", headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        final_balance = response.get_json()["current_balance"]
        print(f"Final balance: {final_balance}")


if __name__ == "__main__":
    unittest.main()
