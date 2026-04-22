from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

from accounts.models import Customer

from stores.models import Store

from accounts.models import Supplier

from .models import PointsTransaction, DeleteSync
from django.shortcuts import get_object_or_404

from django.utils.dateparse import parse_date, parse_datetime
from django.db.models import Q
from datetime import datetime
from decimal import Decimal, InvalidOperation

from core.access_dedupe import dedupe_keep_oldest_for_value

#Ø·Ú¾Ø·ÂµØ·Â¯Ø¸Ù¹Ø·Â±

# Ø·Ú¾Ø·ÂµØ·Â¯Ø¸Ù¹Ø·Â± Ø·Â§Ø¸â€žØ·Â¹Ø¸â€¦Ø¸â€žØ·Â§Ø·ØŒ Ø¸â€¦Ø¸â€  Ø·Â§Ø¸â€žØ¸â€¦Ø·Ú¾Ø·Â¬Ø·Â± Ø·Â¥Ø¸â€žØ¸â€° Ø·Â§Ø¸â€žØ·Â£Ø¸Æ’Ø·Â³Ø·Â³

@csrf_exempt

def merchant_customers_api(request, merchant_id):

    """

    API: Ø·Â¬Ø¸â€žØ·Â¨ Ø·Â¹Ø¸â€¦Ø¸â€žØ·Â§Ø·ØŒ Ø·Ú¾Ø·Â§Ø·Â¬Ø·Â± Ø¸â€¦Ø·Â¹Ø¸Ù¹Ø¸â€  (Ø¸â€šØ·Â±Ø·Â§Ø·ØŒØ·Â© Ø¸Ù¾Ø¸â€šØ·Â·)

    """



    store = Store.objects.filter(id=merchant_id).first()

    if not store:

        return JsonResponse({"error": "Merchant not found"}, status=404)



    customers = Customer.objects.filter(store=store).filter(

        Q(access_id__isnull=True) | Q(access_id=0) | Q(update_time__isnull=False)

    ).values(

        "id",        # -> Ù‡Ø°Ø§ Ù‡Ùˆ Ø§Ù„Ù…ÙØªØ§Ø­ Ø§Ù„Ø°Ù‡Ø¨ÙŠ

        "name",

        "phone",

        "access_id",

        "update_time",

    )



    return JsonResponse({

        "merchant_id": merchant_id,

        "customers": list(customers)

    })





@csrf_exempt

def merchant_suppliers_api(request, merchant_id):

    """

    API: Ø·Â¬Ø¸â€žØ·Â¨ Ø¸â€¦Ø¸Ë†Ø·Â±Ø·Â¯Ø¸Ù¹ Ø·Ú¾Ø·Â§Ø·Â¬Ø·Â± Ø¸â€¦Ø·Â¹Ø¸Ù¹Ø¸â€  (Ø¸â€šØ·Â±Ø·Â§Ø·ØŒØ·Â© Ø¸Ù¾Ø¸â€šØ·Â·)

    """



    store = Store.objects.filter(id=merchant_id).first()

    if not store:

        return JsonResponse({"error": "Merchant not found"}, status=404)



    suppliers = Supplier.objects.filter(store=store).filter(

        Q(access_id__isnull=True) | Q(access_id=0) | Q(update_time__isnull=False)

    ).values(

        "id",

        "name",

        "phone",

        "access_id",

        "update_time",

    )



    return JsonResponse({

        "merchant_id": merchant_id,

        "suppliers": list(suppliers)

    })



#Ø¸â€ Ø¸â€šØ¸â€ž Ø·Â§Ø¸â€žØ¸Æ’Ø·Â§Ø·Â´ Ø·Â¨Ø·Â§Ø¸Æ’

@csrf_exempt

def merchant_points_export_api(request, merchant_id):

    store = Store.objects.filter(id=merchant_id).first()

    if not store:

        return JsonResponse({"error": "Merchant not found"}, status=404)



    points = PointsTransaction.objects.filter(customer__store=store).filter(

        Q(access_id__isnull=True) | Q(access_id=0)
    ).select_related("customer")



    data = []

    for p in points:

        data.append({

            "id": p.id,# Ù‹Úºâ€â€˜ Ø¸â€¦Ø¸â€¡Ø¸â€¦ Ø¸â€ Ø·Â±Ø·Â¬Ø·Â¹ Ø¸â€ Ø·Â±Ø·Â¨Ø·Â· Ø·Â¹Ø¸â€žØ¸Ù¹Ø¸â€¡
            "points_id": p.id,
            "rkmamel_m": p.customer_id,

            "asm": p.customer.name,

            "amount": p.points,

            "trans_date": p.created_at.strftime("%Y-%m-%d"),

            "note": p.note or "",
            "access_id": p.access_id,
            "update_time": p.update_time,
        })



    return JsonResponse({

        "merchant_id": merchant_id,

        "points": data

    })

#Ø·Â§Ø·Â±Ø·Â¬Ø·Â§Ø·Â¹ Ø·Â±Ø¸â€šØ¸â€¦ Ø·Â§Ø¸â€žØ·Â³Ø·Â¬Ø¸â€ž

@csrf_exempt

def merchant_points_confirm_api(request):

    import json

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(data, list):
        return JsonResponse({"error": "Payload must be a JSON array"}, status=400)

    updated = 0
    for item in data:
        point_id = item.get("points_id", item.get("id"))
        access_id = item.get("access_id")
        if point_id in (None, "") or access_id in (None, ""):
            continue
        try:
            updated += PointsTransaction.objects.filter(
                id=int(point_id)
            ).update(
                access_id=int(access_id),
                update_time=None
            )
        except (ValueError, TypeError):
            continue

    return JsonResponse({"status": "ok", "updated": updated})

@csrf_exempt

def merchant_customers_confirm_api(request):

    import json



    data = json.loads(request.body)



    for item in data:

        Customer.objects.filter(

            id=int(item["customer_id"])

        ).update(

            access_id=int(item["access_id"]),

            update_time=None

        )



    return JsonResponse({"status": "ok"})





@csrf_exempt

def merchant_suppliers_confirm_api(request):

    import json



    data = json.loads(request.body)



    for item in data:

        Supplier.objects.filter(

            id=int(item["supplier_id"])

        ).update(

            access_id=int(item["access_id"]),

            update_time=None

        )



    return JsonResponse({"status": "ok"})



## Ø·Â§Ø·Â³Ø·Ú¾Ø¸Ù¹Ø·Â±Ø·Â§Ø·Â¯ Ø¸â€¦Ø¸â€  Ø·Â§Ø¸â€žØ·Â¨Ø·Â±Ø¸â€ Ø·Â§Ø¸â€¦Ø·Â¬



# accounts/views_api.py

from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse

from django.db.models import Q

import json



from stores.models import Store

from accounts.models import Customer



from django.db.models import Q



@csrf_exempt
def create_customer_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        access_id = data.get("access_id")
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "ÈíÇäÇÊ äÇÞÕÉ"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if access_id in ("", None):
            access_id = None
        else:
            access_id = int(access_id)

        # ÊÍÏíË ÕÑíÍ ÍÓÈ access_id (ÑÞã ÓÌá ÃßÓÓ) ÅÐÇ ßÇä ãæÌæÏÇ
        if access_id is not None:
            by_access = Customer.objects.filter(store=store, access_id=access_id).first()
            if by_access:
                Customer.objects.filter(id=by_access.id, store=store).update(
                    name=name,
                    phone=phone,
                    update_time=None
                )
                _clear_store_reset_marker(store.id)
                return JsonResponse({
                    "status": "updated",
                    "customer_id": by_access.id,
                    "id": by_access.id,
                })

        # fallback: ÇÈÍË ÈÇáÇÓã Ãæ ÇáåÇÊÝ
        existing = Customer.objects.filter(
            store=store
        ).filter(
            Q(name=name) | Q(phone=phone)
        ).only("id", "name", "phone", "access_id").first()

        if existing:
            # äÝÓ ÇáÑÞã æÇÓã ãÎÊáÝ -> äÝÓ ÇáÑÓÇáÉ ÇáÞÏíãÉ
            if existing.phone == phone and existing.name != name:
                return JsonResponse({
                    "status": "exists",
                    "message": "ÑÞã ÇáãæÈÇíá ãÓÌá ÈÇÓã ÂÎÑ áä íÊã ÅßãÇá ãÒÇãäÉ ÇáÝæÇÊíÑ ÇáÇ ÈÚÏ Íá ÇáãÔßáÉ . íÝÖá ÇáÊÃßÏ ãä äÞá ÇáÚãáÇÁ ãä ÝæÑã ÇáÚãáÇÁ ÇæáÇ",
                    "existing_name": existing.name,
                    "id": existing.id,
                    "customer_id": existing.id,
                })

            update_data = {}
            if access_id is not None and existing.access_id in (None, 0, ""):
                update_data["access_id"] = access_id
            if existing.name != name:
                update_data["name"] = name
            if existing.phone != phone:
                update_data["phone"] = phone
            if update_data:
                update_data["update_time"] = None
                Customer.objects.filter(id=existing.id, store=store).update(**update_data)

            _clear_store_reset_marker(store.id)
            return JsonResponse({
                "status": "exists",
                "id": existing.id,
                "customer_id": existing.id,
            })

        customer = Customer.objects.create(
            store=store,
            access_id=access_id,
            name=name,
            phone=phone,
        )

        _clear_store_reset_marker(store.id)
        return JsonResponse({
            "status": "created",
            "message": "Êã ÅäÔÇÁ ÇáÒÈæä ÈäÌÇÍ",
            "customer_id": customer.id,
            "id": customer.id,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def create_supplier_from_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        merchant_id = data.get("store")
        access_id = data.get("access_id")
        name = (data.get("name") or "").strip()
        phone = data.get("phone")

        if phone in ("", None):
            phone = None
        else:
            phone = str(phone).strip()

        if not merchant_id or not name:
            return JsonResponse({"error": "ÈíÇäÇÊ äÇÞÕÉ"}, status=400)

        store = Store.objects.filter(id=merchant_id).first()
        if not store:
            return JsonResponse({"error": "Merchant not found"}, status=404)

        if access_id in ("", None):
            access_id = None
        else:
            access_id = int(access_id)

        # ÊÍÏíË ÕÑíÍ ÍÓÈ access_id (ÑÞã ÓÌá ÃßÓÓ) ÅÐÇ ßÇä ãæÌæÏÇ
        if access_id is not None:
            by_access = Supplier.objects.filter(store=store, access_id=access_id).first()
            if by_access:
                Supplier.objects.filter(id=by_access.id, store=store).update(
                    name=name,
                    phone=phone,
                    update_time=None
                )
                _clear_store_reset_marker(store.id)
                return JsonResponse({
                    "status": "updated",
                    "supplier_id": by_access.id,
                    "id": by_access.id,
                })

        # fallback: ÈÇáÇÓã
        existing = Supplier.objects.filter(store=store, name=name).first()
        if existing:
            update_data = {}
            if access_id is not None and existing.access_id in (None, 0, ""):
                update_data["access_id"] = access_id
            if existing.phone != phone:
                update_data["phone"] = phone
            if update_data:
                update_data["update_time"] = None
                Supplier.objects.filter(id=existing.id, store=store).update(**update_data)
            _clear_store_reset_marker(store.id)
            return JsonResponse({
                "status": "exists",
                "id": existing.id,
                "supplier_id": existing.id,
            })

        supplier = Supplier.objects.create(
            store=store,
            access_id=access_id,
            name=name,
            phone=phone,
        )

        _clear_store_reset_marker(store.id)
        return JsonResponse({
            "status": "created",
            "supplier_id": supplier.id,
            "id": supplier.id,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt

def create_cashback_from_access(request, merchant_id):

    if request.method != "POST":

        return JsonResponse({"error": "POST only"}, status=405)



    try:

        data = json.loads(request.body.decode("utf-8"))



        rkmamel = data.get("rkmamel")  # Ø·Â±Ø¸â€šØ¸â€¦ Ø·Â§Ø¸â€žØ·Â¹Ø¸â€¦Ø¸Ù¹Ø¸â€ž Ø·Â¨Ø·Â§Ø¸â€žØ·Â¨Ø·Â±Ø¸â€ Ø·Â§Ø¸â€¦Ø·Â¬

        access_id = data.get("access_id")  # ID Ø³Ø¬Ù„ Ø§Ù„Ø§ÙƒØ³Ø³

        customer_name = (data.get("customer_name") or "").strip()

        amount = data.get("amount")

        trans_date = data.get("trans_date")

        note = data.get("note", "")



        if not customer_name or amount in (None, "") or not trans_date:

            return JsonResponse({"error": "Ø·Â¨Ø¸Ù¹Ø·Â§Ø¸â€ Ø·Â§Ø·Ú¾ Ø¸â€ Ø·Â§Ø¸â€šØ·ÂµØ·Â©"}, status=400)


        # Preserve fractional cashback values and support Access decimal comma.
        try:
            amount_value = Decimal(str(amount).strip().replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            return JsonResponse({"error": "Invalid amount"}, status=400)



        store = Store.objects.filter(id=merchant_id).first()

        if not store:

            return JsonResponse({"error": "Merchant not found"}, status=404)



        customer = Customer.objects.filter(

            store=store,

            name=customer_name

        ).first()



        if not customer:

            return JsonResponse({

                "error": "Ø·Â§Ø¸â€žØ·Â¹Ø¸â€¦Ø¸Ù¹Ø¸â€ž Ø·Ø›Ø¸Ù¹Ø·Â± Ø¸â€¦Ø¸Ë†Ø·Â¬Ø¸Ë†Ø·Â¯ Ø·Â¨Ø·Â§Ø¸â€žØ¸â€¦Ø·Ú¾Ø·Â¬Ø·Â±",

                "customer_name": customer_name

            }, status=400)



        date_only = parse_date(trans_date)

        if not date_only:

            return JsonResponse({"error": "Invalid trans_date"}, status=400)



        created_at = datetime.combine(date_only, datetime.min.time())

        # Ø¯Ø¹Ù… Ù‚Ø¯ÙŠÙ…: Ø¥Ø°Ø§ Ù…Ø§ ÙˆØµÙ„ access_id Ø§Ø³ØªØ®Ø¯Ù… rkmamel

        if access_id in ("", None):

            access_id = rkmamel



        try:
            access_id_int = int(access_id) if access_id not in ("", None) else None
        except (TypeError, ValueError):
            access_id_int = None
        if access_id_int == 0:
            access_id_int = None

        if access_id_int is not None:
            base_qs = PointsTransaction.objects.filter(customer__store=store)
            existing = (
                base_qs.filter(access_id=access_id_int)
                .order_by("id")
                .first()
            )
            if existing:
                PointsTransaction.objects.filter(id=existing.id).update(
                    customer=customer,
                    customer_name=customer_name,
                    transaction_type="add",
                    access_id=access_id_int,
                    points=amount_value,
                    note=note,
                    created_at=created_at,
                    update_time=None,
                )
                dedupe_keep_oldest_for_value(
                    base_qs,
                    field_name="access_id",
                    value=access_id_int,
                )
                _clear_store_reset_marker(store.id)
                return JsonResponse({
                    "status": "updated",
                    "points_id": existing.id,
                    "id": existing.id,
                })

        pt = PointsTransaction.objects.create(
            customer=customer,
            customer_name=customer_name,
            transaction_type="add",
            access_id=access_id_int,
            points=amount_value,
            note=note,
        )

        # Imported from Access: do not mark as locally updated.
        PointsTransaction.objects.filter(id=pt.id).update(
            created_at=created_at,
            update_time=None,
        )

        if access_id_int is not None:
            base_qs = PointsTransaction.objects.filter(customer__store=store)
            _, keep_id = dedupe_keep_oldest_for_value(
                base_qs,
                field_name="access_id",
                value=access_id_int,
            )
            if keep_id and keep_id != pt.id:
                PointsTransaction.objects.filter(id=keep_id).update(
                    customer=customer,
                    customer_name=customer_name,
                    transaction_type="add",
                    access_id=access_id_int,
                    points=amount_value,
                    note=note,
                    created_at=created_at,
                    update_time=None,
                )
                pt.id = keep_id

        # Ù‹Úºâ€â€˜ Ø¸â€ Ø·Â±Ø·Â¬Ø¸â€˜Ø·Â¹ ID Ø·Â³Ø·Â¬Ø¸â€ž Ø·Â§Ø¸â€žØ¸â€ Ø¸â€šØ·Â§Ø·Â·
        _clear_store_reset_marker(store.id)
        return JsonResponse({
            "status": "created",
            "points_id": pt.id,
            "id": pt.id,
        })



    except Exception as e:

        return JsonResponse({"error": str(e)}, status=500)



# Ø¸â€žØ·Ú¾Ø·Â±Ø·Â¬Ø¸Ù¹Ø·Â¹ Ø·Â±Ø¸â€šØ¸â€¦ Ø·Â§Ø¸â€žØ·Â¹Ø¸â€¦Ø¸Ù¹Ø¸â€ž Ø¸â€žØ¸â€žØ·Â£Ø¸Æ’Ø·Â³Ø·Â³

@csrf_exempt

def get_customer_id_for_access(request):

    if request.method != "POST":

        return JsonResponse({"error": "POST only"}, status=405)



    try:

        data = json.loads(request.body.decode("utf-8"))

        access_row_id = data.get("access_row_id")



        if not access_row_id:

            return JsonResponse({"error": "Missing access_row_id"}, status=400)



        pt = PointsTransaction.objects.filter(

            access_id=access_row_id

        ).select_related("customer").first()



        if not pt or not pt.customer_id:

            return JsonResponse({"error": "Not found"}, status=404)



        return JsonResponse({

            "access_row_id": access_row_id,

            "customer_id": pt.customer_id

        })



    except Exception as e:

        return JsonResponse({"error": str(e)}, status=500)

#Ø¸â€žØ¸â€žØ·Â§Ø·Â´Ø·Â¹Ø·Â§Ø·Â±Ø·Â§Ø·Ú¾

from django.http import JsonResponse

from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt

from .models import SystemNotification, AccountingClient

from django.db.models import Q

from django.db import models

@csrf_exempt

def accounting_notifications(request):

    access_id = request.GET.get("access_id")



    if not access_id:

        return JsonResponse({"error": "access_id required"}, status=400)



    try:

        AccountingClient.objects.get(access_id=access_id)

    except AccountingClient.DoesNotExist:

        return JsonResponse({"error": "invalid access_id"}, status=403)



    now = timezone.now()



    notifications = (

        SystemNotification.objects

        .filter(channel__in=["accounting", "both"])

        .filter(

            Q(expires_at__isnull=True) |

            Q(expires_at__gt=now)

        )

        .order_by("id")

    )



    data = []



    for n in notifications:

        data.append({

            "id": n.id,

            "title": n.title,

            "message": n.message,

            "severity": n.severity,

            "created_at": n.created_at.isoformat(),

            "target_store_id": n.target_store_id,  # Ã¢Â­Ú¯ Ø¸â€¦Ø¸â€¡Ø¸â€¦ Ø¸â€žØ¸â€žØ·Â¥Ø¸Æ’Ø·Â³Ø·Â³

        })



    return JsonResponse(

        {"notifications": data},

        json_dumps_params={"ensure_ascii": False}

    )



#Ø¸â€žØ·Â§Ø·Â®Ø·Ú¾Ø·Â¨Ø·Â§Ø·Â± Ø¸â€¦Ø¸â€  Ø·Â§Ø¸Æ’Ø·Â³Ø·Â³ Ø·Â§Ø·Â°Ø·Â§ Ø·Â§Ø¸â€žØ·Â­Ø·Â³Ø·Â§Ø·Â¨ Ø¸Ù¾Ø·Â¹Ø·Â§Ø¸â€ž

from django.http import JsonResponse

from accounts.models import Store



def merchant_status(request, merchant_id):

    store = Store.objects.filter(id=merchant_id).first()



    if not store:

        return JsonResponse(

            {"error": "Store not found"},

            status=404

        )



    return JsonResponse({

        "id": store.id,

        "is_active": store.is_active,

    })

#Ø¸â€žØ¸â€žØ·Ú¾Ø·Â­Ø·Â¯Ø¸Ù¹Ø·Â«

# views.py

from django.http import JsonResponse

from .models import AppUpdate



def check_update(request):

    app = AppUpdate.objects.get(app_name="alaman")

    return JsonResponse({

        "version": app.version,

        "prices_version": app.prices_version,

    })




























@csrf_exempt
def merchant_delete_sync_export_api(request, merchant_id):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    reset_marker_exists = DeleteSync.objects.filter(
        source_flag=2,
        store_model_name=DeleteSync.RESET_MARKER_MODEL,
        store_record_id=merchant_id,
    ).exists()
    if reset_marker_exists:
        return JsonResponse(
            {
                "status": "blocked",
                "error": "Êã ÊÝÑíÛ ÈíÇäÇÊ ÇáãÊÌÑ. ÝÚøá ÅÚÇÏÉ ÅÑÓÇá ßÇãá ÇáÈíÇäÇÊ ãä ÅÚÏÇÏÇÊ ÈÑäÇãÌ ÇáÃßÓÓ Ëã ÃÚÏ ÇáãÍÇæáÉ.",
                "merchant_id": merchant_id,
                "store_was_reset": True,
                "warning_code": "STORE_RESET_RESEND_REQUIRED",
                "warning_message": (
                    "Êã ÊÝÑíÛ ÈíÇäÇÊ ÇáãÊÌÑ. ÞÈá ÇáãÒÇãäÉ¡ ÝÚøá ÅÚÇÏÉ ÅÑÓÇá ßÇãá ÇáÈíÇäÇÊ ãä ÅÚÏÇÏÇÊ ÈÑäÇãÌ ÇáÃßÓÓ Ëã ÃÚÏ ÇáãÍÇæáÉ."
                ),
            },
            status=409,
            json_dumps_params={"ensure_ascii": False},
        )

    rows = DeleteSync.objects.filter(source_flag=2).order_by("id")
    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "source_flag": r.source_flag,
            "store_record_id": r.store_record_id,
            "store_model_name": r.store_model_name,
            "access_record_id": r.access_record_id,
            "access_table_name": r.access_table_name,
        })

    return JsonResponse(
        {
            "merchant_id": merchant_id,
            "rows": data,
            "store_was_reset": False,
            "warning_code": "",
            "warning_message": "",
        },
        json_dumps_params={"ensure_ascii": False},
    )


@csrf_exempt
def merchant_delete_sync_import_api(request, merchant_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    import json

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(payload, list):
        return JsonResponse({"error": "Payload must be a JSON array"}, status=400)

    created_count = 0
    for item in payload:
        # Any row imported via this endpoint is, by definition, from Access.
        source_flag = 1
        store_record_id = item.get("store_record_id")
        store_model_name = item.get("store_model_name")
        access_record_id = item.get("access_record_id")
        access_table_name = item.get("access_table_name")

        exists = DeleteSync.objects.filter(
            source_flag=source_flag,
            store_record_id=store_record_id,
            store_model_name=store_model_name,
            access_record_id=access_record_id,
            access_table_name=access_table_name,
        ).exists()
        if exists:
            continue

        DeleteSync.objects.create(
            source_flag=source_flag,
            store_record_id=store_record_id,
            store_model_name=store_model_name,
            access_record_id=access_record_id,
            access_table_name=access_table_name,
        )
        created_count += 1

    applied_result = _apply_delete_sync_from_access(merchant_id)
    pending_after = DeleteSync.objects.filter(source_flag=1).count()
    return JsonResponse({
        "status": "ok",
        "created": created_count,
        "applied": applied_result["applied"],
        "cleared": applied_result["cleared"],
        "errors": applied_result["errors"],
        "pending_after": pending_after,
    })


def _apply_delete_sync_from_access(merchant_id):
    from accounts.models import Customer, Supplier
    from dashboard.models import Expense
    from orders.models import Order, OrderItem
    from products.models import Category, Product

    model_map = {
        "accounts.Customer": Customer,
        "accounts.Supplier": Supplier,
        "products.Category": Category,
        "products.Product": Product,
        "orders.Order": Order,
        "orders.OrderItem": OrderItem,
        "accounts.PointsTransaction": PointsTransaction,
        "dashboard.Expense": Expense,
    }
    short_to_full = {
        "Customer": "accounts.Customer",
        "Supplier": "accounts.Supplier",
        "Category": "products.Category",
        "Product": "products.Product",
        "Order": "orders.Order",
        "OrderItem": "orders.OrderItem",
        "PointsTransaction": "accounts.PointsTransaction",
        "Expense": "dashboard.Expense",
    }

    table_to_model = {
        "ÃÓãÇÁ ÇáÚãáÇÁ": "accounts.Customer",
        "ÇáãæÑÏæä": "accounts.Supplier",
        "almontg": "products.Category",
        "ÇáÃÕäÇÝ": "products.Product",
        "fatoraaam": "orders.Order",
        "ÝÇÊæÑÉ": "orders.OrderItem",
        "cashback": "accounts.PointsTransaction",
        "ÇáÕÑÝíÇÊ": "dashboard.Expense",
    }

    rows = DeleteSync.objects.filter(source_flag=1).order_by("id")
    applied = 0
    cleared = 0
    errors = 0

    for row in rows:
        model_key = (row.store_model_name or "").strip()
        if model_key in short_to_full:
            model_key = short_to_full[model_key]
        elif model_key.lower() in {k.lower() for k in short_to_full.keys()}:
            for k, v in short_to_full.items():
                if model_key.lower() == k.lower():
                    model_key = v
                    break
        if not model_key:
            model_key = table_to_model.get((row.access_table_name or "").strip(), "")
        model_cls = model_map.get(model_key)

        if not model_cls:
            errors += 1
            row.delete()
            cleared += 1
            continue

        qs = model_cls.objects.none()

        # Preferred delete target in store is store_record_id.
        if row.store_record_id not in (None, 0, ""):
            qs = model_cls.objects.filter(id=row.store_record_id)
        elif row.access_record_id not in (None, 0, ""):
            # Fallback by Access key mapping.
            if model_key == "orders.Order":
                qs = model_cls.objects.filter(accounting_invoice_number=row.access_record_id)
            else:
                qs = model_cls.objects.filter(access_id=row.access_record_id)

        # Scope to merchant whenever possible.
        if model_key == "orders.OrderItem":
            qs = qs.filter(order__store_id=merchant_id)
        elif model_key == "accounts.PointsTransaction":
            qs = qs.filter(customer__store_id=merchant_id)
        else:
            if hasattr(model_cls, "store_id"):
                qs = qs.filter(store_id=merchant_id)

        try:
            target = qs.first()
            if target:
                if model_key == "orders.Order":
                    # Delete items first with skip flags to avoid touching parent update_time
                    # while parent is being removed by sync.
                    for item in OrderItem.objects.filter(order_id=target.id):
                        item._skip_delete_sync = True
                        item._skip_order_update_touch = True
                        item.delete()
                    target._skip_delete_sync = True
                    target._skip_order_update_touch = True
                    target.delete()
                else:
                    target._skip_delete_sync = True
                    target._skip_order_update_touch = True
                    target.delete()
                applied += 1
        except Exception:
            errors += 1
        finally:
            row.delete()
            cleared += 1

    return {"applied": applied, "cleared": cleared, "errors": errors}


def _clear_store_reset_marker(store_id):
    DeleteSync.objects.filter(
        source_flag=2,
        store_model_name=DeleteSync.RESET_MARKER_MODEL,
        store_record_id=store_id,
    ).delete()


@csrf_exempt
def merchant_delete_sync_apply_api(request, merchant_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    result = _apply_delete_sync_from_access(merchant_id)
    return JsonResponse({"status": "ok", **result})


@csrf_exempt
def merchant_delete_sync_confirm_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    import json

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(payload, list):
        return JsonResponse({"error": "Payload must be a JSON array"}, status=400)

    ids = []
    for item in payload:
        row_id = item.get("id")
        if row_id in (None, ""):
            continue
        ids.append(int(row_id))

    if ids:
        DeleteSync.objects.filter(id__in=ids).delete()

    return JsonResponse({"status": "ok", "deleted": len(ids)})






