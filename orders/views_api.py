from django.db.models import F, Sum, DecimalField
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, OrderItem
from stores.models import Store
import json


# ================================
# API: جلب الطلبات غير المرسلة للمحاسبة
# ================================
@csrf_exempt
def merchant_orders_api(request, merchant_id):
    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse([], safe=False)

    orders = Order.objects.filter(
        store=store,
        status="confirmed",                 # ✅ فقط المؤكدة
        accounting_invoice_number__isnull=True
   
    ).order_by("created_at")

    result = []

    for order in orders:
        items = OrderItem.objects.filter(order=order)

        # حساب إجمالي الفاتورة من التفاصيل
        items_total = items.aggregate(
            sum=Sum(
                F("quantity") * F("price"),
                output_field=DecimalField()
            )
        )["sum"] or 0

        result.append({
            "order_id": order.id,
            "transaction_type": order.transaction_type,  # sale / purchase
            "items_total": float(items_total),
            "payment": float(order.payment or 0),
            "discount": float(order.discount or 0),      # ✅ الحسم
            "created_at": order.created_at.strftime("%Y-%m-%d"),
            "party_name": (
                order.customer.name if order.customer
                else order.supplier.name if order.supplier
                else ""
            ),
            "items": [
                {
                    "product": item.product.name if item.product else "",
                    "quantity": float(item.quantity),
                    "price": float(item.price),
                    "direction": item.direction
                }
                for item in items
            ]
        })

    return JsonResponse(result, safe=False)


# ================================
# API: حفظ رقم الفاتورة بعد النقل للمحاسبة
# ================================
@csrf_exempt
def set_invoice_number(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get("order_id")
        invoice_number = data.get("invoice_number")

        if not order_id or not invoice_number:
            return JsonResponse({"error": "Missing data"}, status=400)

        order = Order.objects.get(id=order_id)
        order.accounting_invoice_number = invoice_number
        order.save()

        return JsonResponse({"status": "ok"})

    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
