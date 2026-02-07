
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum
from products.models import ProductDetails ,Product, ProductGallery
# --- ط§ط³طھظٹط±ط§ط¯ ط§ظ„ظ…ظˆط¯ظ„ط² ظ…ظ† ط§ظ„طھط·ط¨ظٹظ‚ط§طھ ط§ظ„ظ…ط®طھظ„ظپط© ---
from products.models import Category, Product
from products.forms import CategoryForm, ProductForm
from stores.models import Store
from orders.models import Order, OrderItem
from accounts.models import PointsTransaction

# 1. ط§ظ„ط²ط¨ظˆظ† ظ…ظˆط¬ظˆط¯ ط¨ظ€ accounts (ط­ط³ط¨ ظƒظ„ط§ظ…ظƒ)
from accounts.models import Customer
from django.contrib import messages
###
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from accounts.models import Supplier
from django.http import JsonResponse
# ط£ظ…ط§ ط¥ط°ط§ ظƒظ†طھ ظ†ط§ظ‚ظ„ظ‡ ظƒظ…ط§ظ† ظ„ظ€ accountsطŒ ط§ظ„ط؛ظٹ ط§ظ„ط³ط·ط± ط§ظ„ظ„ظٹ ظپظˆظ‚ ظˆط§ط³طھط®ط¯ظ… ظ‡ط§ط¯:
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
###

from django.db.models import (
    Sum, F, DecimalField, ExpressionWrapper,
    OuterRef, Subquery
)

from stores.models import Store
from products.models import Product, Category
from orders.models import OrderItem



@login_required
def dashboard_home(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    # ًں”´ ط¹ط¯ط¯ ط§ظ„ط·ظ„ط¨ط§طھ ط§ظ„ط¬ط¯ظٹط¯ط© (ط§ظ„ظ„ظٹ ظ„ط³ط§ ظ…ط§ ط´ط§ظپظ‡ط§ طµط§ط­ط¨ ط§ظ„ظ…طھط¬ط±)
    new_orders_count = Order.objects.filter(
        store=store,
        is_seen_by_store=False
    ).count()

    # ط¢ط®ط± ط§ظ„ط·ظ„ط¨ط§طھ (10 ظپظ‚ط·)
    orders = Order.objects.filter(store=store).order_by("-created_at")[:10]

    # ط¹ط¯ط¯ ط£ظˆ ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ظ†طھط¬ط§طھ
    products = Product.objects.filter(store=store)

    return render(request, "dashboard/dashboard_home.html", {
        "store": store,
        "orders": orders,
        "products": products,

        # ًں”¥ ظ…ظ‡ظ… ط¬ط¯ط§ظ‹ ظ„ظ„ظ€ sidebar 
        "new_orders_count": new_orders_count,
    })



# ًں”¹ ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ظ†طھط¬ط§طھ ظ…ط¹ ط¨ط­ط« + طھطµظپظٹط© + Pagination
@login_required
def products_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    products_qs = Product.objects.filter(store=store).order_by("-id")

    # ط§ظ„ط¨ط­ط« ط¨ط§ظ„ط§ط³ظ…
    q = request.GET.get("q")
    if q:
        products_qs = products_qs.filter(name__icontains=q)

    # ط§ظ„طھطµظپظٹط© ط­ط³ط¨ ط§ظ„ظپط¦ط© ط§ظ„ط£ط³ط§ط³ظٹط©
    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products_qs = products_qs.filter(category_id=category_id)

    # ط§ظ„طھطµظپظٹط© ط­ط³ط¨ ط§ظ„ظپط¦ط© ط§ظ„ظپط±ط¹ظٹط©
    sub_category_id = request.GET.get("category2")
    if sub_category_id and sub_category_id.isdigit():
        products_qs = products_qs.filter(category2_id=sub_category_id)

    # ط¬ظ„ط¨ ظƒظ„ ط§ظ„ظپط¦ط§طھ ط§ظ„ط®ط§طµط© ط¨ظ‡ط°ط§ ط§ظ„ظ…طھط¬ط±
    from products.models import Category
    categories = Category.objects.filter(store=store)

    # Pagination
    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "store": store,
        "page_obj": page_obj,
        "categories": categories,

        # ط§ظ„ط­ط§ظ„ظٹ ط§ظ„ظ…ط®طھط§ط±
        "current_category": int(category_id) if category_id and category_id.isdigit() else None,
        "current_sub_category": int(sub_category_id) if sub_category_id and sub_category_id.isdigit() else None,

        "products_qs": products_qs,
    }
    return render(request, "dashboard/products_list.html", context)

# ًں”¹ ط¥ط¶ط§ظپط© ظ…ظ†طھط¬ ط¬ط¯ظٹط¯
@login_required
def product_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, store=store)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()

            # ًں”¥ ط¥ط¶ط§ظپط© ط§ظ„ظ…ظˆط§طµظپط§طھ (ProductDetails)
            titles = request.POST.getlist("detail_title")
            values = request.POST.getlist("detail_value")

            for t, v in zip(titles, values):
                if t.strip() and v.strip():
                    ProductDetails.objects.create(
                        product=product,
                        title=t.strip(),
                        value=v.strip()
                    )

            # ًں–¼ï¸ڈ ط¥ط¶ط§ظپط© ط§ظ„طµظˆط± ط§ظ„ظپط±ط¹ظٹط© (ProductGallery)
            images = request.FILES.getlist("gallery_images")
            for img in images:
                ProductGallery.objects.create(
                    product=product,
                    image=img
                )

            return redirect("dashboard:products_list", store_slug=store.slug)

    else:
        form = ProductForm(store=store)

    return render(request, "dashboard/product_form.html", {
        "store": store,
        "form": form,
        "is_edit": False,
    })

# ًں”¹ طھط¹ط¯ظٹظ„ ظ…ظ†طھط¬
@login_required
def product_update(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product, store=store)
        if form.is_valid():
            product = form.save()

            # ًں”¥ طھط­ط¯ظٹط« ط§ظ„ظ…ظˆط§طµظپط§طھ (ظ†ط­ط°ظپ ط§ظ„ظ‚ط¯ظٹظ… ظˆظ†ط¶ظٹظپ ط§ظ„ط¬ط¯ظٹط¯)
            ProductDetails.objects.filter(product=product).delete()

            titles = request.POST.getlist("detail_title")
            values = request.POST.getlist("detail_value")

            for t, v in zip(titles, values):
                if t.strip() and v.strip():
                    ProductDetails.objects.create(
                        product=product,
                        title=t.strip(),
                        value=v.strip()
                    )

            # ًں–¼ï¸ڈ ط¥ط¶ط§ظپط© طµظˆط± ظپط±ط¹ظٹط© ط¬ط¯ظٹط¯ط© (ط¨ط¯ظˆظ† ط­ط°ظپ ط§ظ„ظ‚ط¯ظٹظ…ط©)
            images = request.FILES.getlist("gallery_images")
            for img in images:
                ProductGallery.objects.create(
                    product=product,
                    image=img
                )

            return redirect("dashboard:products_list", store_slug=store.slug)

    else:
        form = ProductForm(instance=product, store=store)

    return render(request, "dashboard/product_form.html", {
        "store": store,
        "form": form,
        "is_edit": True,
        "product": product,
    })
#ط­ط°ظپ طµظˆط±ط© ظ…ظ† ط§ظ„ظ…ط¹ط±ط¶
from django.http import HttpResponseForbidden
@login_required
def delete_gallery_image(request, image_id):
    image = get_object_or_404(ProductGallery, id=image_id)
    store = image.product.store

    if store.owner != request.user:
        return HttpResponseForbidden()

    product_id = image.product.id
    image.delete()

    return redirect("dashboard:product_update", store.slug, product_id)

# ًں”¹ ط­ط°ظپ ظ…ظ†طھط¬
@login_required
def product_delete(request, store_slug, product_id):
    store = get_object_or_404(
        Store,
        slug=store_slug,
        owner=request.user
    )

    product_qs = Product.objects.filter(
        id=product_id,
        store=store
    )

    if not product_qs.exists():
        messages.warning(
            request,
            "âڑ ï¸ڈ ط§ظ„ظ…ظ†طھط¬ ط؛ظٹط± ظ…ظˆط¬ظˆط¯ ط£ظˆ طھظ… ط­ط°ظپظ‡ ظ…ط³ط¨ظ‚ط§ظ‹"
        )
        return redirect("dashboard:products_list", store_slug=store.slug)

    if request.method == "POST":
        product_qs.delete()
        messages.success(
            request,
            "ًں—‘ï¸ڈ طھظ… ط­ط°ظپ ط§ظ„ظ…ظ†طھط¬ ط¨ظ†ط¬ط§ط­"
        )

    return redirect("dashboard:products_list", store_slug=store.slug)

#طھظپط§طµظٹظ„ ط§ظ„ظ…ظ†طھط¬
def product_detail(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    product = get_object_or_404(Product, id=product_id, store=store)

    return render(request, 'dashboard/product_detail.html', {
        'store': store,
        'product': product,
    })

#ط§ط¯ط§ط±ط© ط§ظ„ظپط¦ط§طھ
#ط¹ط±ط¶
def categories_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    categories = Category.objects.filter(store=store)

    return render(request, 'dashboard/categories_list.html', {
        'store': store,
        'categories': categories,   # â†گ طھط£ظƒط¯ ظ…ظ† ظ‡ط°ظٹ
    })

# ط§ط¶ط§ظپط©
@login_required
def add_category(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            return render(request, "dashboard/category_form.html", {
                "store": store,
                "error": "ط§ظ„ط±ط¬ط§ط، ط¥ط¯ط®ط§ظ„ ط§ط³ظ… ط§ظ„ظپط¦ط©",
            })

        # ط¥ظ†ط´ط§ط، ط§ظ„ظپط¦ط© ظˆط±ط¨ط·ظ‡ط§ طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ط¨ط§ظ„ظ…طھط¬ط±
        Category.objects.create(
            name=name,
            store=store
        )

        return redirect("dashboard:categories_list", store_slug=store.slug)

    return render(request, "dashboard/category_form.html", {
        "store": store
    })

#ط­ط°ظپ ظپط¦ط©
@login_required
# def delete_category(request, store_slug, category_id):
#     store = get_object_or_404(Store, slug=store_slug, owner=request.user)
#     category = get_object_or_404(Category, id=category_id, store=store)

#     # ط­ط°ظپ ظ…ط¨ط§ط´ط± ط¨ط¯ظˆظ† طµظپط­ط©
#     category.delete()
#     return redirect("dashboard:categories_list", store_slug=store.slug)
def delete_category(request, store_slug, category_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    category = get_object_or_404(Category, id=category_id, store=store)

    if request.method == "POST":
        category.delete()
        return redirect("dashboard:categories_list", store_slug=store.slug)

    return render(request, "dashboard/delete_category.html", {
        "store": store,
        "category": category
    })


#ط§ط¯ط§ط±ط© ط§ظ„ط·ظ„ط¨ط§طھ
#ط­ط°ظپ
@login_required
def delete_order(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    if request.method == "POST":
        order.delete()
        return redirect("dashboard:orders_list", store_slug=store.slug)

    return render(request, "dashboard/delete_order.html", {
        "store": store,
        "order": order,
    })


#طھظپط§طµظٹظ„ ط§ظ„ط·ظ„ط¨
@login_required
def order_detail_dashboard(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    # â­گ ط­ط³ط§ط¨ ط§ظ„ظ†ط³ط¨ط© ظˆط§ظ„ظ…ط¨ظ„ط؛ ط§ظ„ظ…ظ‚طھط±ظژط­ ظ„ظ„ط¯ظپط¹ ط§ظ„ظ…ط³ط¨ظ‚
    required_percent = store.payment_required_percentage or 0
    required_amount = 0

    if required_percent > 0:
        required_amount = (order.net_total * required_percent) / 100

    # ًں‘پï¸ڈ طھط¹ظ„ظٹظ… ط§ظ„ط·ظ„ط¨ ظƒظ…ظ‚ط±ظˆط،
    if not order.is_seen_by_store:
        order.is_seen_by_store = True
        order.save(update_fields=["is_seen_by_store"])

    # ===============================
    # ًںژپ ط­ط³ط§ط¨ ط§ظ„ظƒط§ط´ ط¨ط§ظƒ (ظ„ظ„ط¨ظٹط¹ ظپظ‚ط·)
    # ===============================
    total_profit = 0
    suggested_cashback = 0
    has_cashback = False

    if order.transaction_type == "sale" and order.customer:
        for item in order.items.all():
            buy_price = item.buy_price or 0
            total_profit += (item.price - buy_price) * item.quantity

        percent = store.cashback_percentage or 0
        suggested_cashback = (total_profit * percent) / 100 if total_profit > 0 else 0

        # ًں›،ï¸ڈ ظ‡ظ„ طھظ… طھط³ط¬ظٹظ„ ظƒط§ط´ ط¨ط§ظƒ ط³ط§ط¨ظ‚ظ‹ط§طں
        has_cashback = PointsTransaction.objects.filter(
            customer=order.customer,
            note=f"ظƒط§ط´ ط¨ط§ظƒ ظ…ظ† ط·ظ„ط¨ ط¨ظٹط¹ ط±ظ‚ظ… {order.id}"
        ).exists()

    return render(request, "dashboard/order_detail_dashboard.html", {
        "store": store,
        "order": order,

        # ط§ظ„ط¯ظپط¹ ط§ظ„ظ…ط³ط¨ظ‚
        "required_percent": required_percent,
        "required_amount": required_amount,

        # ط§ظ„ظƒط§ط´ ط¨ط§ظƒ
        "total_profit": total_profit,
        "suggested_cashback": suggested_cashback,
        "has_cashback": has_cashback,
    })

#طھط£ظƒظٹط¯ ط§ظ„ط·ظ„ط¨
@login_required
def confirm_order(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    # طھط£ظƒظٹط¯ ط§ظ„ط·ظ„ط¨
    order.status = "confirmed"
    order.save(update_fields=["status"])

    # ===============================
    # ًںژپ ط­ظپط¸ ط§ظ„ظƒط§ط´ ط¨ط§ظƒ (ظ„ظ„ط¨ظٹط¹ ظپظ‚ط·)
    # ===============================
    if order.transaction_type == "sale" and order.customer:

        # ظ…ظ†ط¹ ط§ظ„طھظƒط±ط§ط±
        exists = PointsTransaction.objects.filter(
            customer=order.customer,
            note=f"ظƒط§ط´ ط¨ط§ظƒ ظ…ظ† ط·ظ„ط¨ ط¨ظٹط¹ ط±ظ‚ظ… {order.id}"
        ).exists()

        if not exists:
            cashback_raw = request.POST.get("cashback_amount", "").strip()

            try:
                cashback_value = Decimal(cashback_raw) if cashback_raw != "" else Decimal("0")
            except:
                cashback_value = Decimal("0")

            if cashback_value > 0:
                PointsTransaction.objects.create(
                    customer=order.customer,
                    customer_name=str(order.customer),
                    points=cashback_value,
                    transaction_type="add",
                    note=f"ظƒط§ط´ ط¨ط§ظƒ ظ…ظ† ط·ظ„ط¨ ط¨ظٹط¹ ط±ظ‚ظ… {order.id}",
                )

    return redirect("dashboard:order_detail_dashboard", store_slug=store.slug, order_id=order.id)

#ط§ط¶ط§ظپط© ط·ظ„ط¨ ظ…ظ† ط§ظ„طھط§ط¬ط± ط¨ظٹط¹ ط§ظˆ ط´ط±ط§ط،



from decimal import Decimal, InvalidOperation

def _to_decimal(val, default="0"):
    try:
        # ط¥ط°ط§ ط§ظ„ظ‚ظٹظ…ط© Decimal ط£طµظ„ظ‹ط§
        if isinstance(val, Decimal):
            return val

        # ط¥ط°ط§ None
        if val is None:
            return Decimal(default)

        # ط¥ط°ط§ ط±ظ‚ظ… (int / float)
        if isinstance(val, (int, float)):
            return Decimal(str(val))

        # ط¥ط°ط§ ظ†طµ
        val = str(val).strip()
        if val == "":
            return Decimal(default)

        return Decimal(val)

    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


@login_required
def order_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":

        # 1) ظ†ظˆط¹ ط§ظ„ط¹ظ…ظ„ظٹط©
        transaction_type = request.POST.get("transaction_type", "sale")

        # 2) ط¬ظ„ط¨ ط§ظ„ط²ط¨ظˆظ† ط£ظˆ ط§ظ„ظ…ظˆط±ط¯
        customer = None
        supplier = None

        if transaction_type == "sale":
            customer_id = request.POST.get("customer_id")
            if customer_id and customer_id.isdigit():
                customer = Customer.objects.filter(id=customer_id, store=store).first()

        elif transaction_type == "purchase":
            supplier_id = request.POST.get("supplier_id")
            if supplier_id and supplier_id.isdigit():
                supplier = Supplier.objects.filter(id=supplier_id, store=store).first()

        if transaction_type == "sale" and not customer:
            messages.error(request, "ظٹط¬ط¨ ط§ط®طھظٹط§ط± ط²ط¨ظˆظ† ظ„ط¥طھظ…ط§ظ… ط¹ظ…ظ„ظٹط© ط§ظ„ط¨ظٹط¹.")
            return redirect("dashboard:order_create", store_slug=store.slug)

        if transaction_type == "purchase" and not supplier:
            messages.error(request, "ظٹط¬ط¨ ط§ط®طھظٹط§ط± ظ…ظˆط±ط¯ ظ„ط¥طھظ…ط§ظ… ط¹ظ…ظ„ظٹط© ط§ظ„ط´ط±ط§ط،.")
            return redirect("dashboard:order_create", store_slug=store.slug)

        status = "confirmed"

        # 3) ط¥ظ†ط´ط§ط، ط§ظ„ط·ظ„ط¨
        order = Order.objects.create(
            store=store,
            user=request.user,
            transaction_type=transaction_type,
            customer=customer if transaction_type == "sale" else None,
            supplier=supplier if transaction_type == "purchase" else None,
            discount=request.POST.get("discount", 0),
            payment=request.POST.get("payment", 0),
            status=status,
        )

        # 4) ط¹ظ†ط§طµط± ط§ظ„ط·ظ„ط¨
        products = request.POST.getlist("product_id[]")
        prices   = request.POST.getlist("price[]")
        qtys     = request.POST.getlist("quantity[]")

        total_profit = Decimal("0")  # ظپظ‚ط· ظ„ظ„ط¨ظٹط¹

        for i in range(len(products)):
            product = Product.objects.filter(id=products[i], store=store).first()
            if not product:
                continue

            price = _to_decimal(prices[i])
            qty   = _to_decimal(qtys[i])

            if transaction_type == "sale":
                buy_price = _to_decimal(product.get_avg_buy_price())

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=price,
                    quantity=qty,
                    direction=-1,
                    buy_price=buy_price,
                )

                # ط§ظ„ط±ط¨ط­ = (ط³ط¹ط± ط§ظ„ط¨ظٹط¹ - ط³ط¹ط± ط§ظ„ط´ط±ط§ط،) * ط§ظ„ظƒظ…ظٹط©
                total_profit += (price - buy_price) * qty

            else:  # purchase
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=price,
                    quantity=qty,
                    direction=1,
                    buy_price=price,
                )

        # 5) â­گ ط¥ط¶ط§ظپط© ط§ظ„ظ†ظ‚ط§ط· (ط§ظ„ظƒط§ط´ ط¨ط§ظƒ) â€” ظپظ‚ط· ط¹ظ†ط¯ ط§ظ„ط¨ظٹط¹
        if transaction_type == "sale" and customer:

            cashback_manual = (request.POST.get("cashback_amount") or "").strip()

            try:
                if cashback_manual != "":
                    points_value = Decimal(cashback_manual)
                else:
                    percent = store.cashback_percentage or Decimal("0")
                    points_value = (total_profit * percent) / Decimal("100")
            except InvalidOperation:
                points_value = Decimal("0")

            # ط­ظ…ط§ظٹط©
            if points_value < 0:
                points_value = Decimal("0")

            if points_value > 0:
                PointsTransaction.objects.create(
                    customer=customer,
                    customer_name=str(customer),
                    points=points_value,
                    transaction_type="add",
                    note=f"ظƒط§ط´ ط¨ط§ظƒ ظ…ظ† ط·ظ„ط¨ ط¨ظٹط¹ ط±ظ‚ظ… {order.id}",
                )

        return redirect("dashboard:orders_list", store_slug=store.slug)

    return render(request, "dashboard/order_create.html", {
        "store": store
    })

# طھط¹ط¯ظٹظ„ ط§ظ„ط·ظ„ط¨ (ط¨ظٹط¹ + ط´ط±ط§ط،) â€” ط¨ط¯ظˆظ† ط­ظ‚ظˆظ„ supplier
@login_required
def order_update(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)
    new_orders_count = Order.objects.filter(store=store, is_seen_by_store=False).count()

    if request.method == "POST":

        # ًںں¦ 1) ظ†ظˆط¹ ط§ظ„ط¹ظ…ظ„ظٹط© (ط¨ظٹط¹ / ط´ط±ط§ط،)
        transaction_type = request.POST.get("transaction_type", "sale")
        order.transaction_type = transaction_type

        # ًںں¦ 2) ط®طµظ… ظˆط¯ظپط¹ (â‌Œ ط¨ط¯ظˆظ† total)
        order.discount = request.POST.get("discount", 0)
        order.payment = request.POST.get("payment", 0)

        # ًںں¦ 3) ط²ط¨ظˆظ† ط£ظˆ ظ…ظˆط±ط¯ (ط­ط³ط¨ ط§ظ„ظ†ظˆط¹)
        if transaction_type == "sale":
            customer_id = request.POST.get("customer_id")
            order.customer_id = customer_id if customer_id else None
            order.supplier = None  # â†گ ظ…ظ‡ظ… ط¬ط¯ط§ظ‹

        else:  # purchase
            supplier_id = request.POST.get("supplier_id")
            order.supplier_id = supplier_id if supplier_id else None
            order.customer = None  # â†گ ظ…ظ‡ظ… ط¬ط¯ط§ظ‹

        order.save()

        # ًںں¦ 4) ط­ط°ظپ ط§ظ„ط¹ظ†ط§طµط± ط§ظ„ظ‚ط¯ظٹظ…ط©
        order.items.all().delete()

        # ًںں¦ 5) ط¥ط¶ط§ظپط© ط§ظ„ط¹ظ†ط§طµط± ط§ظ„ط¬ط¯ظٹط¯ط©
        products = request.POST.getlist("product_id[]")
        prices   = request.POST.getlist("price[]")
        qtys     = request.POST.getlist("quantity[]")

        for i in range(len(products)):

            product = Product.objects.filter(id=products[i]).first()
            if not product:
                continue

            price = float(prices[i])
            qty = float(qtys[i])

            # ط¨ظٹط¹ ط£ظˆ ط´ط±ط§ط،طں
            direction = -1 if transaction_type == "sale" else 1

            # snapshot
            if transaction_type == "sale":
                buy_price = product.buy_price  # snapshot ظ„ظ„ط±ط¨ط­
            else:
                buy_price = price  # snapshot ظ„طھظƒظ„ظپط© ط§ظ„ط´ط±ط§ط،

            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=qty,
                direction=direction,
                buy_price=buy_price,
            )

        return redirect("dashboard:orders_list", store.slug)

    return render(request, "dashboard/order_update.html", {
        "store": store,
        "order": order,
        "new_orders_count": new_orders_count,
    })

#ظپظ„طھط±ط© ط·ظ„ط¨ط§طھ
#ط¨ط§ظ„ط­ط§ظ„ط©
#ط¨ط±ظ‚ظ… ط§ظ„ط·ظ„ط¨
# ظ‚ط§ط¦ظ…ط© ط§ظ„ط·ظ„ط¨ط§طھ
@login_required
def orders_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    status = request.GET.get("status", "")
    order_id = request.GET.get("order_id", "")

    # ظƒظ„ ط·ظ„ط¨ط§طھ ط§ظ„ظ…طھط¬ط±
    orders = Order.objects.filter(store=store)

    # ظپظ„طھط±ط© ط­ط³ط¨ ط§ظ„ط­ط§ظ„ط©
    if status:
        orders = orders.filter(status=status)

    # ظپظ„طھط±ط© ط­ط³ط¨ ط±ظ‚ظ… ط§ظ„ط·ظ„ط¨
    if order_id:
        orders = orders.filter(id=order_id)

    # طھط±طھظٹط¨ ظ…ظ† ط§ظ„ط£ط­ط¯ط« ظ„ظ„ط£ظ‚ط¯ظ…
    orders = orders.order_by("-created_at")

    # ًںں¢ ط¹ط¯ط¯ ط§ظ„ط·ظ„ط¨ط§طھ ط§ظ„ط¬ط¯ظٹط¯ط© (ظ„ط³ظ‘ط§ is_seen_by_store = False)
    new_orders_count = Order.objects.filter(
        store=store,
        is_seen_by_store=False
    ).count()

    context = {
        "store": store,
        "orders": orders,
        "current_status": status,
        "current_id": order_id,
        "new_orders_count": new_orders_count,  # ظ…ظ‡ظ… ظ„ظ„ظ€ sidebar
    }

    # ًں”´ ط§ظ†طھط¨ظ‡: ظ‡ظˆظ† ظ…ط§ ط¹ظ… ظ†ط؛ظٹظ‘ط± is_seen_by_store
    # ط§ظ„ط·ظ„ط¨ ط¨ظٹطھط¹ظ„ظ‘ظژظ… ظƒظ…ظ‚ط±ظˆط، ظ„ظ…ط§ طھظپطھط­ طµظپط­ط© طھظپط§طµظٹظ„ ط§ظ„ط·ظ„ط¨ (ظ…ظ†ط³ظˆظ‘ظٹظ‡ط§ ط¨ط¹ط¯ظٹظ†)

    return render(request, "dashboard/orders_list.html", context)
# ط§ظ„ط¨ط­ط« ط¨ط§ط³ظ…ط§ط، ط§ظ„ظ…ظ†طھط¬ط§طھ

def search_products(request, store_slug):
    q = request.GET.get("q", "")
    products = Product.objects.filter(store__slug=store_slug, name__icontains=q)

    results = [
        {"id": p.id, "name": p.name, "price": float(p.price)}
        for p in products
    ]

    return JsonResponse({"results": results})
#ط§ظ„ط¨ط­ط« ط¨ط§ط³ظ…ط§ط، ط§ظ„ظ…ط³طھط®ط¯ظ…ظٹظ†

def search_customers(request, store_slug):
    q = request.GET.get("q", "")
    
    # ط¬ظ„ط¨ ط²ط¨ط§ط¦ظ† ظ‡ط°ط§ ط§ظ„ظ…طھط¬ط± ظپظ‚ط·
    customers = Customer.objects.filter(store__slug=store_slug, name__icontains=q) | Customer.objects.filter(
        store__slug=store_slug,
        phone__icontains=q
    )

    results = [
        {"id": c.id, "name": c.name, "phone": c.phone}
        for c in customers
    ]

    return JsonResponse({"results": results})
# ًں”چ ط¨ط­ط« ط§ظ„ظ…ظˆط±ط¯ظٹظ†


def search_suppliers(request, store_slug):
    q = request.GET.get("q", "").strip()

    # ط¬ظ„ط¨ ط§ظ„ظ…ظˆط±ط¯ظٹظ† ط­ط³ط¨ ط§ظ„ظ…طھط¬ط± ظˆط§ظ„ظƒظ„ظ…ط© ط§ظ„ظ…ظƒطھظˆط¨ط©
    suppliers = Supplier.objects.filter(
        store__slug=store_slug
    ).filter(
        Q(name__icontains=q) | Q(phone__icontains=q)
    )

    results = [
        {
            "id": s.id,
            "name": s.name,
            "phone": s.phone or "",
        }
        for s in suppliers
    ]

    return JsonResponse({"results": results})
#ط§ط´ط¹ط§ط±ط§طھ ط§ظ„ظ‚ط¨ط¶ ظˆ ط§ظ„طµط±ظپ
#ط§ظ„ط¹ط±ط¶
@login_required
def notices_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    notices = Order.objects.filter(
        store=store,
        document_kind=2
    )

    # ===== ظپظ„طھط± ط§ظ„ظ†ظˆط¹ (ظ‚ط¨ط¶ / طµط±ظپ) =====
    transaction_type = request.GET.get("transaction_type")
    normalized_type = None
    if transaction_type:
        if transaction_type in ["in", "sale", "-1"]:
            normalized_type = "sale"
        elif transaction_type in ["out", "purchase", "1"]:
            normalized_type = "purchase"
        else:
            normalized_type = transaction_type

    if normalized_type:
        notices = notices.filter(transaction_type=normalized_type)

    # ===== ???????? ?????????? ???? ?????????? =====
    keyword = (request.GET.get("keyword") or "").strip()

    if keyword:
        if normalized_type == "sale":
            # ?????? ??? ??????????
            notices = notices.filter(customer__name__icontains=keyword)
        elif normalized_type == "purchase":
            # ?????? ??? ????????????
            notices = notices.filter(supplier__name__icontains=keyword)

    notices = notices.order_by("-created_at")

    return render(request, "dashboard/notices_list.html", {
        "store": store,
        "notices": notices,
        "current_type": transaction_type,
        "current_keyword": keyword,
    })
#ظ„ظ„ظپظ„طھط±ط©
@login_required
def notices_filter(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    notices = Order.objects.filter(
        store=store,
        document_kind=2
    )

    transaction_type = request.GET.get("transaction_type")
    customer_id = request.GET.get("customer_id")
    supplier_id = request.GET.get("supplier_id")

    if transaction_type:
        if transaction_type == "in":
            notices = notices.filter(transaction_type="sale")
        elif transaction_type == "out":
            notices = notices.filter(transaction_type="purchase")
        else:
            notices = notices.filter(transaction_type=transaction_type)


    if customer_id and customer_id.isdigit():
        notices = notices.filter(customer_id=customer_id)

    if supplier_id and supplier_id.isdigit():
        notices = notices.filter(supplier_id=supplier_id)

    notices = notices.order_by("-created_at")

    return render(request, "dashboard/partials/notices_rows.html", {
        "notices": notices
    })


#ط§ط¶ط§ظپط© ط§ط´ط؛ط§ط±


from decimal import Decimal, InvalidOperation

@login_required
@login_required
def notice_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        # ===== نوع العملية =====
        transaction_type = request.POST.get("transaction_type")

        if transaction_type not in ["sale", "purchase"]:
            messages.error(request, "نوع الإشعار غير صالح.")
            return redirect("dashboard:notice_create", store_slug=store.slug)

        # ===== الطرف =====
        customer = None
        supplier = None

        if transaction_type == "sale":
            customer_id = request.POST.get("customer_id")
            if customer_id and customer_id.isdigit():
                customer = Customer.objects.filter(id=customer_id, store=store).first()

            if not customer:
                messages.error(request, "يجب اختيار زبون لإشعار القبض.")
                return redirect("dashboard:notice_create", store_slug=store.slug)

        if transaction_type == "purchase":
            supplier_id = request.POST.get("supplier_id")
            if supplier_id and supplier_id.isdigit():
                supplier = Supplier.objects.filter(id=supplier_id, store=store).first()

            if not supplier:
                messages.error(request, "يجب اختيار مورد لإشعار الصرف.")
                return redirect("dashboard:notice_create", store_slug=store.slug)

        # ===== المبالغ =====
        try:
            amount_raw = request.POST.get("amount")
            payment_raw = request.POST.get("payment")
            amount = Decimal(amount_raw) if amount_raw not in [None, ""] else Decimal("0")
            payment = Decimal(payment_raw) if payment_raw not in [None, ""] else Decimal("0")
        except InvalidOperation:
            messages.error(request, "قيمة المبلغ غير صحيحة.")
            return redirect("dashboard:notice_create", store_slug=store.slug)

        if amount < 0 or payment < 0:
            messages.error(request, "القيم يجب أن تكون موجبة.")
            return redirect("dashboard:notice_create", store_slug=store.slug)

        if amount == 0 and payment == 0:
            messages.error(request, "يرجى إدخال دفعة أو مبلغ.")
            return redirect("dashboard:notice_create", store_slug=store.slug)

        # ===== إنشاء الإشعار =====
        Order.objects.create(
            store=store,
            user=request.user,
            document_kind=2,
            transaction_type=transaction_type,
            customer=customer,
            supplier=supplier,
            amount=amount,
            discount=Decimal("0"),
            payment=payment,
            status="confirmed",
        )

        messages.success(request, "تم إنشاء الإشعار بنجاح.")
        return redirect("dashboard:notices_list", store_slug=store.slug)

    return render(request, "dashboard/notice_create.html", {
        "store": store
    })


@login_required
def notice_delete(request, store_slug, notice_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    notice = get_object_or_404(
        Order,
        id=notice_id,
        store=store,
        document_kind=2
    )

    if request.method == "POST":
        notice.delete()
        messages.success(request, "تم حذف الإشعار.")

    return redirect("dashboard:notices_list", store_slug=store.slug)


@login_required
def suppliers_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    suppliers = Supplier.objects.filter(store=store).order_by("-id")

    return render(request, "dashboard/suppliers_list.html", {
        "store": store,
        "suppliers": suppliers,
    })


@login_required
def customers_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    customers = Customer.objects.filter(store=store)

    return render(request, "dashboard/customers_list.html", {
        "store": store,
        "customers": customers,
    })


@login_required
def customer_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        exists = Customer.objects.filter(store=store).filter(
            Q(name=name) | Q(phone=phone)
        ).exists()

        if exists:
            messages.error(request, "هذا العميل مسجّل مسبقًا (اسم أو رقم).")
            return redirect("dashboard:customers_list", store_slug=store.slug)

        Customer.objects.create(
            store=store,
            name=name,
            phone=phone
        )

        return redirect("dashboard:customers_list", store_slug=store.slug)

    return render(request, "dashboard/customer_create.html", {
        "store": store
    })


@login_required
def delete_customer(request, store_slug, customer_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    customer = get_object_or_404(Customer, id=customer_id, store=store)

    if request.method == "POST":
        customer.delete()
        return redirect("dashboard:customers_list", store_slug=store.slug)

    return render(request, "dashboard/delete_customer.html", {
        "store": store,
        "customer": customer,
    })


def points_page(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)

    customer_id = request.GET.get("customer")
    customer = None
    balance = Decimal("0.0")

    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id, store=store)

        balance = (
            PointsTransaction.objects
            .filter(customer=customer)
            .aggregate(total=Sum("points"))["total"]
            or Decimal("0.0")
        )

        if request.method == "POST":
            raw_value = request.POST.get("points")
            note = request.POST.get("note", "")

            try:
                value = Decimal(raw_value)
            except (TypeError, InvalidOperation):
                messages.error(request, "قيمة النقاط غير صالحة")
                return redirect(f"/dashboard/{store_slug}/points/?customer={customer.id}")

            if value > 0:
                transaction_type = "add"
            elif value < 0:
                transaction_type = "subtract"
            else:
                transaction_type = "adjust"

            PointsTransaction.objects.create(
                customer=customer,
                customer_name=str(customer),
                points=value,
                transaction_type=transaction_type,
                note=note,
            )

            messages.success(request, "تم تعديل الرصيد بنجاح")

            return redirect(f"/dashboard/{store_slug}/points/?customer={customer.id}")

    customers = Customer.objects.filter(store=store)

    return render(request, "dashboard/points.html", {
        "store": store,
        "customers": customers,
        "selected_customer": customer,
        "balance": balance,
        "history": (
            PointsTransaction.objects
            .filter(customer=customer)
            .order_by("-id")
            if customer else []
        ),
    })


@login_required
def delete_points_transaction(request, store_slug, transaction_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    transaction = get_object_or_404(
        PointsTransaction,
        id=transaction_id
    )

    transaction.delete()

    messages.success(request, "تم حذف سجل النقاط بنجاح.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def store_settings(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)

    if request.user != store.owner:
        messages.error(request, "غير مسموح لك بالدخول إلى إعدادات هذا المتجر.")
        return redirect("/")

    if request.method == "POST":
        new_slug = request.POST.get("slug", "").strip()

        if new_slug != store.slug:
            if Store.objects.filter(slug=new_slug).exclude(id=store.id).exists():
                messages.error(request, "هذا الاسم مستخدم مسبقًا.")
                return redirect(f"/dashboard/{store.slug}/settings/")
            store.slug = new_slug

        store.description = request.POST.get("description", "")
        store.description2 = request.POST.get("description2", "")
        store.description3 = request.POST.get("description3", "")
        store.description4 = request.POST.get("description4", "")
        store.description5 = request.POST.get("description5", "")

        theme_value = request.POST.get("theme")
        if theme_value and theme_value.isdigit():
            store.theme = int(theme_value)

        if "logo" in request.FILES:
            store.logo = request.FILES["logo"]

        new_password = request.POST.get("new_password", "").strip()
        if new_password:
            store.owner.password = make_password(new_password)
            store.owner.save()
            messages.success(request, "تم تغيير كلمة المرور بنجاح.")

        percent = request.POST.get("payment_required_percentage", "").strip()
        if percent.isdigit():
            store.payment_required_percentage = int(percent)

        cashback = request.POST.get("cashback_percentage", "").strip()
        try:
            if cashback != "":
                cashback_value = Decimal(cashback)
                if Decimal("0") <= cashback_value <= Decimal("100"):
                    store.cashback_percentage = cashback_value
                else:
                    messages.error(request, "نسبة الكاش باك يجب أن تكون بين 0 و 100.")
                    return redirect(f"/dashboard/{store.slug}/settings/")
        except InvalidOperation:
            messages.error(request, "قيمة نسبة الكاش باك غير صحيحة.")
            return redirect(f"/dashboard/{store.slug}/settings/")

        hero_height = request.POST.get("hero_height", "").strip()
        if hero_height.isdigit():
            store.hero_height = int(hero_height)

        hero_fit = request.POST.get("hero_fit")
        if hero_fit in ["contain", "cover"]:
            store.hero_fit = hero_fit

        store.save()

        messages.success(request, "تم حفظ إعدادات المتجر بنجاح.")
        return redirect(f"/dashboard/{store.slug}/settings/")

    return render(request, "dashboard/store_settings.html", {"store": store})

def balances_report(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    customers = list(Customer.objects.filter(store=store).order_by("name"))
    suppliers = list(Supplier.objects.filter(store=store).order_by("name"))

    # ط§ط­ط³ط¨ ط§ظ„ط±طµظٹط¯ ظ…ظ† ط§ظ„ط·ظ„ط¨ط§طھ: طµط§ظپظٹ ط§ظ„ط·ظ„ط¨ - ط§ظ„ط¯ظپط¹ط§طھ
    orders_qs = (
        Order.objects
        .filter(store=store, document_kind__in=[1, 2], status="confirmed")
        .select_related("customer", "supplier")
        .prefetch_related("items")
    )

    customer_balances = {}
    supplier_balances = {}

    for order in orders_qs:
        if order.document_kind == 1:
            amount = order.net_total
            payment = order.payment
        else:
            amount = order.amount or Decimal("0")
            payment = order.payment

        balance_delta = amount - payment

        if order.customer_id:
            customer_balances[order.customer_id] = customer_balances.get(order.customer_id, Decimal("0")) + balance_delta
        elif order.supplier_id:
            supplier_balances[order.supplier_id] = supplier_balances.get(order.supplier_id, Decimal("0")) + balance_delta

    customer_total = Decimal("0.0")
    supplier_total = Decimal("0.0")

    for customer in customers:
        bal = customer_balances.get(customer.id, Decimal("0"))
        customer_total += bal
        customer.calc_balance = bal
        customer.calc_balance_abs = abs(bal)
        if bal > 0:
            customer.calc_balance_label = "ظ…ط¯ظٹظ†"
        elif bal < 0:
            customer.calc_balance_label = "ط¯ط§ط¦ظ†"
        else:
            customer.calc_balance_label = "ظ…طھظˆط§ط²ظ†"

    for supplier in suppliers:
        bal = supplier_balances.get(supplier.id, Decimal("0"))
        supplier_total += bal
        supplier.calc_balance = bal
        supplier.calc_balance_abs = abs(bal)
        if bal > 0:
            supplier.calc_balance_label = "ظ…ط¯ظٹظ†"
        elif bal < 0:
            supplier.calc_balance_label = "ط¯ط§ط¦ظ†"
        else:
            supplier.calc_balance_label = "ظ…طھظˆط§ط²ظ†"

    customer_total_abs = abs(customer_total)
    supplier_total_abs = abs(supplier_total)
    customer_total_label = "ظ…ط¯ظٹظ†" if customer_total > 0 else "ط¯ط§ط¦ظ†" if customer_total < 0 else "ظ…طھظˆط§ط²ظ†"
    supplier_total_label = "ظ…ط¯ظٹظ†" if supplier_total > 0 else "ط¯ط§ط¦ظ†" if supplier_total < 0 else "ظ…طھظˆط§ط²ظ†"

    return render(request, "dashboard/balances_report.html", {
        "store": store,
        "customers": customers,
        "suppliers": suppliers,
        "customer_total": customer_total,
        "supplier_total": supplier_total,
        "customer_total_abs": customer_total_abs,
        "supplier_total_abs": supplier_total_abs,
        "customer_total_label": customer_total_label,
        "supplier_total_label": supplier_total_label,
    })
#ط§ط¶ط§ظپط© 


@login_required
def supplier_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address")
        email = request.POST.get("email")
        opening_balance = request.POST.get("opening_balance") or 0

        # âœ… ظ…ظ†ط¹ ط§ظ„طھظƒط±ط§ط± ظپظ‚ط· ط¥ط°ط§ ط§ظ„ظ‚ظٹظ… ظ…ظˆط¬ظˆط¯ط©
        exists_qs = Supplier.objects.filter(store=store)

        if name:
            exists_qs = exists_qs.filter(name=name)

        if phone:
            exists_qs = exists_qs.filter(phone=phone)

        if exists_qs.exists():
            messages.error(request, "âڑ ï¸ڈ ظ‡ط°ط§ ط§ظ„ظ…ظˆط±ط¯ ظ…ط³ط¬ظ‘ظ„ ظ…ط³ط¨ظ‚ط§ظ‹ (ط§ط³ظ… ط£ظˆ ط±ظ‚ظ…).")
            return redirect("dashboard:suppliers_list", store_slug=store.slug)

        Supplier.objects.create(
            store=store,
            name=name,
            phone=phone,
            address=address,
            email=email,
            opening_balance=opening_balance
        )

        return redirect("dashboard:suppliers_list", store_slug=store.slug)

    return render(request, "dashboard/supplier_create.html", {
        "store": store
    })
#ط­ط°ظپ ظ…ظˆط±ط¯
@login_required
def delete_supplier(request, store_slug, supplier_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, store=store)

    if request.method == "POST":
        supplier.delete()
        return redirect("dashboard:suppliers_list", store_slug=store.slug)

    return render(request, "dashboard/delete_supplier.html", {
        "store": store,
        "supplier": supplier,
    })
# ط§ط¸ظ‡ط§ط± ظ‚ظٹظ…ط© ط§ظ„ظƒط§ط´ ط¨ط§ظƒ ط¨ط§ظ„ط·ظ„ط¨ ظˆ طھط¹ط¯ظٹظ„ظˆ ظˆ طھظپط§طµظٹظ„ظˆ
# dashboard/views.py

import json
@login_required
def cashback_preview(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    data = json.loads(request.body)
    total_cashback = Decimal("0")

    for item in data.get("items", []):
        # â›‘ï¸ڈ ط­ظ…ط§ظٹط©
        if not item.get("product_id"):
            continue

        price = Decimal(item.get("price") or 0)
        qty = Decimal(item.get("quantity") or 0)

        if qty <= 0 or price <= 0:
            continue

        product = Product.objects.get(id=item["product_id"], store=store)
        buy_price = product.get_avg_buy_price()

        profit = (price - buy_price) * qty
        if profit > 0:
            total_cashback += (
                profit * Decimal(store.cashback_percentage) / Decimal("100")
            )

    return JsonResponse({
        "cashback": float(total_cashback.quantize(Decimal("0.01")))
    })
#ط¬ط±ط¯ ط§ظ„ظ…ظ†طھط¬ط§طھ
from django.db.models import (
    Sum, F, DecimalField, ExpressionWrapper,
    OuterRef, Subquery, Value
)
from django.db.models.functions import Coalesce




@login_required
def inventory_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    # ًں”¹ ط¢ط®ط± ط³ط¹ط± ط´ط±ط§ط، ظ„ظƒظ„ ظ…ظ†طھط¬
    last_buy_price_qs = OrderItem.objects.filter(
        product=OuterRef("pk"),
        direction=1
    ).order_by("-id").values("buy_price")[:1]

    products_qs = (
        Product.objects
        .filter(store=store)
        .annotate(
            # âœ… ط§ظ„ظƒظ…ظٹط© ط§ظ„ظ…طھط¨ظ‚ظٹط© (Decimal ظ…ط¶ظ…ظˆظ†)
            remaining_qty=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("order_items__quantity") * F("order_items__direction"),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),

            # âœ… ط¢ط®ط± ط³ط¹ط± ط´ط±ط§ط، (Decimal ظ…ط¶ظ…ظˆظ†)
            last_buy_price=Coalesce(
                Subquery(
                    last_buy_price_qs,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
        )
        .annotate(
            # âœ… ظ‚ظٹظ…ط© ط§ظ„ظ…ط®ط²ظˆظ† (Decimal أ— Decimal)
            stock_value=ExpressionWrapper(
                F("remaining_qty") * F("last_buy_price"),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        .order_by("-id")
    )

    # ًں”چ ط§ظ„ط¨ط­ط«
    q = request.GET.get("q")
    if q:
        products_qs = products_qs.filter(name__icontains=q)

    # ًں“‚ ط§ظ„ظپط¦ط§طھ
    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products_qs = products_qs.filter(category_id=category_id)

    sub_category_id = request.GET.get("category2")
    if sub_category_id and sub_category_id.isdigit():
        products_qs = products_qs.filter(category2_id=sub_category_id)

    categories = Category.objects.filter(store=store)

    # ًں’° ط¥ط¬ظ…ط§ظ„ظٹ ظ‚ظٹظ…ط© ط§ظ„ظ…ط®ط²ظˆظ†
    total_inventory_value = products_qs.aggregate(
        total=Coalesce(
            Sum("stock_value"),
            Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))
        )
    )["total"]

    # Pagination
    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "store": store,
        "page_obj": page_obj,
        "categories": categories,
        "q": q,
        "current_category": int(category_id) if category_id and category_id.isdigit() else None,
        "current_sub_category": int(sub_category_id) if sub_category_id and sub_category_id.isdigit() else None,
        "total_inventory_value": total_inventory_value,
    }

    return render(request, "dashboard/inventory_list.html", context)



