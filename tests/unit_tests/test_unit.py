import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from app.main import app

import werkzeug
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "3.0.0"

class TestApp(unittest.TestCase):

    def setUp(self):
        # Setting up mock values
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

        # Prepare auth header
        import base64
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.auth_header = {"Authorization": f"Basic {token}"}

    """
    Unit test case for valid balance for account

    This test case mocks valid values to the account -
    and verify if the behaviour is accurate.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_valid_account(self, mock_get):

        mock_get.return_value = {"Item": {
            "account_id": self.account_id,
            "current_balance": float(self.initial_balance),
            "first_name": "John",
            "last_name": "Doe"
        }}

        response = self.client.get(f"/balance/{self.account_id}",headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("current_balance", data)
        self.assertIsInstance(data["current_balance"], float)

    """
    Unit test case for invalid account (int)

    This test case validate the behaviour if an invalid -
    account number (int) is passed to the GET endpoint.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_invalid_account_number(self, mock_get):
        response = self.client.get("/balance/67899",headers=self.auth_header)
        self.assertEqual(response.status_code, 404)
    
    """
    Unit test case for invalid account (string)

    This test case validate the behaviour if an invalid -
    account number (string) is passed to the GET endpoint.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_invalid_account_string(self, mock_get):
        response = self.client.get("/balance/abbbdf",headers=self.auth_header)
        self.assertEqual(response.status_code, 400)
    
    """
    Unit test case for invalid account (alphanumeric)

    This test case validate the behaviour if an invalid -
    account number (alphanumeric) is passed to the GET endpoint.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_invalid_account_alphanumeric(self, mock_get):
        response = self.client.get("/balance/abb4bdf",headers=self.auth_header)
        self.assertEqual(response.status_code, 400)
    
    """
    Unit test case for invalid account (minus value)

    This test case validate the behaviour if an invalid -
    account number (minus value) is passed to the GET endpoint.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_invalid_account_minus(self, mock_get):
        response = self.client.get("/balance/-78908",headers=self.auth_header)
        self.assertEqual(response.status_code, 400)
    
    """
    Unit test case for invalid account (float)

    This test case validate the behaviour if an invalid -
    account number (float) is passed to the GET endpoint.

    :param mock_get: Mock values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_balance_invalid_account_float(self, mock_get):
        response = self.client.get("/balance/1067.789",headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for valid deposit POST endpoint

    This test case verify the behaviour if valid deposit value  -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    :param mock_update: Mock update values from Accounts table
    """
    @patch("app.main.table.update_item")
    @patch("app.main.table.get_item")
    def test_deposit_valid(self, mock_get, mock_update):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}
        mock_update.return_value = {"Attributes": {"account_id": self.account_id, "current_balance": float(self.initial_balance + 500)}}

        response = self.client.post("/deposit", json={"account_id": self.account_id, "amount": 500},headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        new_balance = float(response.get_json()["current_balance"])
        self.assertEqual(new_balance, self.initial_balance + 500)

    """
    Unit test case for invalid deposit (minus) POST endpoint

    This test case verify the behaviour if invalid deposit value (minus) -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_deposit_invalid_minus(self, mock_get):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}

        response = self.client.post("/deposit", json={"account_id": self.account_id, "amount": -1500},headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for invalid deposit (alphanumeric) POST endpoint

    This test case verify the behaviour if invalid deposit value (alphanumeric) -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_deposit_invalid_alphanumeric(self, mock_get):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}

        response = self.client.post("/deposit", json={"account_id": self.account_id, "amount": "32432f4242"},headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for invalid deposit (string) POST endpoint

    This test case verify the behaviour if invalid deposit value (string) -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_deposit_invalid_string(self, mock_get):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}

        response = self.client.post("/deposit", json={"account_id": self.account_id, "amount": "dsdsfdsfs"},headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for valid withdraw POST endpoint

    This test case verify the behaviour if valid withdraw amount -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    :param mock_update: Mock update values from Accounts table
    """
    @patch("app.main.table.update_item")
    @patch("app.main.table.get_item")
    def test_withdraw_valid(self, mock_get, mock_update):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}
        mock_update.return_value = {"Attributes": {"account_id": self.account_id, "current_balance": float(self.initial_balance - 500)}}

        response = self.client.post("/withdraw", json={"account_id": self.account_id, "amount": 500},headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        new_balance = float(response.get_json()["current_balance"])
        self.assertEqual(new_balance, self.initial_balance - 500)

    """
    Unit test case for invalid withdraw (minus) POST endpoint

    This test case verify the behaviour if invalid withdraw amount (minus) -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    :param mock_update: Mock update values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_withdraw_invalid_minus(self, mock_get):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}
        response = self.client.post("/withdraw", json={"account_id": self.account_id, "amount": -1000},headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for invalid withdraw (alphanumeric) POST endpoint

    This test case verify the behaviour if invalid withdraw amount (alphanumeric) -
    is passed to the POST endpoint.

    :param mock_get: Mock get values from Accounts table
    :param mock_update: Mock update values from Accounts table
    """
    @patch("app.main.table.get_item")
    def test_withdraw_invalid_alphanumeric(self, mock_get):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}
        response = self.client.post("/withdraw", json={"account_id": self.account_id, "amount": "500abc"},headers=self.auth_header)
        self.assertEqual(response.status_code, 400)

    """
    Unit test case for invalid withdraw (insufficient balance) POST endpoint

    This test case verify the behaviour if try to withdraw an amount which no longer exist -
    in the bank account.

    :param mock_get: Mock get values from Accounts table
    :param mock_update: Mock update values from Accounts table
    """
    @patch("app.main.table.update_item")
    @patch("app.main.table.get_item")
    def test_withdraw_insufficient_balance(self, mock_get, mock_update):
        mock_get.return_value = {"Item": {"account_id": self.account_id, "current_balance": float(self.initial_balance)}}
        
        # Simulate DynamoDB failing the conditional check
        error_response = {"Error": {"Code": "ConditionalCheckFailedException", "Message": "Conditional check failed"}}
        mock_update.side_effect = ClientError(error_response, "update_item")
        
        response = self.client.post(
            "/withdraw",
            json={"account_id": self.account_id, "amount": self.initial_balance + 100},
            headers=self.auth_header
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
