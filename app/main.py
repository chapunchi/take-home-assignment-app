import os
import boto3
import json
from flask import Flask, request, jsonify
from botocore.exceptions import ClientError
from decimal import Decimal, InvalidOperation
from app.utils.validator import validate_amount

# entrypoint of the web application
app = Flask(__name__)

# retrieve credentials from Secret Manager
def get_credentials():
    client = boto3.client("secretsmanager", region_name="ap-southeast-1")
    secret_name = "myapp/credentials"  # nosec B105
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret["username"], secret["password"]

USERNAME, PASSWORD = get_credentials()

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

@app.before_request
def require_auth():
    if request.endpoint == "health":
        return
    
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({"error": "Unauthorized"}), 401

# creates DynamoDB object with default region set to Singapore
dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION", "ap-southeast-1") 
)

# Set the DyanmoDB table to Accounts
table_name = os.getenv("DDB_TABLE", "Accounts")
table = dynamodb.Table(table_name)

"""
Health check endpoint where the Application Load Balancer -
will check if the application is reachable and healthy.
Without this route the Load Balancer health will be unstable -
it will continously try to restart the service.

:return: JSON status key with 'ok'
:rtype: dict
"""
@app.route("/")
def health():
    return {"status": "ok"}, 200

"""
GET endpoint to retrieve the balance of the -
bank account.

:param int account_id: The account number of bank account
:return: current balance of the requested account
:rtype: dict
:statuscode 200: Successfully retrieved account balance
:statuscode 400: Invalid account id
:statuscode 404: Account not found
:statuscode 500: Internal server error
"""
@app.route("/balance/<account_id>", methods=["GET"])
def get_balance(account_id):
    try:
        # Validate if account id is in digits
        if not account_id.isdigit():
            return jsonify({"error": f"Invalid account id : {account_id}"}), 400

        # Retrieve account id from DDB table
        response = table.get_item(Key={"account_id": account_id})

        # Validate if the account exists in the DDB table
        if "Item" not in response:
            return jsonify({"error": f"Account {account_id} not found"}), 404

        # If exists return the current balance of the requested account
        account = response["Item"]
        return jsonify({
            "current_balance": float(account["current_balance"])
        }), 200
    except ClientError as e:
        return jsonify({"error": str(e)}), 500


"""
POST endpoint to deposit money to the -
bank account.

:param request body:
    - account_id(int): Account id of the bank account
    - amount(float) : Amount to be deposited to account
:return: returns bank information with the current balance 
:rtype: dict
:statuscode 200: Successfully deposited to the account
:statuscode 400: Invalid payload/Invalid account id/Empty request body/Invalid amount
:statuscode 404: Account not found
:statuscode 500: Internal server error
"""
@app.route("/deposit", methods=["POST"])
def deposit():
    try:
        # Validates for payload
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Validates for empty requests
    if not data:
        return jsonify({"error": "Empty request body"}), 400
    
    # Retrieves account id
    account_id = data.get("account_id")

    # Validates if amount is float
    amount = validate_amount(data.get("amount"))

    # Validates if account id is valid
    if not account_id:
        return jsonify({"error": "Invalid account_id"}), 400
    
    # Validates if amount is valid
    if amount is None:
        return jsonify({"error": "Invalid amount"}), 400
                      
    try:
        # Validate if amount if less than zero
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    try:
        # Update the records in the DynamoDB
        response = table.update_item(
            Key={"account_id": account_id},
            UpdateExpression="SET current_balance = current_balance + :val",
            ExpressionAttributeValues={":val": amount},
            ConditionExpression="attribute_exists(account_id)",
            ReturnValues="ALL_NEW"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"error": f"Account {account_id} not found"}), 404
        else:
            return jsonify({"error": "Internal server error"}), 500
        
    return jsonify(response["Attributes"])


"""
POST endpoint to withdraw money from the -
bank account.

:param request body:
    - account_id(int): Account id of the bank account
    - amount(float) : Amount to be deposited to account
:return: returns bank information with the current balance 
:rtype: dict
:statuscode 200: Successfully withdrawn from account
:statuscode 400: Invalid payload/Invalid account id/Empty request body/Invalid amount
:statuscode 404: Account not found
:statuscode 500: Internal server error
"""
@app.route("/withdraw", methods=["POST"])
def withdraw():
    try:
        # Validates for payload
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Validates for empty requests
    if not data:
        return jsonify({"error": "Empty request body"}), 400

    account_id = data.get("account_id")
    raw_amount = data.get("amount")
    # daily_limit = data.get("daily_limit")
    # daily_amount_withdrawn = data.get("amount_withdrawn")
    # withdraw_flag = data.get("withdraw_flag")

    # Validates if account is valid
    if not account_id:
        return jsonify({"error": "Invalid account_id"}), 400

    try:
        # Validate if amount if less than zero
        amount = Decimal(str(raw_amount))
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    try:

        # Get current details from DDB
        account = table.get_item(
            Key={"account_id": account_id}
        ).get("Item")

        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        daily_limit = Decimal(str(account.get("daily_limit", 0)))
        daily_amount_withdrawn = Decimal(str(account.get("daily_amount_withdrawn", 0)))
        current_balance = Decimal(str(account.get("current_balance", 0)))

        if daily_amount_withdrawn +  amount > daily_limit:
            return jsonify({"error": "Daily limit exceeded"}), 400
        
        # Update the records in the DynamoDB
        response = table.update_item(
            Key={"account_id": account_id},
            UpdateExpression="SET current_balance = current_balance - :val, daily_amount_withdrawn=daily_amount_withdrawn + :val",
            ExpressionAttributeValues={":val": amount},
            ConditionExpression="attribute_exists(account_id) AND current_balance >= :val",
            ReturnValues="ALL_NEW"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"error": "Insufficient balance or account not found or daily limit exceeded"}), 404
        else:
            return jsonify({"error": "Internal server error"}), 500

    return jsonify(response["Attributes"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80) # nosec B104
