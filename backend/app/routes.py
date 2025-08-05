import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from .textract_utils import read_parsed_json
from app.models import Bill, BillItem
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
    # ✅ Import here to avoid circular import
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

        from app.models import db
        db.session.add(new_bill)
        db.session.commit()

        return jsonify({"message": "Bill saved", "bill_id": new_bill.id}), 201

# ✅ List all bills
@bp.route("/bills", methods=["GET"])
def list_bills():
    bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return jsonify([{
        "id": bill.id,
        "vendor": bill.vendor,
        "total": bill.total,
        "tax": bill.tax,
        "currency": bill.currency,
        "created_at": bill.created_at.isoformat()
    } for bill in bills])

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

# ✅ Optional: handle 404 errors globally
@bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404
