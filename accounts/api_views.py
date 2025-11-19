from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.db import models   # ✅ أضف هذا السطر
import json
from .models import PointsTransaction


@csrf_exempt
def create_or_add_points(request):
    """
    API endpoint لاستقبال بيانات المستخدم من Access:
    {
      "username": "bassam",
      "password": "12345",
      "points": 100
    }
    """
    if request.method != 'POST':
        return JsonResponse({"error": "يُسمح فقط بطلبات POST"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username')
        password = data.get('password')
        points = int(data.get('points', 0))

        if not username or not password:
            return JsonResponse({"error": "الرجاء إرسال اسم المستخدم وكلمة المرور"}, status=400)

        # ✅ إذا المستخدم موجود → نضيف له النقاط
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            PointsTransaction.objects.create(
                user=user,
                amount=points,
                date=timezone.now(),
                note="إضافة نقاط من Access"
            )

            # احسب الرصيد بعد الإضافة
            total_points = PointsTransaction.objects.filter(user=user).aggregate(total=models.Sum('amount'))['total'] or 0

            return JsonResponse({
                "success": True,
                "message": f"تمت إضافة {points} نقطة للمستخدم '{username}'.",
                "current_balance": total_points
            })

        # ✅ إذا المستخدم غير موجود → ننشئه ونضيف له النقاط
        else:
            user = User.objects.create_user(username=username, password=password)
            PointsTransaction.objects.create(
                user=user,
                amount=points,
                date=timezone.now(),
                note="رصيد ابتدائي من Access"
            )
            return JsonResponse({
                "success": True,
                "message": f"تم إنشاء المستخدم '{username}' وإضافة {points} نقطة له.",
                "current_balance": points
            })

    except json.JSONDecodeError:
        return JsonResponse({"error": "البيانات المرسلة غير صالحة (JSON)"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
