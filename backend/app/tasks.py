import os
from .models import db, Bill, BillItem
from .textract_utils import read_parsed_json
from app.celery_config import celery_app
from flask import current_app
from app.models import UserInsight, db


@celery_app.task(name="app.tasks.parse_json_async")
def parse_json_async(filename):
    # Use a fixed sample file path
    json_path = os.path.join(current_app.root_path, "..", "data", "sample_output.json")
    json_path = os.path.abspath(json_path)

    # Debug check if file exists
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Sample JSON file not found: {json_path}")

    # Read and parse JSON
    data = read_parsed_json(json_path)

    # Save Bill
    bill = Bill(
        vendor=data.get("vendor"),
        total=data.get("total"),
        tax=data.get("tax"),
        currency=data.get("currency")
    )
    db.session.add(bill)
    db.session.flush()

    # Save Items
    for item in data.get("items", []):
        db.session.add(BillItem(
            name=item["name"],
            price=item["price"],
            bill_id=bill.id
        ))

    db.session.commit()
    return {"message": "Bill saved", "bill_id": bill.id}

def generate_per_bill_insight(user_id, bill_id, vendor, total):
    try:
        total = float(total)
    except:
        total = 0.0

    if total > 2000:
        msg = f"You spent ₹{total} at {vendor} — consider reviewing high-value purchases."
    elif total > 0:
        msg = f"You spent ₹{total} at {vendor}. Track your frequent vendors to spot patterns."
    else:
        msg = f"A bill was added with no total amount. Consider reviewing it manually."

    insight = UserInsight(
        user_id=user_id,
        bill_id=bill_id,
        insight_text=msg,
        insight_type='per_bill'
    )
    db.session.add(insight)
    db.session.commit()
