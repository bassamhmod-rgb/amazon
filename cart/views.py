from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from stores.models import Store
from products.models import Product
from .models import Cart, CartItem

#دالة مساعدة
def get_cart(request, store):
    # تأمين session key
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # إذا الزبون مسجّل دخول → cart حسب user
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            store=store
        )
        return cart

    # إذا الزبون ضيف → cart حسب session_key
    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        store=store
    )
    return cart



# --- الدالة الأولى: إضافة المنتج للسلة (التي قمنا بتعديلها) ---
def add_to_cart(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    product = get_object_or_404(Product, id=product_id, store=store, active=True)

    cart = get_cart(request, store)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        note = request.POST.get("item_note", "")

        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity

        if note:
            item.item_note = note

        item.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            cart_count = cart.items.count()
            return JsonResponse({
                "cart_count": cart_count,
                "item_quantity": item.quantity,
            })

    return redirect("cart:cart_detail", store_slug=store.slug)

# --- الدالة الثانية: عرض صفحة السلة (التي كانت مفقودة) ---
def cart_detail(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)

    # --- تأمين session key للزبون الضيف ---
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # --- اختيار السلة حسب حالة المستخدم ---
    if request.user.is_authenticated:
        cart = Cart.objects.filter(
            user=request.user, store=store
        ).first()
    else:
        cart = Cart.objects.filter(
            session_key=session_key, store=store
        ).first()

    return render(request, "cart/cart_detail.html", {
        "store": store,
        "cart": cart,
    })
def remove_from_cart(request, store_slug, item_id):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)

    # --- تأمين session key للزبون الضيف ---
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # --- اختيار السلة الصحيحة حسب حالة المستخدم ---
    if request.user.is_authenticated:
        cart = Cart.objects.filter(
            user=request.user,
            store=store
        ).first()
    else:
        cart = Cart.objects.filter(
            session_key=session_key,
            store=store
        ).first()

    # إذا ما كان في كارت أصلاً!
    if not cart:
        return redirect("cart:cart_detail", store_slug=store.slug)

    # --- حذف العنصر ---
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()

    return redirect("cart:cart_detail", store_slug=store.slug)


def update_cart_item_quantity(request, store_slug, item_id, action):
    if request.method != "POST":
        return redirect("cart:cart_detail", store_slug=store_slug)

    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    cart = get_cart(request, store)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if action == "inc":
        item.quantity += 1
        item.save()
    elif action == "dec":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()

    return redirect("cart:cart_detail", store_slug=store.slug)
