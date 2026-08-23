from datetime import datetime


def format_amount(amount):
    amount = float(amount)
    if amount.is_integer():
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def format_conversion_message(
    amount, from_currency, to_currency, converted_amount, timestamp
):
    amount_text = format_amount(amount)
    if converted_amount < 0.01:
        converted_amount_text = "< 0.01"
    else:
        converted_amount_text = format_amount(converted_amount)

    return (
        f"`💰{amount_text} {from_currency} = {converted_amount_text} {to_currency}`"
        f"\n\n更新時間: {format_timestamp(timestamp)}"
    )
