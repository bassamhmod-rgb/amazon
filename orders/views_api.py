from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from stores.models import Store


@csrf_exempt
def merchant_orders_api(request, merchant_id):
    """
    API: عرض جميع الطلبات الخاصة بتاجر معين عبر رقم معرفه (merchant_id)
    """

    # جلب المتجر اللي صاحبه هو التاجر المعطى
    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse({"error": "Merchant not found"}, status=404)

    # جلب الطلبات الخاصة بهذا المتجر فقط
    orders = Order.objects.filter(store=store).values(
        "id",
        "customer__name",
        "customer__phone",
        "total",
        "status",
        "created_at"
    )

    return JsonResponse({
        "merchant_id": merchant_id,
        "store_name": store.name,
        "orders": list(orders)
    }, safe=False)
