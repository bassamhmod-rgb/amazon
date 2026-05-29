from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from products.models import Product


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def products_pull(request):
    merchant_id = request.query_params.get("merchant_id")
    since = request.query_params.get("since")

    if not merchant_id:
        return Response(
            {"detail": "merchant_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        merchant_id_int = int(merchant_id)
    except (TypeError, ValueError):
        return Response(
            {"detail": "merchant_id must be an integer"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = Product.objects.filter(store_id=merchant_id_int).order_by("id")

    if since not in (None, "", "0"):
        try:
            since_int = int(since)
        except (TypeError, ValueError):
            return Response(
                {"detail": "since must be an integer (minutes)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = qs.filter(update_time__gt=since_int)

    data = [
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price if isinstance(p.price, Decimal) else p.price),
            "update_time": p.update_time or 0,
        }
        for p in qs.only("id", "name", "price", "update_time")
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def sync_push(request):
    return Response(
        {
            "detail": "Not implemented yet. Send outbox events here.",
        },
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )

