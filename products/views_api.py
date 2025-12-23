from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from products.models import Category
from stores.models import Store
from products.models import Product


@csrf_exempt
def merchant_categories_api(request, merchant_id):
    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse([], safe=False)

    categories = Category.objects.filter(store=store).values(
        "name"
    )

    return JsonResponse(list(categories), safe=False)




@csrf_exempt
def merchant_products_api(request, merchant_id):
    store = Store.objects.filter(owner_id=merchant_id).first()
    if not store:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(store=store).values(
        "name",
        "price",
        "description",
        "category__name",
    )

    return JsonResponse(list(products), safe=False)
