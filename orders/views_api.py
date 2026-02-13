from django.db.models import F, Sum, DecimalField
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, OrderItem
from stores.models import Store
from accounts.models import Customer, Supplier
from products.models import Product
import json
from django.utils.dateparse import parse_datetime
from django.utils import timezone

#تصدير
# ================================
# API: جلب الطلبات غير المرسلة للمحاسبة
# ================================
@csrf_exempt
def merchant_orders_api(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()
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
                    "buy_price": float(item.buy_price or 0),
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
#استيراد الفواتير

@csrf_exempt
def create_order_from_access(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        invoice_no = data.get("rkmfatora")  # ID من Access
        name = data.get("asm", "").strip()
        noaf = int(data.get("noaf"))
        created_at_str = data.get("tarek")
        amount = data.get("egmale", 0)
        document_kind = data.get("noam")
        payment = data.get("dfaa")
        discount = data.get("hsm", 0)

        # ✅ تحقق من المتجر
        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "store not found"}, status=404)

        # ✅ منع التكرار
        existing_order = Order.objects.filter(
            accounting_invoice_number=invoice_no,
            store=store
        ).first()

        if existing_order:
            return JsonResponse({
                "status": "exists",
                "order_id": existing_order.id
            })

        # ✅ تحديد نوع العملية
        transaction_type = "sale" if noaf == -1 else "purchase"

        customer = None
        supplier = None

        if noaf == -1:
            customer = Customer.objects.filter(store=store, name=name).first()
            if not customer:
                return JsonResponse({"error": "customer not found"})
        else:
            supplier = Supplier.objects.filter(store=store, name=name).first()
            if not supplier:
                return JsonResponse({"error": "supplier not found"})

        # ✅ معالجة التاريخ
        created_at = parse_datetime(created_at_str) if created_at_str else timezone.now()

        order = Order.objects.create(
            store=store,
            accounting_invoice_number=invoice_no,
            customer=customer,
            supplier=supplier,
            created_at=created_at,
            amount=amount,
            document_kind=document_kind,
            transaction_type=transaction_type,
            payment=payment,
            discount=discount,
            is_seen_by_store=True,
            status="confirmed",
        )

        return JsonResponse({
            "status": "created",
            "order_id": order.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def create_order_item_from_access(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        order_id = data.get("order_id")
        product_name = data.get("product_name", "").strip()

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return JsonResponse({"error": "order not found"})

        product = Product.objects.filter(store=order.store, name=product_name).first()
        if not product:
            return JsonResponse({"error": "product not found for store"})

        quantity = data.get("quantity", 1)
        direction = data.get("noaf")
        buy_price = data.get("buy_price", 0)
        price = data.get("price", 0)

        # ✅ منع تكرار نفس السطر
        existing_item = OrderItem.objects.filter(
            order=order,
            product=product,
            price=price,
            buy_price=buy_price,
            direction=direction
        ).first()

        if existing_item:
            return JsonResponse({"status": "exists"})

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            direction=direction,
            buy_price=buy_price,
            price=price,
        )

        return JsonResponse({"status": "created"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
