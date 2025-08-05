from backend.celery_worker import celery_app
from app.models import db, Bill, BillItem
from flask import current_app
from .textract_utils import read_parsed_json

@celery_app.task(name="parse_json_async")
def parse_json_async(filename):
    with current_app.app_context():
        data = read_parsed_json("sample_output.json")

        bill = Bill(
            vendor=data.get("vendor"),
            total=data.get("total"),
            tax=data.get("tax"),
            currency=data.get("currency")
        )
        db.session.add(bill)
        db.session.flush()

        for item in data.get("items", []):
            db.session.add(BillItem(
                name=item["name"],
                price=item["price"],
                bill_id=bill.id
            ))

        db.session.commit()
        return {"message": "Bill saved", "bill_id": bill.id}
