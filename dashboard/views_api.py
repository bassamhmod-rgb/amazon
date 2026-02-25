from decimal import Decimal
import json

from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

from stores.models import Store
from .models import Expense, ExpenseType, ExpenseReason


# ================================
# API: تصدير الصرفيات إلى الأكسس
# ================================
@csrf_exempt
def merchant_expenses_export_api(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    expenses = (
        Expense.objects.filter(store=store, access_id__isnull=True)
        .select_related("expense_type", "expense_reason")
        .order_by("id")
    )

    data = []
    for e in expenses:
        data.append({
            "id": e.id,
            "amount": float(e.amount or 0),
            "date": e.date.strftime("%Y-%m-%d"),
            "expense_type": e.expense_type.name if e.expense_type else "",
            "expense_reason": e.expense_reason.name if e.expense_reason else "",
            "notes": e.notes or "",
        })

    return JsonResponse({
        "merchant_id": merchant_id,
        "expenses": data
    })


# ================================
# API: تثبيت معرف الأكسس بعد التصدير
# ================================
@csrf_exempt
def merchant_expenses_confirm_api(request):
    try:
        data = json.loads(request.body)
        for item in data:
            Expense.objects.filter(
                id=int(item["expense_id"])
            ).update(
                access_id=int(item["access_id"])
            )

        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ================================
# API: استيراد الصرفيات من الأكسس
# ================================
@csrf_exempt
def create_expense_from_access(request, merchant_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        amount = data.get("amount", 0)
        date_str = data.get("date")
        expense_type_name = (data.get("expense_type") or "").strip()
        expense_reason_name = (
            data.get("expense_reason")
            or data.get("reason")
            or ""
        ).strip()
        notes = data.get("notes", "")

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        expense_type = None
        if expense_type_name:
            expense_type, _ = ExpenseType.objects.get_or_create(
                store=store,
                name=expense_type_name
            )

        expense_reason = None
        if expense_reason_name:
            expense_reason, _ = ExpenseReason.objects.get_or_create(
                store=store,
                name=expense_reason_name
            )

        date_only = parse_date(date_str) if date_str else None

        expense = Expense.objects.create(
            store=store,
            amount=Decimal(str(amount)) if amount not in ("", None) else Decimal("0"),
            date=date_only if date_only else timezone.now().date(),
            expense_type=expense_type,
            expense_reason=expense_reason,
            notes=notes or "",
        )

        return JsonResponse({
            "status": "created",
            "id": expense.id,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
