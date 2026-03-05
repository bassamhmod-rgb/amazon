from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import Customer
from stores.models import Store
from accounts.models import Supplier
from .models import PointsTransaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.db.models import Q

#ط·ع¾ط·آµط·آ¯ط¸ظ¹ط·آ±
# ط·ع¾ط·آµط·آ¯ط¸ظ¹ط·آ± ط·آ§ط¸â€‍ط·آ¹ط¸â€¦ط¸â€‍ط·آ§ط·طŒ ط¸â€¦ط¸â€  ط·آ§ط¸â€‍ط¸â€¦ط·ع¾ط·آ¬ط·آ± ط·آ¥ط¸â€‍ط¸â€° ط·آ§ط¸â€‍ط·آ£ط¸ئ’ط·آ³ط·آ³
@csrf_exempt
def merchant_customers_api(request, merchant_id):
    """
    API: ط·آ¬ط¸â€‍ط·آ¨ ط·آ¹ط¸â€¦ط¸â€‍ط·آ§ط·طŒ ط·ع¾ط·آ§ط·آ¬ط·آ± ط¸â€¦ط·آ¹ط¸ظ¹ط¸â€  (ط¸â€ڑط·آ±ط·آ§ط·طŒط·آ© ط¸ظ¾ط¸â€ڑط·آ·)
    """

    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    customers = Customer.objects.filter(store=store).filter(
        Q(access_id__isnull=True) | Q(access_id=0) | Q(update_time__isnull=False)
    ).values(
        "id",        # -> ظ‡ط°ط§ ظ‡ظˆ ط§ظ„ظ…ظپطھط§ط­ ط§ظ„ط°ظ‡ط¨ظٹ
        "name",
        "phone",
        "access_id",
        "update_time",
    )

    return JsonResponse({
        "merchant_id": merchant_id,
        "customers": list(customers)
    })


@csrf_exempt
def merchant_suppliers_api(request, merchant_id):
    """
    API: ط·آ¬ط¸â€‍ط·آ¨ ط¸â€¦ط¸ث†ط·آ±ط·آ¯ط¸ظ¹ ط·ع¾ط·آ§ط·آ¬ط·آ± ط¸â€¦ط·آ¹ط¸ظ¹ط¸â€  (ط¸â€ڑط·آ±ط·آ§ط·طŒط·آ© ط¸ظ¾ط¸â€ڑط·آ·)
    """

    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    suppliers = Supplier.objects.filter(store=store).filter(
        Q(access_id__isnull=True) | Q(access_id=0) | Q(update_time__isnull=False)
    ).values(
        "id",
        "name",
        "phone",
        "access_id",
        "update_time",
    )

    return JsonResponse({
        "merchant_id": merchant_id,
        "suppliers": list(suppliers)
    })

#ط¸â€ ط¸â€ڑط¸â€‍ ط·آ§ط¸â€‍ط¸ئ’ط·آ§ط·آ´ ط·آ¨ط·آ§ط¸ئ’
@csrf_exempt
def merchant_points_export_api(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    points = PointsTransaction.objects.filter(customer__store=store).filter(
        Q(access_id__isnull=True) | Q(access_id=0) | Q(update_time__isnull=False)
    ).select_related("customer")

    data = []
    for p in points:
        data.append({
            "id": p.id,  # ظ‹ع؛â€‌â€ک ط¸â€¦ط¸â€،ط¸â€¦ ط¸â€ ط·آ±ط·آ¬ط·آ¹ ط¸â€ ط·آ±ط·آ¨ط·آ· ط·آ¹ط¸â€‍ط¸ظ¹ط¸â€،
            "rkmamel_m": p.customer_id,
            "asm": p.customer.name,
            "amount": p.points,
            "trans_date": p.created_at.strftime("%Y-%m-%d"),
            "note": p.note or "",
            "access_id": p.access_id,
            "update_time": p.update_time,
        })

    return JsonResponse({
        "merchant_id": merchant_id,
        "points": data
    })
#ط·آ§ط·آ±ط·آ¬ط·آ§ط·آ¹ ط·آ±ط¸â€ڑط¸â€¦ ط·آ§ط¸â€‍ط·آ³ط·آ¬ط¸â€‍
@csrf_exempt
def merchant_points_confirm_api(request):
    import json

    data = json.loads(request.body)

    for item in data:
        PointsTransaction.objects.filter(
            id=int(item["points_id"])   # ظ‹ع؛â€‌آ´ ط·ع¾ط·آ­ط¸ث†ط¸ظ¹ط¸â€‍ ط·آµط·آ±ط¸ظ¹ط·آ­
        ).update(
            access_id=int(item["access_id"]),
            update_time=None
        )

    return JsonResponse({"status": "ok"})
@csrf_exempt
def merchant_customers_confirm_api(request):
    import json

    data = json.loads(request.body)

    for item in data:
        Customer.objects.filter(
            id=int(item["customer_id"])
        ).update(
            access_id=int(item["access_id"]),
            update_time=None
        )

    return JsonResponse({"status": "ok"})


@csrf_exempt
def merchant_suppliers_confirm_api(request):
    import json

    data = json.loads(request.body)

    for item in data:
        Supplier.objects.filter(
            id=int(item["supplier_id"])
        ).update(
            access_id=int(item["access_id"]),
            update_time=None
        )

    return JsonResponse({"status": "ok"})

## ط·آ§ط·آ³ط·ع¾ط¸ظ¹ط·آ±ط·آ§ط·آ¯ ط¸â€¦ط¸â€  ط·آ§ط¸â€‍ط·آ¨ط·آ±ط¸â€ ط·آ§ط¸â€¦ط·آ¬

# accounts/views_api.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
import json

from stores.models import Store
from accounts.models import Customer

from django.db.models import Q

@csrf_exempt
def create_customer_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        access_id = data.get("access_id")
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if access_id in ("", None):
            access_id = None
        else:
            access_id = int(access_id)

        # تحديث صريح حسب access_id (رقم سجل أكسس) إذا كان موجودا
        if access_id is not None:
            by_access = Customer.objects.filter(store=store, access_id=access_id).first()
            if by_access:
                Customer.objects.filter(id=by_access.id, store=store).update(
                    name=name,
                    phone=phone,
                    update_time=None
                )
                return JsonResponse({
                    "status": "updated",
                    "customer_id": by_access.id,
                    "id": by_access.id,
                })

        # fallback: ابحث بالاسم أو الهاتف
        existing = Customer.objects.filter(
            store=store
        ).filter(
            Q(name=name) | Q(phone=phone)
        ).only("id", "name", "phone", "access_id").first()

        if existing:
            # نفس الرقم واسم مختلف -> نفس الرسالة القديمة
            if existing.phone == phone and existing.name != name:
                return JsonResponse({
                    "status": "exists",
                    "message": "رقم الموبايل مسجل باسم آخر لن يتم إكمال مزامنة الفواتير الا بعد حل المشكلة . يفضل التأكد من نقل العملاء من فورم العملاء اولا",
                    "existing_name": existing.name,
                    "id": existing.id,
                    "customer_id": existing.id,
                })

            update_data = {}
            if access_id is not None and existing.access_id in (None, 0, ""):
                update_data["access_id"] = access_id
            if existing.name != name:
                update_data["name"] = name
            if existing.phone != phone:
                update_data["phone"] = phone
            if update_data:
                update_data["update_time"] = None
                Customer.objects.filter(id=existing.id, store=store).update(**update_data)

            return JsonResponse({
                "status": "exists",
                "id": existing.id,
                "customer_id": existing.id,
            })

        customer = Customer.objects.create(
            store=store,
            access_id=access_id,
            name=name,
            phone=phone,
        )

        return JsonResponse({
            "status": "created",
            "message": "تم إنشاء الزبون بنجاح",
            "customer_id": customer.id,
            "id": customer.id,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def create_supplier_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        access_id = data.get("access_id")
        name = (data.get("name") or "").strip()
        phone = data.get("phone")

        if phone in ("", None):
            phone = None
        else:
            phone = str(phone).strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if access_id in ("", None):
            access_id = None
        else:
            access_id = int(access_id)

        # تحديث صريح حسب access_id (رقم سجل أكسس) إذا كان موجودا
        if access_id is not None:
            by_access = Supplier.objects.filter(store=store, access_id=access_id).first()
            if by_access:
                Supplier.objects.filter(id=by_access.id, store=store).update(
                    name=name,
                    phone=phone,
                    update_time=None
                )
                return JsonResponse({
                    "status": "updated",
                    "supplier_id": by_access.id,
                    "id": by_access.id,
                })

        # fallback: بالاسم
        existing = Supplier.objects.filter(store=store, name=name).first()
        if existing:
            update_data = {}
            if access_id is not None and existing.access_id in (None, 0, ""):
                update_data["access_id"] = access_id
            if existing.phone != phone:
                update_data["phone"] = phone
            if update_data:
                update_data["update_time"] = None
                Supplier.objects.filter(id=existing.id, store=store).update(**update_data)
            return JsonResponse({
                "status": "exists",
                "id": existing.id,
                "supplier_id": existing.id,
            })

        supplier = Supplier.objects.create(
            store=store,
            access_id=access_id,
            name=name,
            phone=phone,
        )

        return JsonResponse({
            "status": "created",
            "supplier_id": supplier.id,
            "id": supplier.id,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def create_cashback_from_access(request, merchant_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        rkmamel = data.get("rkmamel")  # ط·آ±ط¸â€ڑط¸â€¦ ط·آ§ط¸â€‍ط·آ¹ط¸â€¦ط¸ظ¹ط¸â€‍ ط·آ¨ط·آ§ط¸â€‍ط·آ¨ط·آ±ط¸â€ ط·آ§ط¸â€¦ط·آ¬
        access_id = data.get("access_id")  # ID ط³ط¬ظ„ ط§ظ„ط§ظƒط³ط³
        customer_name = (data.get("customer_name") or "").strip()
        amount = data.get("amount")
        trans_date = data.get("trans_date")
        note = data.get("note", "")

        if not customer_name or amount is None or not trans_date:
            return JsonResponse({"error": "ط·آ¨ط¸ظ¹ط·آ§ط¸â€ ط·آ§ط·ع¾ ط¸â€ ط·آ§ط¸â€ڑط·آµط·آ©"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        customer = Customer.objects.filter(
            store=store,
            name=customer_name
        ).first()

        if not customer:
            return JsonResponse({
                "error": "ط·آ§ط¸â€‍ط·آ¹ط¸â€¦ط¸ظ¹ط¸â€‍ ط·ط›ط¸ظ¹ط·آ± ط¸â€¦ط¸ث†ط·آ¬ط¸ث†ط·آ¯ ط·آ¨ط·آ§ط¸â€‍ط¸â€¦ط·ع¾ط·آ¬ط·آ±",
                "customer_name": customer_name
            }, status=400)

        date_only = parse_date(trans_date)
        if not date_only:
            return JsonResponse({"error": "Invalid trans_date"}, status=400)

        created_at = datetime.combine(date_only, datetime.min.time())
        # ط¯ط¹ظ… ظ‚ط¯ظٹظ…: ط¥ط°ط§ ظ…ط§ ظˆطµظ„ access_id ط§ط³طھط®ط¯ظ… rkmamel
        if access_id in ("", None):
            access_id = rkmamel

        pt = PointsTransaction.objects.create(
            customer=customer,
            access_id=int(access_id) if access_id not in ("", None) else None,
            points=int(amount),
            created_at=created_at,
            note=note
        )

        # ظ‹ع؛â€‌â€ک ط¸â€ ط·آ±ط·آ¬ط¸â€کط·آ¹ ID ط·آ³ط·آ¬ط¸â€‍ ط·آ§ط¸â€‍ط¸â€ ط¸â€ڑط·آ§ط·آ·
        return JsonResponse({
            "status": "created",
            "points_id": pt.id,
            "id": pt.id,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ط¸â€‍ط·ع¾ط·آ±ط·آ¬ط¸ظ¹ط·آ¹ ط·آ±ط¸â€ڑط¸â€¦ ط·آ§ط¸â€‍ط·آ¹ط¸â€¦ط¸ظ¹ط¸â€‍ ط¸â€‍ط¸â€‍ط·آ£ط¸ئ’ط·آ³ط·آ³
@csrf_exempt
def get_customer_id_for_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        access_row_id = data.get("access_row_id")

        if not access_row_id:
            return JsonResponse({"error": "Missing access_row_id"}, status=400)

        pt = PointsTransaction.objects.filter(
            access_id=access_row_id
        ).select_related("customer").first()

        if not pt or not pt.customer_id:
            return JsonResponse({"error": "Not found"}, status=404)

        return JsonResponse({
            "access_row_id": access_row_id,
            "customer_id": pt.customer_id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
#ط¸â€‍ط¸â€‍ط·آ§ط·آ´ط·آ¹ط·آ§ط·آ±ط·آ§ط·ع¾
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import SystemNotification, AccountingClient
from django.db.models import Q
from django.db import models
@csrf_exempt
def accounting_notifications(request):
    access_id = request.GET.get("access_id")

    if not access_id:
        return JsonResponse({"error": "access_id required"}, status=400)

    try:
        AccountingClient.objects.get(access_id=access_id)
    except AccountingClient.DoesNotExist:
        return JsonResponse({"error": "invalid access_id"}, status=403)

    now = timezone.now()

    notifications = (
        SystemNotification.objects
        .filter(channel__in=["accounting", "both"])
        .filter(
            Q(expires_at__isnull=True) |
            Q(expires_at__gt=now)
        )
        .order_by("id")
    )

    data = []

    for n in notifications:
        data.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "created_at": n.created_at.isoformat(),
            "target_store_id": n.target_store_id,  # أ¢آ­ع¯ ط¸â€¦ط¸â€،ط¸â€¦ ط¸â€‍ط¸â€‍ط·آ¥ط¸ئ’ط·آ³ط·آ³
        })

    return JsonResponse(
        {"notifications": data},
        json_dumps_params={"ensure_ascii": False}
    )

#ط¸â€‍ط·آ§ط·آ®ط·ع¾ط·آ¨ط·آ§ط·آ± ط¸â€¦ط¸â€  ط·آ§ط¸ئ’ط·آ³ط·آ³ ط·آ§ط·آ°ط·آ§ ط·آ§ط¸â€‍ط·آ­ط·آ³ط·آ§ط·آ¨ ط¸ظ¾ط·آ¹ط·آ§ط¸â€‍
from django.http import JsonResponse
from accounts.models import Store

def merchant_status(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()

    if not store:
        return JsonResponse(
            {"error": "Store not found"},
            status=404
        )

    return JsonResponse({
        "id": store.id,
        "is_active": store.is_active,
    })
#ط¸â€‍ط¸â€‍ط·ع¾ط·آ­ط·آ¯ط¸ظ¹ط·آ«
# views.py
from django.http import JsonResponse
from .models import AppUpdate

def check_update(request):
    app = AppUpdate.objects.get(app_name="alaman")
    return JsonResponse({
        "version": app.version,
        "prices_version": app.prices_version,
    })














