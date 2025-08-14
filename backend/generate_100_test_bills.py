import random
from datetime import datetime, timedelta
from app import create_app
from app.models import db, Bill, BillItem, UserInsight

app = create_app()

VENDORS = ['D-Mart', 'Big Bazaar', 'Reliance Fresh', 'Spencer’s', 'Nature’s Basket', 'KFC', 'McDonald’s']
ITEMS = ['Rice', 'Milk', 'Apples', 'Toothpaste', 'Soap', 'Chips', 'Oil', 'Chicken', 'Paneer']

def generate_random_bill(user_id, index):
    vendor = random.choice(VENDORS)
    date = datetime.now().date() - timedelta(days=random.randint(0, 30))
    total = round(random.uniform(100, 3000), 2)
    filename = f"bill_{index}.json"

    bill = Bill(
        user_id=user_id,
        date=date,
        vendor=vendor,
        total=total,
        filename=filename
    )
    db.session.add(bill)
    db.session.commit()

    # Add 2–4 items
    for _ in range(random.randint(2, 4)):
        item = BillItem(
            bill_id=bill.id,
            name=random.choice(ITEMS),
            quantity=random.randint(1, 5),
            price=round(random.uniform(20, 500), 2)
        )
        db.session.add(item)

    # Generate simple insight
    if total > 2000:
        insight_text = f"You spent ₹{total} at {vendor} — consider reviewing high-value purchases."
    else:
        insight_text = f"You spent ₹{total} at {vendor}. Track your frequent vendors to spot patterns."

    insight = UserInsight(
        user_id=user_id,
        bill_id=bill.id,
        insight_text=insight_text,
        insight_type='per_bill',
        generated_at=datetime.now()
    )
    db.session.add(insight)

with app.app_context():
    for i in range(100):
        generate_random_bill(user_id=1, index=i)
    db.session.commit()

print("✅ Successfully created 100 test bills and insights.")
