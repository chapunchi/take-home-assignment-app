def validate_amount(amount):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None

    if amount <= 0:
        return None

    return amount