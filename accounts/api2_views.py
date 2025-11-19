from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate
import json
from .models import Product

@csrf_exempt
def add_product_from_access(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            username = data.get("username")
            password = data.get("password")

            user = authenticate(username=username, password=password)
            if user is None:
                return JsonResponse({"error": "بيانات الدخول غير صحيحة"}, status=401)

            name = data.get("name")
            description = data.get("description", "")
            price = data.get("price", 0)
            quantity = data.get("quantity", 0)

            if not name:
                return JsonResponse({"error": "اسم المنتج مطلوب"}, status=400)

            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                added_by=user
            )

            return JsonResponse({
                "message": "تمت إضافة المنتج بنجاح",
                "product_id": product.id,
                "name": product.name
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "تنسيق البيانات غير صحيح"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "يجب استخدام POST"}, status=405)
