from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from stores.models import Store
from products.models import Product
from .models import Cart, CartItem

# @login_required
# def add_to_cart(request, store_slug, product_id):
#     store = get_object_or_404(Store, slug=store_slug, is_active=True)
#     product = get_object_or_404(Product, id=product_id, store=store, active=True)
#     cart, created = Cart.objects.get_or_create(user=request.user, store=store)
#     item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#     if not created:
#         item.quantity += 1
#     item.save()
#     return redirect("cart:cart_detail", store_slug=store.slug)

# @login_required
# def cart_detail(request, store_slug):
#     store = get_object_or_404(Store, slug=store_slug, is_active=True)
#     cart, created = Cart.objects.get_or_create(user=request.user, store=store)
#     return render(request, "cart/cart_detail.html", {
#         "store": store,
#         "cart": cart,
#     })



# --- الدالة الأولى: إضافة المنتج للسلة (التي قمنا بتعديلها) ---
@login_required
def add_to_cart(request, store_slug, product_id):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    product = get_object_or_404(Product, id=product_id, store=store, active=True)
    
    cart, created = Cart.objects.get_or_create(user=request.user, store=store)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # معالجة البيانات القادمة من الفورم
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        note = request.POST.get('item_note', '')

        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
            
        # تأكد أنك أضفت حقل note في ملف models.py كما شرحنا سابقاً
        if note:
             # إذا لم تضف الحقل في المودل بعد، احذف السطر التالي مؤقتاً لتجنب الأخطاء
            item.item_note = note
            
        item.save()
    
    return redirect("cart:cart_detail", store_slug=store.slug)


# --- الدالة الثانية: عرض صفحة السلة (التي كانت مفقودة) ---
@login_required
def cart_detail(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user, store=store)
    
    return render(request, "cart/cart_detail.html", {
        "store": store,
        "cart": cart,
    })
#حذف من السلة
@login_required
def remove_from_cart(request, store_slug, item_id):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user, store=store)

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()

    return redirect("cart:cart_detail", store_slug=store.slug)
