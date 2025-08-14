import os
from .models import db, Bill, BillItem
from .textract_utils import read_parsed_json
from app.celery_config import celery_app
from flask import current_app
from app.models import UserInsight, db
from app.insights import get_category_insight_from_llm

@celery_app.task(name="app.tasks.parse_json_async")
def parse_json_async(filename):
    # Use a fixed sample file path
    json_path = os.path.join(current_app.root_path, "..", "data", "sample_bill_1.json")
    json_path = os.path.abspath(json_path)

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
    bill_items = []
    for item in data.get("items", []):
        bill_item = BillItem(
            name=item["name"],
            price=item["price"],
            bill_id=bill.id
        )
        db.session.add(bill_item)
        bill_items.append({"name": item["name"], "price": item["price"]})

    db.session.commit()

    # ✅ Generate categorization insight via Ollama LLM
    category_insight = get_category_insight_from_llm(bill_items)
    if category_insight:
        db.session.add(UserInsight(
            user_id=None,  # Update with actual user_id if available
            bill_id=bill.id,
            insight_text=category_insight,
            insight_type="category_summary"
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
