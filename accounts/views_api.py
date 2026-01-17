from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import Customer
from stores.models import Store
from accounts.models import Supplier
from .models import PointsTransaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

#تصدير
# تصدير العملاء من المتجر إلى الأكسس
@csrf_exempt
def merchant_customers_api(request, merchant_id):
    """
    API: جلب عملاء تاجر معين (قراءة فقط)
    """

    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    customers = Customer.objects.filter(store=store).values(
        "id",        # ← هذا هو المفتاح الذهبي
        "name",
        "phone",
    )

    return JsonResponse({
        "merchant_id": merchant_id,
        "customers": list(customers)
    })


@csrf_exempt
def merchant_suppliers_api(request, merchant_id):
    """
    API: جلب موردي تاجر معين (قراءة فقط)
    """

    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    suppliers = Supplier.objects.filter(store=store).values(
        "name",
        "phone",
    )

    return JsonResponse({
        "merchant_id": merchant_id,
        "suppliers": list(suppliers)
    })

#نقل الكاش باك
@csrf_exempt
def merchant_points_export_api(request, merchant_id):
    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    points = PointsTransaction.objects.filter(
        customer__store=store,
        access_id__isnull=True
    ).select_related("customer")

    data = []
    for p in points:
        data.append({
            "id": p.id,  # 🔑 مهم نرجع نربط عليه
            "rkmamel_m": p.customer_id,
            "asm": p.customer.name,
            "amount": p.points,
            "trans_date": p.created_at.strftime("%Y-%m-%d"),
            "note": p.note or "",
        })

    return JsonResponse({
        "merchant_id": merchant_id,
        "points": data
    })
#ارجاع رقم السجل
@csrf_exempt
def merchant_points_confirm_api(request):
    import json

    data = json.loads(request.body)

    for item in data:
        PointsTransaction.objects.filter(
            id=int(item["points_id"])   # 🔴 تحويل صريح
        ).update(
            access_id=int(item["access_id"])
        )

    return JsonResponse({"status": "ok"})


## استيراد من البرنامج

# accounts/views_api.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
import json

from stores.models import Store
from accounts.models import Customer

@csrf_exempt
def create_customer_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        
        merchant_id = data.get("store")   # ← نفس منطق التصدير
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        if name == "أخطاء التسجيل":
            return JsonResponse({"status": "ignored"})
        if name == "مرتجع إلى مورد":
            return JsonResponse({"status": "ignored"})
        if name == "اتلاف":
            return JsonResponse({"status": "ignored"})
        
        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        # 🔑 نفس منطق merchant_customers_api
        store = Store.objects.filter(owner_id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if Customer.objects.filter(
            store=store
        ).filter(
            Q(name=name) | Q(phone=phone)
        ).exists():
            return JsonResponse({
                "status": "exists",
                "message": "الزبون موجود مسبقًا"
            })

        Customer.objects.create(
            store=store,
            name=name,
            phone=phone,
        )

        return JsonResponse({
            "status": "created",
            "message": "تم إنشاء الزبون بنجاح"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
import json

@csrf_exempt
def create_supplier_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        name = (data.get("name") or "").strip()
        phone = data.get("phone")
        if name == "أخطاء التسجيل":
            return JsonResponse({"status": "ignored"})
        if name == "فاتورة بدء":
            return JsonResponse({"status": "ignored"})
        if name == "مرتجع من زبون":
            return JsonResponse({"status": "ignored"})
        # توحيد phone
        if phone in ("", None):
            phone = None
        else:
            phone = str(phone).strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(owner_id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        # منع التكرار بالاسم فقط
        if Supplier.objects.filter(store=store, name=name).exists():
            return JsonResponse({"status": "exists"})

        Supplier.objects.create(
            store=store,
            name=name,
            phone=phone,
        )

        return JsonResponse({"status": "created"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# استيراد الكاش باك
from datetime import datetime
from django.utils.dateparse import parse_date
from datetime import datetime

@csrf_exempt
def create_cashback_from_access(request, merchant_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        rkmamel = data.get("rkmamel")  # رقم العميل بالبرنامج
        customer_name = (data.get("customer_name") or "").strip()
        amount = data.get("amount")
        trans_date = data.get("trans_date")
        note = data.get("note", "")

        if not customer_name or amount is None or not trans_date:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(owner_id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        customer = Customer.objects.filter(
            store=store,
            name=customer_name
        ).first()

        if not customer:
            return JsonResponse({
                "error": "العميل غير موجود بالمتجر",
                "customer_name": customer_name
            }, status=400)

        date_only = parse_date(trans_date)
        if not date_only:
            return JsonResponse({"error": "Invalid trans_date"}, status=400)

        created_at = datetime.combine(date_only, datetime.min.time())

        pt = PointsTransaction.objects.create(
            customer=customer,
            access_id=rkmamel,
            points=int(amount),
            created_at=created_at,
            note=note
        )

        # 🔑 نرجّع ID سجل النقاط
        return JsonResponse({
            "status": "created",
            "points_id": pt.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# لترجيع رقم العميل للأكسس
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
#للاشعارات
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
            "target_store_id": n.target_store_id,  # ⭐ مهم للإكسس
        })

    return JsonResponse(
        {"notifications": data},
        json_dumps_params={"ensure_ascii": False}
    )

#لاختبار من اكسس اذا الحساب فعال
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
#للتحديث
# views.py
from django.http import JsonResponse
from .models import AppUpdate

def check_update(request):
    app = AppUpdate.objects.get(app_name="alaman")
    return JsonResponse({
        "version": app.version.isoformat(),
        "prices_version": app.prices_version.isoformat(),
    })

