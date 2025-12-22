from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import Customer
from stores.models import Store
from accounts.models import Supplier


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
