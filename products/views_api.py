from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from products.models import Category
from stores.models import Store
from products.models import Product
import json
from django.db.models import F
#تصدير
@csrf_exempt
def merchant_categories_api(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()
    
    if not store:
        return JsonResponse([], safe=False)

    categories = Category.objects.filter(store=store).values(
        "name"
    )

    return JsonResponse(list(categories), safe=False)




@csrf_exempt
def merchant_products_api(request, merchant_id):
    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(store=store).values(
        "name",
        "price",
        "description",
       category_name=F("category__name"),
    )

    return JsonResponse(list(products), safe=False)
#استيراد
@csrf_exempt
def create_category_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        name = data.get("name", "").strip()
        
        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        # ✅ منع تكرار الفئة (مو المنتج)
        if Category.objects.filter(store=store, name=name).exists():
            return JsonResponse({"status": "exists"})

        Category.objects.create(
            store=store,
            name=name
        )

        return JsonResponse({"status": "created"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_product_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        name = data.get("name", "").strip()
        price = data.get("price", 0)
        description = data.get("description", "").strip()
        category_name = data.get("category", "").strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "بيانات ناقصة"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(
                store=store,
                name=category_name
            )

        existing = Product.objects.filter(store=store, name=name).first()
        if existing:
           return JsonResponse({
        "status": "exists",
        "id": existing.id
           })

        product = Product.objects.create(
            store=store,
            name=name,
            price=float(price) if price else 0,
            buy_price=0,
            stock=0,
            description=description,
            category=category,
            active=True
        )

        return JsonResponse({
            "status": "created",
            "id": product.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
