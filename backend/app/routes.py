import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import and_

from .textract_utils import read_parsed_json
from app.models import Bill, BillItem, db
from celery.result import AsyncResult
from celery import Celery
from app.celery_config import celery_app

bp = Blueprint('main', __name__)

# ✅ Health check route
@bp.route("/", methods=["GET"])
def index():
    return jsonify({"message": "BillWise API is running"}), 200

# ✅ Upload route (asynchronous)
@bp.route("/upload", methods=["POST"])
def upload_file():
    from app.tasks import parse_json_async
    try:
        print("Upload route hit!")
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        file.save(save_path)

        print(f"Saved file: {save_path}")
        task = parse_json_async.delay(filename)
        print(f"Started task: {task.id}")

        return jsonify({"task_id": task.id, "status": "processing"}), 202
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ✅ Celery task result
@bp.route("/result/<task_id>", methods=["GET"])
def get_task_result(task_id):
    result = AsyncResult(task_id, app=celery_app)
    if result.state == 'PENDING':
        return jsonify({"status": "Pending"}), 202
    elif result.state == 'SUCCESS':
        return jsonify({"status": "Completed", "result": result.result})
    else:
        return jsonify({"status": result.state}), 202

# ✅ Direct JSON test route
@bp.route("/parse-json", methods=["GET", "POST"])
def parse_json():
    if request.method == "GET":
        data = read_parsed_json("sample_output.json")
        return jsonify(data)

    elif request.method == "POST":
        data = request.get_json()
        if not data or "items" not in data:
            return jsonify({"error": "Invalid JSON or missing 'items'"}), 400

        new_bill = Bill(
            vendor=data.get("vendor", "Unknown"),
            tax=data.get("tax", "0.00"),
            total=data.get("total", "0.00"),
            currency=data.get("currency", "INR")
        )
        for item in data["items"]:
            bill_item = BillItem(
                name=item.get("name", "Unnamed"),
                price=item.get("price", 0.0)
            )
            new_bill.items.append(bill_item)

        db.session.add(new_bill)
        db.session.commit()
        return jsonify({"message": "Bill saved", "bill_id": new_bill.id}), 201

# ✅ Enhanced: List bills with pagination and filters
@bp.route("/bills", methods=["GET"])
def list_bills():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    vendor = request.args.get("vendor")
    min_total = request.args.get("min_total", type=float)
    max_total = request.args.get("max_total", type=float)

    query = Bill.query

    if vendor:
        query = query.filter(Bill.vendor.ilike(f"%{vendor}%"))
    if min_total is not None:
        query = query.filter(Bill.total >= min_total)
    if max_total is not None:
        query = query.filter(Bill.total <= max_total)

    pagination = query.order_by(Bill.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    bills = [{
        "id": bill.id,
        "vendor": bill.vendor,
        "total": bill.total,
        "tax": bill.tax,
        "currency": bill.currency,
        "created_at": bill.created_at.isoformat()
    } for bill in pagination.items]

    return jsonify({
        "bills": bills,
        "meta": {
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
            "per_page": pagination.per_page
        }
    })

# ✅ Get one bill by ID
@bp.route("/bills/<int:bill_id>", methods=["GET"])
def get_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    return jsonify({
        "id": bill.id,
        "vendor": bill.vendor,
        "total": bill.total,
        "tax": bill.tax,
        "currency": bill.currency,
        "created_at": bill.created_at.isoformat(),
        "items": [{
            "name": item.name,
            "price": item.price
        } for item in bill.items]
    })

# ✅ Update a bill
@bp.route("/bills/<int:bill_id>", methods=["PUT"])
def update_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    data = request.json
    bill.vendor = data.get("vendor", bill.vendor)
    bill.total = data.get("total", bill.total)
    bill.tax = data.get("tax", bill.tax)
    bill.currency = data.get("currency", bill.currency)
    #bill.date = data.get("date", bill.date)

    db.session.commit()
    return jsonify({"message": "Bill updated successfully"}), 200

# ✅ Delete a bill and its items
@bp.route("/bills/<int:bill_id>", methods=["DELETE"])
def delete_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    BillItem.query.filter_by(bill_id=bill_id).delete()
    db.session.delete(bill)
    db.session.commit()
    return jsonify({"message": "Bill and its items deleted successfully"}), 200

# ✅ Optional: handle 404 errors globally
@bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404
# ================================
# 📊 Insight Routes
# ================================

# 1. Top vendors by total spend
@bp.route("/insights/top-vendors", methods=["GET"])
def top_vendors():
    results = db.session.query(
        Bill.vendor,
        db.func.sum(Bill.total).label("total_spent")
    ).group_by(Bill.vendor).order_by(db.desc("total_spent")).limit(5).all()

    return jsonify([
        {"vendor": r[0], "total_spent": round(r[1], 2)} for r in results
    ])

# 2. Monthly spend trend
@bp.route("/insights/monthly-spend", methods=["GET"])
def monthly_spend():
    results = db.session.query(
        db.func.strftime("%Y-%m", Bill.created_at).label("month"),
        db.func.sum(Bill.total).label("total")
    ).group_by("month").order_by("month").all()

    return jsonify([
        {"month": r[0], "total_spent": round(r[1], 2)} for r in results
    ])

# 3. Most frequent items purchased
@bp.route("/insights/frequent-items", methods=["GET"])
def frequent_items():
    results = db.session.query(
        BillItem.name,
        db.func.count(BillItem.name).label("count")
    ).group_by(BillItem.name).order_by(db.desc("count")).limit(5).all()

    return jsonify([
        {"item": r[0], "count": r[1]} for r in results
    ])

# 4. Price trend for a specific item over time
@bp.route("/insights/price-trend/<item_name>", methods=["GET"])
def price_trend(item_name):
    results = db.session.query(
        db.func.strftime("%Y-%m", Bill.created_at).label("month"),
        db.func.avg(BillItem.price).label("avg_price")
    ).join(Bill).filter(BillItem.name.ilike(f"%{item_name}%")) \
     .group_by("month").order_by("month").all()

    return jsonify([
        {"month": r[0], "avg_price": round(r[1], 2)} for r in results
    ])
