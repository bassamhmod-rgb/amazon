
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum
from products.models import ProductDetails ,Product, ProductGallery
# --- استيراد المودلز من التطبيقات المختلفة ---
from products.models import Category, Product
from products.forms import CategoryForm, ProductForm
from stores.models import Store
from orders.models import Order, OrderItem
from accounts.models import PointsTransaction

# 1. الزبون موجود بـ accounts (حسب كلامك)
from accounts.models import Customer
from django.contrib import messages
###
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from accounts.models import Supplier
from django.http import JsonResponse
# أما إذا كنت ناقله كمان لـ accounts، الغي السطر اللي فوق واستخدم هاد:
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

    # 🔴 عدد الطلبات الجديدة (اللي لسا ما شافها صاحب المتجر)
    new_orders_count = Order.objects.filter(
        store=store,
        is_seen_by_store=False
    ).count()

    # آخر الطلبات (10 فقط)
    orders = Order.objects.filter(store=store).order_by("-created_at")[:10]

    # عدد أو قائمة المنتجات
    products = Product.objects.filter(store=store)

    return render(request, "dashboard/dashboard_home.html", {
        "store": store,
        "orders": orders,
        "products": products,

        # 🔥 مهم جداً للـ sidebar 
        "new_orders_count": new_orders_count,
    })



# 🔹 قائمة المنتجات مع بحث + تصفية + Pagination
@login_required
def products_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    products_qs = Product.objects.filter(store=store).order_by("-id")

    # البحث بالاسم
    q = request.GET.get("q")
    if q:
        products_qs = products_qs.filter(name__icontains=q)

    # التصفية حسب الفئة الأساسية
    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products_qs = products_qs.filter(category_id=category_id)

    # التصفية حسب الفئة الفرعية
    sub_category_id = request.GET.get("category2")
    if sub_category_id and sub_category_id.isdigit():
        products_qs = products_qs.filter(category2_id=sub_category_id)

    # جلب كل الفئات الخاصة بهذا المتجر
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

        # الحالي المختار
        "current_category": int(category_id) if category_id and category_id.isdigit() else None,
        "current_sub_category": int(sub_category_id) if sub_category_id and sub_category_id.isdigit() else None,

        "products_qs": products_qs,
    }
    return render(request, "dashboard/products_list.html", context)

# 🔹 إضافة منتج جديد
@login_required
def product_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, store=store)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()

            # 🔥 إضافة المواصفات (ProductDetails)
            titles = request.POST.getlist("detail_title")
            values = request.POST.getlist("detail_value")

            for t, v in zip(titles, values):
                if t.strip() and v.strip():
                    ProductDetails.objects.create(
                        product=product,
                        title=t.strip(),
                        value=v.strip()
                    )

            # 🖼️ إضافة الصور الفرعية (ProductGallery)
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

# 🔹 تعديل منتج
@login_required
def product_update(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product, store=store)
        if form.is_valid():
            product = form.save()

            # 🔥 تحديث المواصفات (نحذف القديم ونضيف الجديد)
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

            # 🖼️ إضافة صور فرعية جديدة (بدون حذف القديمة)
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
#حذف صورة من المعرض
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

# 🔹 حذف منتج
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
            "⚠️ المنتج غير موجود أو تم حذفه مسبقاً"
        )
        return redirect("dashboard:products_list", store_slug=store.slug)

    if request.method == "POST":
        product_qs.delete()
        messages.success(
            request,
            "🗑️ تم حذف المنتج بنجاح"
        )

    return redirect("dashboard:products_list", store_slug=store.slug)

#تفاصيل المنتج
def product_detail(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    product = get_object_or_404(Product, id=product_id, store=store)

    return render(request, 'dashboard/product_detail.html', {
        'store': store,
        'product': product,
    })

#ادارة الفئات
#عرض
def categories_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    categories = Category.objects.filter(store=store)

    return render(request, 'dashboard/categories_list.html', {
        'store': store,
        'categories': categories,   # ← تأكد من هذي
    })

# اضافة
@login_required
def add_category(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            return render(request, "dashboard/category_form.html", {
                "store": store,
                "error": "الرجاء إدخال اسم الفئة",
            })

        # إنشاء الفئة وربطها تلقائياً بالمتجر
        Category.objects.create(
            name=name,
            store=store
        )

        return redirect("dashboard:categories_list", store_slug=store.slug)

    return render(request, "dashboard/category_form.html", {
        "store": store
    })

#حذف فئة
@login_required
# def delete_category(request, store_slug, category_id):
#     store = get_object_or_404(Store, slug=store_slug, owner=request.user)
#     category = get_object_or_404(Category, id=category_id, store=store)

#     # حذف مباشر بدون صفحة
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


#ادارة الطلبات
#حذف
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


#تفاصيل الطلب
@login_required
def order_detail_dashboard(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    # ⭐ حساب النسبة والمبلغ المقترَح للدفع المسبق
    required_percent = store.payment_required_percentage or 0
    required_amount = 0

    if required_percent > 0:
        required_amount = (order.net_total * required_percent) / 100

    # 👁️ تعليم الطلب كمقروء
    if not order.is_seen_by_store:
        order.is_seen_by_store = True
        order.save(update_fields=["is_seen_by_store"])

    # ===============================
    # 🎁 حساب الكاش باك (للبيع فقط)
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

        # 🛡️ هل تم تسجيل كاش باك سابقًا؟
        has_cashback = PointsTransaction.objects.filter(
            customer=order.customer,
            note=f"كاش باك من طلب بيع رقم {order.id}"
        ).exists()

    return render(request, "dashboard/order_detail_dashboard.html", {
        "store": store,
        "order": order,

        # الدفع المسبق
        "required_percent": required_percent,
        "required_amount": required_amount,

        # الكاش باك
        "total_profit": total_profit,
        "suggested_cashback": suggested_cashback,
        "has_cashback": has_cashback,
    })

#تأكيد الطلب
@login_required
def confirm_order(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    # تأكيد الطلب
    order.status = "confirmed"
    order.save(update_fields=["status"])

    # ===============================
    # 🎁 حفظ الكاش باك (للبيع فقط)
    # ===============================
    if order.transaction_type == "sale" and order.customer:

        # منع التكرار
        exists = PointsTransaction.objects.filter(
            customer=order.customer,
            note=f"كاش باك من طلب بيع رقم {order.id}"
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
                    note=f"كاش باك من طلب بيع رقم {order.id}",
                )

    return redirect("dashboard:order_detail_dashboard", store_slug=store.slug, order_id=order.id)

#اضافة طلب من التاجر بيع او شراء



from decimal import Decimal, InvalidOperation

def _to_decimal(val, default="0"):
    try:
        # إذا القيمة Decimal أصلًا
        if isinstance(val, Decimal):
            return val

        # إذا None
        if val is None:
            return Decimal(default)

        # إذا رقم (int / float)
        if isinstance(val, (int, float)):
            return Decimal(str(val))

        # إذا نص
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

        # 1) نوع العملية
        transaction_type = request.POST.get("transaction_type", "sale")

        # 2) جلب الزبون أو المورد
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
            messages.error(request, "يجب اختيار زبون لإتمام عملية البيع.")
            return redirect("dashboard:order_create", store_slug=store.slug)

        if transaction_type == "purchase" and not supplier:
            messages.error(request, "يجب اختيار مورد لإتمام عملية الشراء.")
            return redirect("dashboard:order_create", store_slug=store.slug)

        status = "confirmed"

        # 3) إنشاء الطلب
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

        # 4) عناصر الطلب
        products = request.POST.getlist("product_id[]")
        prices   = request.POST.getlist("price[]")
        qtys     = request.POST.getlist("quantity[]")

        total_profit = Decimal("0")  # فقط للبيع

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

                # الربح = (سعر البيع - سعر الشراء) * الكمية
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

        # 5) ⭐ إضافة النقاط (الكاش باك) — فقط عند البيع
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

            # حماية
            if points_value < 0:
                points_value = Decimal("0")

            if points_value > 0:
                PointsTransaction.objects.create(
                    customer=customer,
                    customer_name=str(customer),
                    points=points_value,
                    transaction_type="add",
                    note=f"كاش باك من طلب بيع رقم {order.id}",
                )

        return redirect("dashboard:orders_list", store_slug=store.slug)

    return render(request, "dashboard/order_create.html", {
        "store": store
    })

# تعديل الطلب (بيع + شراء) — بدون حقول supplier
@login_required
def order_update(request, store_slug, order_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)
    new_orders_count = Order.objects.filter(store=store, is_seen_by_store=False).count()

    if request.method == "POST":

        # 🟦 1) نوع العملية (بيع / شراء)
        transaction_type = request.POST.get("transaction_type", "sale")
        order.transaction_type = transaction_type

        # 🟦 2) خصم ودفع (❌ بدون total)
        order.discount = request.POST.get("discount", 0)
        order.payment = request.POST.get("payment", 0)

        # 🟦 3) زبون أو مورد (حسب النوع)
        if transaction_type == "sale":
            customer_id = request.POST.get("customer_id")
            order.customer_id = customer_id if customer_id else None
            order.supplier = None  # ← مهم جداً

        else:  # purchase
            supplier_id = request.POST.get("supplier_id")
            order.supplier_id = supplier_id if supplier_id else None
            order.customer = None  # ← مهم جداً

        order.save()

        # 🟦 4) حذف العناصر القديمة
        order.items.all().delete()

        # 🟦 5) إضافة العناصر الجديدة
        products = request.POST.getlist("product_id[]")
        prices   = request.POST.getlist("price[]")
        qtys     = request.POST.getlist("quantity[]")

        for i in range(len(products)):

            product = Product.objects.filter(id=products[i]).first()
            if not product:
                continue

            price = float(prices[i])
            qty = float(qtys[i])

            # بيع أو شراء؟
            direction = -1 if transaction_type == "sale" else 1

            # snapshot
            if transaction_type == "sale":
                buy_price = product.buy_price  # snapshot للربح
            else:
                buy_price = price  # snapshot لتكلفة الشراء

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

#فلترة طلبات
#بالحالة
#برقم الطلب
# قائمة الطلبات
@login_required
def orders_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    status = request.GET.get("status", "")
    order_id = request.GET.get("order_id", "")

    # كل طلبات المتجر
    orders = Order.objects.filter(store=store)

    # فلترة حسب الحالة
    if status:
        orders = orders.filter(status=status)

    # فلترة حسب رقم الطلب
    if order_id:
        orders = orders.filter(id=order_id)

    # ترتيب من الأحدث للأقدم
    orders = orders.order_by("-created_at")

    # 🟢 عدد الطلبات الجديدة (لسّا is_seen_by_store = False)
    new_orders_count = Order.objects.filter(
        store=store,
        is_seen_by_store=False
    ).count()

    context = {
        "store": store,
        "orders": orders,
        "current_status": status,
        "current_id": order_id,
        "new_orders_count": new_orders_count,  # مهم للـ sidebar
    }

    # 🔴 انتبه: هون ما عم نغيّر is_seen_by_store
    # الطلب بيتعلَّم كمقروء لما تفتح صفحة تفاصيل الطلب (منسوّيها بعدين)

    return render(request, "dashboard/orders_list.html", context)
# البحث باسماء المنتجات

def search_products(request, store_slug):
    q = request.GET.get("q", "")
    products = Product.objects.filter(store__slug=store_slug, name__icontains=q)

    results = [
        {"id": p.id, "name": p.name, "price": float(p.price)}
        for p in products
    ]

    return JsonResponse({"results": results})
#البحث باسماء المستخدمين

def search_customers(request, store_slug):
    q = request.GET.get("q", "")
    
    # جلب زبائن هذا المتجر فقط
    customers = Customer.objects.filter(store__slug=store_slug, name__icontains=q) | Customer.objects.filter(
        store__slug=store_slug,
        phone__icontains=q
    )

    results = [
        {"id": c.id, "name": c.name, "phone": c.phone}
        for c in customers
    ]

    return JsonResponse({"results": results})
# 🔍 بحث الموردين


def search_suppliers(request, store_slug):
    q = request.GET.get("q", "").strip()

    # جلب الموردين حسب المتجر والكلمة المكتوبة
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

# ادارة العملاء
# عرض العملاء
@login_required
def customers_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    customers = Customer.objects.filter(store=store)

    return render(request, "dashboard/customers_list.html", {
        "store": store,
        "customers": customers,
    })
# إضافة زبون من قبل التاجر


from django.db.models import Q

@login_required
def customer_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        # 🔥 منع تكرار الاسم أو الرقم عند نفس المتجر
        exists = Customer.objects.filter(store=store).filter(
            Q(name=name) | Q(phone=phone)
        ).exists()

        if exists:
            messages.error(request, "⚠️ هذا العميل مسجّل مسبقاً عندك (اسم أو رقم).")
            return redirect("dashboard:customers_list", store_slug=store.slug)

        # ✔ إنشاء العميل
        Customer.objects.create(
            store=store,
            name=name,
            phone=phone
        )

        return redirect("dashboard:customers_list", store_slug=store.slug)

    return render(request, "dashboard/customer_create.html", {
        "store": store
    })


# حذف عميل
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

# ادارة النقاط

def points_page(request, store_slug):

    # ✅ دائماً نجيب المتجر أول شي
    store = get_object_or_404(Store, slug=store_slug)

    customer_id = request.GET.get("customer")
    customer = None
    balance = Decimal("0.0")

    # إذا تم اختيار زبون
    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id, store=store)

        balance = (
            PointsTransaction.objects
            .filter(customer=customer)
            .aggregate(total=Sum("points"))["total"]
            or Decimal("0.0")
        )

        # إذا في POST (إضافة أو خصم نقاط)
        if request.method == "POST":
            raw_value = request.POST.get("points")
            note = request.POST.get("note", "")

            try:
                value = Decimal(raw_value)
            except (TypeError, InvalidOperation):
                messages.error(request, "❌ قيمة النقاط غير صالحة")
                return redirect(f"/dashboard/{store_slug}/points/?customer={customer.id}")

            # تحديد نوع العملية
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

            messages.success(request, "✅ تم تعديل الرصيد بنجاح")

            return redirect(f"/dashboard/{store_slug}/points/?customer={customer.id}")

    # جلب زبائن المتجر
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

#حذف سجل نقاط
@login_required
def delete_points_transaction(request, store_slug, transaction_id):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    transaction = get_object_or_404(
        PointsTransaction,
        id=transaction_id
    )

    transaction.delete()

    messages.success(request, "🗑 تم حذف سجل النقاط بنجاح.")

    # ✅ رجوع لنفس صفحة الرصيد بدون أسماء مسارات
    return redirect(request.META.get("HTTP_REFERER", "/"))


# اعدادات التاجر



@login_required
def store_settings(request, store_slug):

    # 🔐 تأكيد إنو المستخدم هو صاحب المتجر
    store = get_object_or_404(Store, slug=store_slug)

    if request.user != store.owner:
        messages.error(request, "🚫 غير مسموح لك بالدخول إلى إعدادات هذا المتجر.")
        return redirect("/")

    if request.method == "POST":

        # 1) Slug
        new_slug = request.POST.get("slug", "").strip()

        if new_slug != store.slug:
            if Store.objects.filter(slug=new_slug).exclude(id=store.id).exists():
                messages.error(request, "⚠️ هذا الاسم مستخدم مسبقاً.")
                return redirect(f"/dashboard/{store.slug}/settings/")
            store.slug = new_slug

        # 2) Descriptions
        store.description = request.POST.get("description", "")
        store.description2 = request.POST.get("description2", "")
        store.description3 = request.POST.get("description3", "")
        store.description4 = request.POST.get("description4", "")
        store.description5 = request.POST.get("description5", "")

        # 3) Theme
        theme_value = request.POST.get("theme")
        if theme_value and theme_value.isdigit():
            store.theme = int(theme_value)

        # 4) Logo
        if "logo" in request.FILES:
            store.logo = request.FILES["logo"]

        # 5) Password
        new_password = request.POST.get("new_password", "").strip()
        if new_password:
            store.owner.password = make_password(new_password)
            store.owner.save()
            messages.success(request, "🔐 تم تغيير كلمة المرور بنجاح.")

        # ⭐ 6) نسبة الدفع المطلوبة لكل الطلبات
        percent = request.POST.get("payment_required_percentage", "").strip()
        if percent.isdigit():
            store.payment_required_percentage = int(percent)

        # ⭐ 7) نسبة الكاش باك من ربح الطلب
        from decimal import Decimal, InvalidOperation

        cashback = request.POST.get("cashback_percentage", "").strip()

        try:
           if cashback != "":
              cashback_value = Decimal(cashback)

              if Decimal("0") <= cashback_value <= Decimal("100"):
                 store.cashback_percentage = cashback_value
              else:
                 messages.error(request, "⚠️ نسبة الكاش باك يجب أن تكون بين 0 و 100.")
                 return redirect(f"/dashboard/{store.slug}/settings/")
        except InvalidOperation:
            messages.error(request, "⚠️ قيمة نسبة الكاش باك غير صحيحة.")
            return redirect(f"/dashboard/{store.slug}/settings/")

        # 🖼️ 7) إعدادات صورة الهيرو (الجديدة)
        hero_height = request.POST.get("hero_height", "").strip()
        if hero_height.isdigit():
            store.hero_height = int(hero_height)

        hero_fit = request.POST.get("hero_fit")
        if hero_fit in ["contain", "cover"]:
            store.hero_fit = hero_fit

        # Save all changes
        store.save()

        messages.success(request, "✅ تم حفظ إعدادات المتجر بنجاح.")
        return redirect(f"/dashboard/{store.slug}/settings/")

    # GET request
    return render(request, "dashboard/store_settings.html", {"store": store})
#اشعار بعدد الطلبات الجديدة

def merchant_dashboard(request, store_slug):

    store = Store.objects.get(slug=store_slug)

    new_orders_count = Order.objects.filter(
        store=store,
        is_seen_by_store=False
    ).count()

    return render(request, "dashboard/dashboard.html", {
        "store": store,
        "new_orders_count": new_orders_count,
    })
# ادارة الموردين
#عرض
@login_required
def suppliers_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)
    suppliers = Supplier.objects.filter(store=store).order_by("-id")

    return render(request, "dashboard/suppliers_list.html", {
        "store": store,
        "suppliers": suppliers,
    })
#اضافة 


@login_required
def supplier_create(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address")
        email = request.POST.get("email")
        opening_balance = request.POST.get("opening_balance") or 0

        # ✅ منع التكرار فقط إذا القيم موجودة
        exists_qs = Supplier.objects.filter(store=store)

        if name:
            exists_qs = exists_qs.filter(name=name)

        if phone:
            exists_qs = exists_qs.filter(phone=phone)

        if exists_qs.exists():
            messages.error(request, "⚠️ هذا المورد مسجّل مسبقاً (اسم أو رقم).")
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
#حذف مورد
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
# اظهار قيمة الكاش باك بالطلب و تعديلو و تفاصيلو
# dashboard/views.py

import json
@login_required
def cashback_preview(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    data = json.loads(request.body)
    total_cashback = Decimal("0")

    for item in data.get("items", []):
        # ⛑️ حماية
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
#جرد المنتجات
from django.db.models import (
    Sum, F, DecimalField, ExpressionWrapper,
    OuterRef, Subquery, Value
)
from django.db.models.functions import Coalesce




@login_required
def inventory_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, owner=request.user)

    # 🔹 آخر سعر شراء لكل منتج
    last_buy_price_qs = OrderItem.objects.filter(
        product=OuterRef("pk"),
        direction=1
    ).order_by("-id").values("buy_price")[:1]

    products_qs = (
        Product.objects
        .filter(store=store)
        .annotate(
            # ✅ الكمية المتبقية (Decimal مضمون)
            remaining_qty=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("order_items__quantity") * F("order_items__direction"),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),

            # ✅ آخر سعر شراء (Decimal مضمون)
            last_buy_price=Coalesce(
                Subquery(
                    last_buy_price_qs,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
        )
        .annotate(
            # ✅ قيمة المخزون (Decimal × Decimal)
            stock_value=ExpressionWrapper(
                F("remaining_qty") * F("last_buy_price"),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        .order_by("-id")
    )

    # 🔍 البحث
    q = request.GET.get("q")
    if q:
        products_qs = products_qs.filter(name__icontains=q)

    # 📂 الفئات
    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products_qs = products_qs.filter(category_id=category_id)

    sub_category_id = request.GET.get("category2")
    if sub_category_id and sub_category_id.isdigit():
        products_qs = products_qs.filter(category2_id=sub_category_id)

    categories = Category.objects.filter(store=store)

    # 💰 إجمالي قيمة المخزون
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