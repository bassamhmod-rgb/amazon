from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from stores.models import Store

#لنقل الارقام من gcod
@csrf_exempt
def update_store_codes_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        mobile = (data.get("mobile") or "").strip()
        number = (data.get("number") or "").strip()
        sna = (data.get("sna") or "").strip()

        if not mobile:
            return JsonResponse({"error": "mobile required"}, status=400)

        store = Store.objects.filter(mobile=mobile).first()
        if not store:
            return JsonResponse({"status": "not_found", "mobile": mobile}, status=404)

        # ✅ كلها نصوص
        if number:
            store.rkmdb = number
        if sna:
            store.rkmtb = sna

        store.save(update_fields=["rkmdb", "rkmtb"])

        return JsonResponse({
            "status": "updated",
            "mobile": mobile
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# للتأكد من وجود رقم النسخة
from django.conf import settings

from django.db.models.functions import Trim
@csrf_exempt
def check_store_by_rkmdb(request):

    # ✅ امنع GET من البداية
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "POST only"
        }, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        # ✅ تعريف المتغير بشكل آمن
        rkmdb = (data.get("rkmdb") or data.get("number") or "").strip()

        if not rkmdb:
            return JsonResponse({
                "status": "error",
                "message": "يرجى إدخال الرقم"
            }, status=400)

        # ✅ مقارنة مطبّعة
        for store in Store.objects.all():
            if str(store.rkmdb).strip() == rkmdb:
                return JsonResponse({
                    "status": "found",
                    "message": "القيمة موجودة بالموقع"
                })

        return JsonResponse({
            "status": "not_found",
            "message": "القيمة غير موجودة بالموقع"
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

