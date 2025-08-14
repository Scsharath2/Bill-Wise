import os
from datetime import datetime
from app import create_app
from app.models import db, Bill, BillItem, UserInsight

app = create_app()

DB_PATH = os.path.join("app", "billwise.db")

# Step 1: Delete DB
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("✅ Deleted old DB.")

with app.app_context():
    # Step 2: Recreate all tables
    db.create_all()
    print("✅ Recreated tables.")

    # Step 3: Add sample bill
    bill = Bill(
        user_id=1,
        date=datetime.now().date(),
        vendor="D-Mart",
        total=2350.0,
        filename="sample.json"
    )
    db.session.add(bill)
    db.session.commit()

    # Step 4: Add bill items
    items = [
        BillItem(bill_id=bill.id, name="Apples", quantity=2, price=120.0),
        BillItem(bill_id=bill.id, name="Rice", quantity=1, price=600.0)
    ]
    db.session.add_all(items)

    # Step 5: Generate insight
    msg = f"You spent ₹{bill.total} at {bill.vendor} — consider reviewing high-value purchases."
    insight = UserInsight(
        user_id=bill.user_id,
        bill_id=bill.id,
        insight_text=msg,
        insight_type="per_bill"
    )
    db.session.add(insight)
    db.session.commit()

    print("✅ Added sample bill, items, and insight.")

    # Step 6: Print insight
    insights = UserInsight.query.all()
    print("\n📊 Generated Insights:")
    for i in insights:
        print(f"- {i.insight_text} (on {i.generated_at})")
