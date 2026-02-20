from django.shortcuts import render, get_object_or_404, redirect
from .models import Store
from products.models import Product
from accounts.models import Customer
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce, Cast
from accounts.models import PointsTransaction
from products.models import Category
from django.db.models import Q, Exists, OuterRef
from django.contrib.auth.decorators import login_required
from stores.models import Store, StorePaymentMethod
from cart.models import Cart

def store_list(request):
    stores = Store.objects.filter(is_active=True)
    return render(request, "stores/store_list.html", {"stores": stores})

def store_front(request, slug):
    store = get_object_or_404(Store, slug=slug, is_active=True)

    # ✔ التاجر الحقيقي فقط
    is_owner = request.user.is_authenticated and request.user == store.owner

    # ✔ الزبون المسجل دخول
    customer = None
    balance = 0

    if request.session.get("customer_id"):
        customer = Customer.objects.filter(
            id=request.session["customer_id"],
            store=store
        ).first()

        if customer:
            balance = PointsTransaction.objects.filter(customer=customer).aggregate(
                total=Sum("points")
            )["total"] or 0

    # ============ 🛒 سلة الزبون ============
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, store=store).first()
    else:
        cart = Cart.objects.filter(session_key=session_key, store=store).first()

    cart_count = 0
    if cart:
        cart_count = cart.items.count()

    # ============ 🔥 المنتجات ============
    movement_expr = ExpressionWrapper(
        F("order_items__quantity") * Cast(F("order_items__direction"), DecimalField(max_digits=12, decimal_places=2)),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    movements = Coalesce(
        Sum(movement_expr),
        Value(0),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    real_stock_calc = ExpressionWrapper(
        Cast(F("stock"), DecimalField(max_digits=12, decimal_places=2)) + movements,
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    sold_qty = Coalesce(
        Sum(Case(
            When(order_items__direction=-1, then=F("order_items__quantity")),
            default=Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )),
        Value(0),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    products = (
        Product.objects
        .filter(store=store, active=True)
        .annotate(real_stock_calc=real_stock_calc, sold_qty=sold_qty)
        .filter(real_stock_calc__gt=0)
        .order_by("-sold_qty", "-id")
    )

    # ============ 🔎 البحث ============
    q = request.GET.get("q")
    if q:
        products = products.filter(name__icontains=q)

    # ============ 🟦 جلب الفئات ============
    categories = Category.objects.filter(store=store)

    # ============ 🟨 التصفية بالحقل category ============
    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products = products.filter(category_id=category_id)
    else:
        category_id = ""

    # ============ 🟧 التصفية بالحقل category2 ============
    category2_id = request.GET.get("category2")
    if category2_id and category2_id.isdigit():
        products = products.filter(category2_id=category2_id)
    else:
        category2_id = ""

    return render(request, "stores/store_front.html", {
        "store": store,
        "products": products,
        "is_owner": is_owner,
        "customer": customer,
        "balance": balance,
        "cart_count": cart_count,

        # مهم جداً للواجهة
        "categories": categories,
        "current_category": category_id,
        "current_category2": category2_id,
        "q": q or "",
    })

# تفاصيل المنتج للزبون
def product_public(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug)
    product = get_object_or_404(Product, id=product_id, store=store)
    return render(request, "stores/product_public.html", {
    "store": store,
    "product": product,
})

#بحث عام للصفحة العامة

from django.db.models import Q, Exists, OuterRef
from products.models import Product, Category

def store_list(request):

    q = request.GET.get("q", "").strip()

    stores = Store.objects.filter(is_active=True)

    if q:
        # 🔎 بحث في المنتجات
        product_match = Product.objects.filter(
            store=OuterRef("pk"),
            name__icontains=q
        )

        # 🔎 بحث في الفئة الأساسية
        category_match = Category.objects.filter(
            store=OuterRef("pk"),
            name__icontains=q
        )

        # 🔎 بحث في الفئة الفرعية category2 (داخل جدول المنتجات)
        subcategory_match = Product.objects.filter(
            store=OuterRef("pk"),
            category2__name__icontains=q
        )

        stores = stores.annotate(
            has_product=Exists(product_match),
            has_category=Exists(category_match),
            has_subcategory=Exists(subcategory_match),
        ).filter(
            Q(name__icontains=q) |
            Q(has_product=True) |
            Q(has_category=True) |
            Q(has_subcategory=True)
        )

    return render(request, "stores/store_list.html", {
        "stores": stores,
        "q": q,
    })
#طرق الدفع
# ============= قائمة طرق الدفع =============
@login_required
def payment_methods_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    methods = StorePaymentMethod.objects.filter(store=store).order_by("order")

    return render(request, "stores_dashboard/payment_methods/list.html", {
        "store": store,
        "methods": methods,
    })


# ============= إضافة طريقة دفع =============
@login_required
def payment_methods_add(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        type = request.POST.get("type")
        recipient_name = request.POST.get("recipient_name")
        phone_number = request.POST.get("phone_number")
        account_number = request.POST.get("account_number")
        additional_info = request.POST.get("additional_info")
        order = request.POST.get("order") or 0
        is_active = "is_active" in request.POST

        icon = request.FILES.get("icon")

        StorePaymentMethod.objects.create(
            store=store,
            name=name,
            type=type,
            recipient_name=recipient_name,
            phone_number=phone_number,
            account_number=account_number,
            additional_info=additional_info,
            order=order,
            is_active=is_active,
            icon=icon
        )

        return redirect("stores:payment_methods", store_slug=store.slug)

    return render(request, "stores_dashboard/payment_methods/add.html", {
        "store": store
    })


# ============= تعديل طريقة دفع =============
@login_required
def payment_methods_edit(request, store_slug, method_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    method = get_object_or_404(StorePaymentMethod, id=method_id, store=store)

    if request.method == "POST":
        method.name = request.POST.get("name")
        method.type = request.POST.get("type")
        method.recipient_name = request.POST.get("recipient_name")
        method.phone_number = request.POST.get("phone_number")
        method.account_number = request.POST.get("account_number")
        method.additional_info = request.POST.get("additional_info")
        method.order = request.POST.get("order") or 0
        method.is_active = "is_active" in request.POST
##
        if request.FILES.get("icon"):
            method.icon = request.FILES.get("icon")

        method.save()

        return redirect("stores:payment_methods", store_slug=store.slug)

    return render(request, "stores_dashboard/payment_methods/edit.html", {
        "store": store,
        "method": method
    })


# ============= حذف طريقة دفع =============
@login_required
def payment_methods_delete(request, store_slug, method_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    method = get_object_or_404(StorePaymentMethod, id=method_id, store=store)

    method.delete()

    return redirect("stores:payment_methods", store_slug=store.slug)
