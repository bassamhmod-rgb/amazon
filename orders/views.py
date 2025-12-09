from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from stores.models import Store
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from products.models import Product
from accounts.models import Customer
from stores.models import StorePaymentMethod
from django.urls import reverse



import uuid
from django.core.files.storage import default_storage

@login_required
def checkout(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)

    customer_id = request.session.get("customer_id")
    customer = Customer.objects.filter(id=customer_id, store=store).first()
    if not customer:
        login_url = reverse("accounts:customer_login", kwargs={"store_slug": store.slug})
        return redirect(f"{login_url}?next=/orders/{store.slug}/checkout/")

    cart, _ = Cart.objects.get_or_create(user=request.user, store=store)
    if cart.items.count() == 0:
        return redirect("cart:cart_detail", store_slug=store.slug)

    payment_methods = StorePaymentMethod.objects.filter(store=store, is_active=True)

    checkout_data = request.session.get("checkout_data", {})
    error_message = None

    # ⭐ حساب الحد الأدنى المقترح للدفع الجزئي (مجرد إعلام)
    # ⭐ حساب الحد الأدنى المقترح للدفع الجزئي (مجرد إعلام)
    required_percent = store.payment_required_percentage or 0
    required_amount = 0

    if required_percent > 0:
        required_amount = (cart.get_total() * required_percent) / 100


    if request.method == "POST":

        new_name = request.POST.get("customer_name")
        new_phone = request.POST.get("customer_phone")
        address = request.POST.get("customer_address")
        note = request.POST.get("customer_note")
        payment_type = request.POST.get("payment_type")
        payment_method_id = request.POST.get("payment_method")

        proof_image_file = request.FILES.get("payment_proof_image")
        transaction_id = request.POST.get("payment_transaction_id", "").strip()

        # إلزامية الإثبات
        if payment_type in ["full", "partial"]:
            if not proof_image_file and not transaction_id:
                return render(request, "stores/checkout/checkout.html", {
                    "store": store,
                    "customer": customer,
                    "payment_methods": payment_methods,
                    "cart": cart,
                    "checkout_data": checkout_data,
                    "error_message": "يجب رفع صورة التحويل أو إدخال رقم العملية.",
                    "required_percent": required_percent,    # ⭐
                    "required_amount": required_amount,      # ⭐
                })

        # حفظ صورة الإثبات فوراً قبل الريدايركت
        proof_image_path = None
        if proof_image_file:
            filename = f"proofs/{uuid.uuid4()}_{proof_image_file.name}"
            proof_image_path = default_storage.save(filename, proof_image_file)

        # تحديث بيانات المستخدم
        if new_name:
            customer.name = new_name
        if new_phone:
            customer.phone = new_phone
        customer.save()

        # تخزين البيانات في الجلسة
        request.session["checkout_data"] = {
            "customer_name": customer.name,
            "customer_phone": customer.phone,
            "customer_address": address,
            "customer_note": note,
            "payment_method_id": payment_method_id,
            "payment_type": payment_type,
            "payment_transaction_id": transaction_id,
            "payment_proof_image_path": proof_image_path,
        }

        return redirect("orders:review_order", store_slug=store.slug)

    return render(request, "stores/checkout/checkout.html", {
        "store": store,
        "customer": customer,
        "payment_methods": payment_methods,
        "cart": cart,
        "checkout_data": checkout_data,

        # ⭐ إرسال المبلغ المقترح ليظهر فقط عند اختيار الدفع الجزئي
        "required_percent": required_percent,
        "required_amount": required_amount,
    })

@login_required
def customer_orders(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)

    # جلب الزبون من السيشن وليس من Django User
    customer_id = request.session.get("customer_id")
    customer = None

    if customer_id:
        customer = Customer.objects.filter(id=customer_id, store=store).first()

    # إذا ما في زبون مسجّل → رجّعه لتسجيل الدخول
    if not customer:
        return redirect("accounts:customer_login")

    # جلب طلبات الزبون
    orders = Order.objects.filter(customer=customer, store=store).order_by("-id")

    return render(request, "orders/customer_orders.html", {
        "store": store,
        "customer": customer,
        "orders": orders,
    })
@login_required
def order_detail(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)

    order = get_object_or_404(Order, id=order_id, store=store)

    # 🔥 أمان: الطلب لازم يكون لنفس الزبون عبر الـ session
    customer_id = request.session.get("customer_id")

    if customer_id != order.customer.id:
        return redirect("orders:customer_orders", store_slug=store.slug)

    items = order.items.all()

    return render(request, "orders/order_detail.html", {
        "store": store,
        "order": order,
        "items": items,
    })
@login_required
def review_order(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)

    # جلب الزبون
    customer_id = request.session.get("customer_id")
    customer = None
    if customer_id:
        customer = Customer.objects.filter(id=customer_id, store=store).first()

    if not customer:
        return redirect("accounts:customer_login")

    # جلب السلة
    cart, _ = Cart.objects.get_or_create(user=request.user, store=store)

    # بيانات checkout من session
    data = request.session.get("checkout_data")
    if not data:
        return redirect("orders:checkout", store_slug=store.slug)

    # ========= حل مشكلة ظهور None =========
    # إذا الحقول موجودة لكن فارغة أو None → استخدم قيم الزبون الحقيقية
    if not data.get("customer_name"):
        data["customer_name"] = customer.name

    if not data.get("customer_phone"):
        data["customer_phone"] = customer.phone
    # =======================================

    # جلب طريقة الدفع
    payment_method = None
    method_id = data.get("payment_method_id")

    if method_id:
        payment_method = StorePaymentMethod.objects.filter(
            id=method_id,
            store=store
        ).first()

    return render(request, "stores/checkout/review.html", {
        "store": store,
        "customer": customer,
        "data": data,
        "payment_method": payment_method,
        "cart": cart,
    })
import os
from django.core.files import File
from django.core.files.storage import default_storage

@login_required
def confirm_order(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)
    cart, _ = Cart.objects.get_or_create(user=request.user, store=store)

    # بيانات checkout من السيشن
    data = request.session.get("checkout_data")
    if not data:
        return redirect("orders:checkout", store_slug=store.slug)

    # الزبون
    customer_id = request.session.get("customer_id")
    customer = Customer.objects.filter(id=customer_id, store=store).first()
    if not customer:
        return redirect("accounts:customer_login")

    # طريقة الدفع
    method = None
    method_id = data.get("payment_method_id")
    if method_id:
        method = StorePaymentMethod.objects.filter(id=method_id, store=store).first()

    # ⭐ المسار المؤقّت الذي خزّناه بالـ checkout
    proof_image_path = data.get("payment_proof_image_path")
    transaction_id = data.get("payment_transaction_id")

    # 🟦 إنشاء الطلب
    order = Order.objects.create(
        store=store,
        customer=customer,
        user=store.owner,
        total=cart.total(),
        status="pending",

        shipping_address=data.get("customer_address", ""),
        payment_type=data.get("payment_type"),

        payment_method=method,
        payment_method_name=method.name if method else "",
        payment_recipient_name=method.recipient_name if method else "",
        payment_account_info=method.account_number if method else "",
        payment_additional_info=method.additional_info if method else "",
    )

    # ⭐ حفظ صورة أثبات الدفع إذا موجودة
    if proof_image_path:
        with default_storage.open(proof_image_path, "rb") as f:
            filename = os.path.basename(proof_image_path)
            order.payment_proof_image.save(filename, File(f), save=True)

        # حذف الصورة المؤقتة
        default_storage.delete(proof_image_path)

    # ⭐ حفظ رقم العملية
    if transaction_id:
        order.payment_transaction_id = transaction_id
        order.save()

    # نقل عناصر السلة
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
            item_note=item.item_note,
        )

    # تفريغ السلة
    cart.items.all().delete()

    # حذف بيانات الـ checkout
    if "checkout_data" in request.session:
        del request.session["checkout_data"]

    return redirect("orders:success", store_slug=store.slug, order_id=order.id)

@login_required
def order_success(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug)
    order = get_object_or_404(Order, id=order_id, store=store)

    return render(request, "stores/checkout/success.html", {
        "store": store,
        "order": order,
    })
