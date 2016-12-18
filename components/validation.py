import jsonschema

def _validate_json(data, schema):
    try:
        jsonschema.validate(data, schema)
        return True
    except:
        return False


def _validate_add_deposit(request):
    ticker_schema = {
        "type": "object",
        "properties": {
            "ticker": { "type": "string" },
            "amount": { "type": "number", "minimum": 0}
        },
        "required": ["ticker", "amount"]
    }

    schema = {
        "type": "object",
        "properties": {
            "date": { "type": "string" },
            "fonds": {
                "type": "array",
                "items": ticker_schema
            }
        },
        "required": ["date", "fonds"]
    }
    if not request.is_json:
        return False

    deposit_data = request.get_json()
    if not _validate_json(deposit_data, schema):
        return False

    return True

def _validate_delete_deposit(request):
    schema = {
        "type": "object",
        "properties": {
            "date": { "type": "string" },
            "tickers": {
                "type": "array",
                "items": { "type": "string" }
            }
        },
        "required": ["date", "tickers"]
    }
    if not request.is_json:
        return False

    deposit_data = request.get_json()
    if not _validate_json(deposit_data, schema):
        return False

    return True

def validate_deposit(request):
    if request.method == "DELETE":
        return _validate_delete_deposit(request)
    elif request.method == "PUT":
        return _validate_add_deposit(request)
    else:
        return False
