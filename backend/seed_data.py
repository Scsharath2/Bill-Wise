from app import create_app
from app.models import db, Bill, BillItem
from datetime import datetime
import random

app = create_app()
app.app_context().push()

# Clear old data
BillItem.query.delete()
Bill.query.delete()

vendors = ["D-Mart", "Star Bazaar", "Reliance Fresh", "Big Bazaar", "Mohan's Vegetables"]
items = ["Milk", "Bread", "Eggs", "Rice", "Tomato", "Onion", "Oil", "Sugar", "Tea", "Salt"]

# Add 10 sample bills (one per month)
for i in range(1, 11):
    bill = Bill(
        vendor=random.choice(vendors),
        tax=round(random.uniform(2, 10), 2),
        total=0.0,  # will be updated
        currency="INR",
        created_at=datetime(2024, i, 10)
    )

    total = 0.0
    for _ in range(4):  # 4 items per bill
        item_name = random.choice(items)
        price = round(random.uniform(20, 100), 2)
        total += price
        bill.items.append(BillItem(name=item_name, price=price))

    bill.total = round(total + bill.tax, 2)
    db.session.add(bill)

db.session.commit()
print("✅ Sample data inserted.")
