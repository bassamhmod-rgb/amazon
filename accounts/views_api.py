from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import Customer
from stores.models import Store
from accounts.models import Supplier

#تصدير
@csrf_exempt
def merchant_customers_api(request, merchant_id):
    """
    API: جلب عملاء تاجر معين (قراءة فقط)
    """

    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    customers = Customer.objects.filter(store=store).values(
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

@csrf_exempt
def create_supplier_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        # نفس منطقكم: merchant_id → store
        store = Store.objects.filter(owner_id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if Supplier.objects.filter(
            store=store
        ).filter(
            Q(name=name) | Q(phone=phone)
        ).exists():
            return JsonResponse({"status": "exists"})

        Supplier.objects.create(
            store=store,
            name=name,
            phone=phone,
        )

        return JsonResponse({"status": "created"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
