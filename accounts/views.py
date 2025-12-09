from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models

from stores.models import Store
from accounts.models import Customer


# إنشاء حساب زبون جديد
def customer_register(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        # 🔥 منع تكرار رقم الهاتف فقط عند نفس المتجر
        exists = Customer.objects.filter(
            store=store,
            phone=phone
        ).exists()

        if exists:
            messages.error(request, "⚠️ رقم الهاتف مسجّل مسبقاً عند هذا المتجر.")
            return redirect("accounts:customer_register", store_slug=store.slug)

        # ✔ إنشاء زبون
        customer = Customer.objects.create(
            store=store,
            name=name,
            phone=phone
        )

        # ✔ تسجيل دخوله (باستخدام session)
        request.session["customer_id"] = customer.id

        # ✔ العودة لصفحة المتجر
        return redirect(f"/store/{store.slug}/")

    return render(request, "accounts/customer_register.html", {
        "store": store,
    })
def customer_login(request, store_slug):
    next_page = request.GET.get("next") or f"/orders/{store_slug}/checkout/"

    store = Store.objects.filter(slug=store_slug).first()
    message = None

    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()

        if not store:
            message = "خطأ: لا يمكن تحديد المتجر."
        elif not phone:
            message = "❌ يرجى إدخال رقم الهاتف."
        else:
            customer = Customer.objects.filter(store=store, phone=phone).first()

            # ✔️ إذا موجود → تابع مباشرة
            if customer:
                request.session["customer_id"] = customer.id
                return redirect(next_page)

            # ❗ إذا غير موجود → صفحة تأكيد
            request.session["temp_phone"] = phone
            request.session["next_after_register"] = next_page

            return render(request, "accounts/customer_confirm_new.html", {
                "store": store,
                "phone": phone,
            })

    return render(request, "accounts/customer_login.html", {
        "next": next_page,
        "store": store,
        "message": message,
    })


# تحويل التاجر مباشرة إلى متجره
def merchant_redirect(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    store = Store.objects.filter(owner=request.user).first()

    if store:
        return redirect("stores:store_front", slug=store.slug)

    return render(request, "accounts/no_store.html")

#تسجيل خروج زبون
def customer_logout(request):
    # امسح هوية الزبون من الـ session
    request.session.pop("customer_id", None)

    # رجّعو على الصفحة الرئيسية أو صفحة المتجر السابقة
    next_page = request.GET.get("next") or "/"
    return redirect(next_page)

def quick_register(request, store_slug):
    if request.method != "POST":
        return redirect("accounts:customer_login", store_slug=store_slug)

    store = get_object_or_404(Store, slug=store_slug)

    phone = request.session.get("temp_phone")
    next_page = request.session.get("next_after_register") or f"/orders/{store_slug}/checkout/"

    if not phone:
        return redirect("accounts:customer_login", store_slug=store_slug)

    # 🔥 إنشاء حساب بالخلفية
    customer = Customer.objects.create(
        store=store,
        phone=phone,
        name=""     # يكتب اسمو لاحقاً داخل checkout
    )

    request.session["customer_id"] = customer.id
    return redirect(next_page)
