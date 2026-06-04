import time
from decimal import Decimal

from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from mobile_sync.models import MobileDeleteSync
from accounts.models import Customer, normalize_phone_number
from products.models import Category
from products.models import Product
from products.models import ProductBarcode
from stores.models import Store
from accounts.models import StoreUser
from django.db import transaction


def _now_minute():
    return int(time.time() // 60)


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default=0.0):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_bool(value, default=False):
    if value in ("", None):
        return default
    if isinstance(value, bool):
        return value
    text = str(value).lower()
    if text in ("1", "true", "yes", "y"):
        return True
    if text in ("0", "false", "no", "n"):
        return False
    return default


def _to_str(value, default=""):
    if value in (None, ""):
        return default
    return str(value)


def _serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "access_id": category.access_id,
        "update_time": category.update_time or 0,
    }


def _serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price if isinstance(product.price, Decimal) else product.price),
        "description": product.description or "",
        "price2": float(product.price2 if isinstance(product.price2, Decimal) else product.price2),
        "price3": float(product.price3 if isinstance(product.price3, Decimal) else product.price3),
        "unit2": product.unit2 or "",
        "unit2_price": float(product.unit2_price if isinstance(product.unit2_price, Decimal) else product.unit2_price),
        "unit2_pieces": float(product.unit2_pieces if isinstance(product.unit2_pieces, Decimal) else product.unit2_pieces),
        "show_price": product.show_price,
        "buy_price": float(product.buy_price if isinstance(product.buy_price, Decimal) else product.buy_price),
        "stock": product.stock,
        "main_image": product.main_image.name if product.main_image else "",
        "category_id": product.category_id,
        "category2_id": product.category2_id,
        "active": product.active,
        "update_time": product.update_time or 0,
    }


def _serialize_barcode(barcode):
    return {
        "id": barcode.id,
        "value": barcode.value,
        "product_id": barcode.product_id,
        "access_id": barcode.access_id,
        "update_time": barcode.update_time or 0,
    }


def _serialize_customer(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address or "",
        "note": customer.note or "",
        "balance": float(customer.balance),
        "opening_balance": float(customer.opening_balance),
        "access_id": customer.access_id,
        "update_time": customer.update_time or 0,
    }


def _apply_category_change(store, payload, server_id=None):
    name = _to_str(payload.get("name")).strip()
    access_id = _to_int(payload.get("access_id"))
    if not name:
        raise ValueError("Category name is required")

    now_minute = _now_minute()
    obj = None
    if server_id:
        obj = Category.objects.filter(id=server_id, store=store).first()
    if not obj:
        obj = Category.objects.filter(store=store, name=name).first()

    if obj:
        update_fields = {"name": name, "update_time": now_minute}
        if access_id is not None and obj.access_id in (None, 0, ""):
            update_fields["access_id"] = access_id
        Category.objects.filter(id=obj.id, store=store).update(**update_fields)
        obj.refresh_from_db()
        return obj, "updated"

    obj = Category.objects.create(
        store=store,
        access_id=access_id,
        name=name,
        update_time=now_minute,
    )
    return obj, "created"


def _apply_product_change(store, payload, server_id=None, category_resolver=None):
    name = _to_str(payload.get("name")).strip()
    if not name:
        raise ValueError("Product name is required")

    now_minute = _now_minute()
    category = None
    category2 = None
    if category_resolver:
        category = category_resolver(payload.get("category_server_id"), payload.get("category_local_id"))
        category2 = category_resolver(payload.get("category2_server_id"), payload.get("category2_local_id"))

    obj = None
    if server_id:
        obj = Product.objects.filter(id=server_id, store=store).first()
    if not obj:
        obj = Product.objects.filter(store=store, name=name).first()

    update_fields = {
        "name": name,
        "price": _to_float(payload.get("price")),
        "description": _to_str(payload.get("description")),
        "price2": _to_float(payload.get("price2", payload.get("searg"))),
        "price3": _to_float(payload.get("price3", payload.get("a3"))),
        "unit2": _to_str(payload.get("unit2", payload.get("wahda2"))),
        "unit2_price": _to_float(payload.get("unit2_price", payload.get("nshra"))),
        "unit2_pieces": _to_float(payload.get("unit2_pieces", payload.get("motger"))),
        "show_price": _to_bool(payload.get("show_price"), True),
        "buy_price": _to_float(payload.get("buy_price")),
        "stock": int(_to_float(payload.get("stock"))),
        "active": _to_bool(payload.get("active"), True),
        "update_time": now_minute,
    }
    if category is not None:
        update_fields["category"] = category
    if category2 is not None:
        update_fields["category2"] = category2

    if obj:
        if access_id := _to_int(payload.get("access_id")):
            if obj.access_id in (None, 0, ""):
                update_fields["access_id"] = access_id
        Product.objects.filter(id=obj.id, store=store).update(**update_fields)
        obj.refresh_from_db()
        return obj, "updated"

    obj = Product.objects.create(
        store=store,
        access_id=_to_int(payload.get("access_id")),
        name=name,
        price=update_fields["price"],
        description=update_fields["description"],
        price2=update_fields["price2"],
        price3=update_fields["price3"],
        unit2=update_fields["unit2"],
        unit2_price=update_fields["unit2_price"],
        unit2_pieces=update_fields["unit2_pieces"],
        show_price=update_fields["show_price"],
        buy_price=update_fields["buy_price"],
        stock=update_fields["stock"],
        category=category,
        category2=category2,
        active=update_fields["active"],
        update_time=now_minute,
    )
    return obj, "created"


def _apply_barcode_change(store, payload, server_id=None, product_resolver=None):
    value = _to_str(payload.get("value", payload.get("barkod"))).strip()
    if not value:
        raise ValueError("Barcode value is required")

    product = None
    if product_resolver:
        product = product_resolver(payload.get("product_id"), payload.get("product_access_id"), payload.get("product_server_id"), payload.get("product_local_id"))
    if not product:
        raise ValueError("Product is required for barcode")

    now_minute = _now_minute()
    obj = None
    if server_id:
        obj = ProductBarcode.objects.filter(id=server_id, product__store=store).first()
    if not obj:
        obj = ProductBarcode.objects.filter(product=product, value=value).first()

    if obj:
        ProductBarcode.objects.filter(id=obj.id).update(
            product=product,
            value=value,
            update_time=now_minute,
        )
        obj.refresh_from_db()
        return obj, "updated"

    obj = ProductBarcode.objects.create(
        product=product,
        value=value,
        update_time=now_minute,
    )
    return obj, "created"


def _apply_customer_change(store, payload, server_id=None):
    name = _to_str(payload.get("name")).strip()
    phone = normalize_phone_number(_to_str(payload.get("phone")).strip())
    address = _to_str(payload.get("address")).strip()
    note = _to_str(payload.get("note")).strip()
    access_id = _to_int(payload.get("access_id"))
    if not name and not phone:
        raise ValueError("Customer name or phone is required")

    if not name:
        name = phone

    now_minute = _now_minute()
    obj = None
    if server_id:
        obj = Customer.objects.filter(id=server_id, store=store).first()
    if not obj and access_id not in (None, 0, ""):
        obj = Customer.objects.filter(store=store, access_id=access_id).first()
    if not obj and phone:
        obj = Customer.objects.filter(store=store, phone=phone).first()
    if not obj:
        obj = Customer.objects.filter(store=store, name=name).first()

    update_fields = {
        "name": name,
        "phone": phone,
        "address": address,
        "note": note,
        "balance": Decimal(str(_to_float(payload.get("balance"), 0.0))),
        "opening_balance": Decimal(str(_to_float(payload.get("opening_balance"), 0.0))),
        "update_time": now_minute,
    }
    if access_id is not None:
        update_fields["access_id"] = access_id

    if obj:
        Customer.objects.filter(id=obj.id, store=store).update(**update_fields)
        obj.refresh_from_db()
        return obj, "updated"

    obj = Customer.objects.create(
        store=store,
        access_id=access_id,
        name=name,
        phone=phone,
        address=address,
        note=note,
        balance=update_fields["balance"],
        opening_balance=update_fields["opening_balance"],
        update_time=now_minute,
    )
    return obj, "created"


@api_view(["GET"])
@permission_classes([AllowAny])
def categories_pull(request):
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

    qs = Category.objects.filter(store_id=merchant_id_int).order_by("id")

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
            "id": c.id,
            "name": c.name,
            "access_id": c.access_id,
            "update_time": c.update_time or 0,
        }
        for c in qs.only("id", "name", "access_id", "update_time")
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def customers_pull(request):
    merchant_id = request.query_params.get("merchant_id")
    since = request.query_params.get("since")

    if not merchant_id:
        return Response({"detail": "merchant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        merchant_id_int = int(merchant_id)
    except (TypeError, ValueError):
        return Response({"detail": "merchant_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    store = Store.objects.filter(id=merchant_id_int).first()
    if not store:
        return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

    qs = Customer.objects.filter(store_id=merchant_id_int).order_by("id")
    if since not in (None, "", "0"):
        try:
            since_int = int(since)
        except (TypeError, ValueError):
            return Response({"detail": "since must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(update_time__gt=since_int)

    data = [
        _serialize_customer(customer)
        for customer in qs.only(
            "id",
            "name",
            "phone",
            "address",
            "note",
            "balance",
            "opening_balance",
            "access_id",
            "update_time",
        )
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def stores_pull(request):
    since = request.query_params.get("since")

    qs = Store.objects.filter(is_active=True).order_by("id")
    if since not in (None, "", "0"):
        try:
            since_int = int(since)
        except (TypeError, ValueError):
            return Response({"detail": "since must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(update_time__gt=since_int)

    data = [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "mobile": s.mobile or "",
            "access_id": s.access_id,
            "is_active": s.is_active,
            "update_time": s.update_time or 0,
        }
        for s in qs.only("id", "name", "slug", "mobile", "access_id", "is_active", "update_time")
    ]

    return Response(
        {
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


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
            "description": p.description or "",
            "price2": float(p.price2 if isinstance(p.price2, Decimal) else p.price2),
            "price3": float(p.price3 if isinstance(p.price3, Decimal) else p.price3),
            "unit2": p.unit2 or "",
            "unit2_price": float(p.unit2_price if isinstance(p.unit2_price, Decimal) else p.unit2_price),
            "unit2_pieces": float(
                p.unit2_pieces if isinstance(p.unit2_pieces, Decimal) else p.unit2_pieces
            ),
            "show_price": p.show_price,
            "buy_price": float(p.buy_price if isinstance(p.buy_price, Decimal) else p.buy_price),
            "stock": p.stock,
            "main_image": p.main_image.name if p.main_image else "",
            "category_id": p.category_id,
            "category2_id": p.category2_id,
            "active": p.active,
            "update_time": p.update_time or 0,
        }
        for p in qs.only(
            "id",
            "name",
            "price",
            "description",
            "price2",
            "price3",
            "unit2",
            "unit2_price",
            "unit2_pieces",
            "show_price",
            "buy_price",
            "stock",
            "main_image",
            "category_id",
            "category2_id",
            "active",
            "update_time",
        )
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def store_users_pull(request):
    merchant_id = request.query_params.get("merchant_id")
    since = request.query_params.get("since")

    if not merchant_id:
        return Response({"detail": "merchant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        merchant_id_int = int(merchant_id)
    except (TypeError, ValueError):
        return Response({"detail": "merchant_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    store = Store.objects.select_related("owner").filter(id=merchant_id_int).first()
    if not store:
        return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

    qs = StoreUser.objects.filter(store_id=merchant_id_int).order_by("id")
    if since not in (None, "", "0"):
        try:
            since_int = int(since)
        except (TypeError, ValueError):
            return Response({"detail": "since must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(update_time__gt=since_int)

    data = []
    if since in (None, "", "0"):
        owner = store.owner
        owner_name = (owner.get_full_name() or owner.username or store.name).strip()
        data.append(
            {
                "id": -owner.id,
                "store_id": store.id,
                "identifier": owner.username,
                "name": owner_name,
                "warehouse_id": None,
                "access_id": None,
                "is_active": owner.is_active and store.is_active,
                "has_password": owner.has_usable_password(),
                "is_owner": True,
                "update_time": store.update_time or 0,
            }
        )

    data.extend(
        {
            "id": u.id,
            "store_id": u.store_id,
            "identifier": u.identifier,
            "name": u.name,
            "warehouse_id": u.warehouse_id,
            "access_id": u.access_id,
            "is_active": u.is_active,
            "has_password": bool(u.password),
            "is_owner": False,
            "update_time": u.update_time or 0,
        }
        for u in qs.select_related("warehouse").only(
            "id",
            "store_id",
            "identifier",
            "name",
            "warehouse_id",
            "access_id",
            "is_active",
            "password",
            "update_time",
        )
    )

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def store_user_login(request):
    payload = request.data if isinstance(request.data, dict) else None
    if not payload:
        return Response({"detail": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)

    merchant_id = _to_int(payload.get("merchant_id"))
    identifier = _to_str(payload.get("identifier")).strip()
    password = _to_str(payload.get("password"))

    if merchant_id is None:
        return Response({"detail": "merchant_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not identifier:
        return Response({"detail": "identifier is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({"detail": "password is required"}, status=status.HTTP_400_BAD_REQUEST)

    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
    if not store.is_active:
        return Response({"detail": "Store is inactive"}, status=status.HTTP_409_CONFLICT)

    owner_candidate = authenticate(username=identifier, password=password)
    if owner_candidate is not None and owner_candidate == store.owner:
        owner_name = (owner_candidate.get_full_name() or owner_candidate.username or store.name).strip()
        return Response(
            {
                "status": "ok",
                "store": {
                    "id": store.id,
                    "name": store.name,
                    "slug": store.slug,
                    "is_active": store.is_active,
                },
                "user": {
                    "id": -owner_candidate.id,
                    "identifier": owner_candidate.username,
                    "name": owner_name,
                    "is_active": owner_candidate.is_active,
                    "is_owner": True,
                },
            }
        )

    user = StoreUser.objects.filter(store=store, identifier__iexact=identifier).first()
    if not user:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    if not user.is_active:
        return Response({"detail": "User is inactive"}, status=status.HTTP_409_CONFLICT)
    if not user.check_password(password):
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(
        {
            "status": "ok",
            "store": {
                "id": store.id,
                "name": store.name,
                "slug": store.slug,
                "is_active": store.is_active,
            },
            "user": {
                "id": user.id,
                "identifier": user.identifier,
                "name": user.name,
                "is_active": user.is_active,
                "is_owner": False,
            },
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def sync_push(request):
    if request.method != "POST":
        return Response({"detail": "POST only"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    payload = request.data if isinstance(request.data, dict) else None
    if not payload:
        return Response({"detail": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)

    merchant_id = _to_int(payload.get("merchant_id"))
    changes = payload.get("changes", [])
    if merchant_id is None:
        return Response({"detail": "merchant_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(changes, list):
        return Response({"detail": "changes must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    store = Store.objects.filter(id=merchant_id).first()
    if not store:
        return Response({"detail": "Merchant not found"}, status=status.HTTP_404_NOT_FOUND)

    applied = []
    errors = []
    category_local_to_server = {}
    product_local_to_server = {}
    customer_local_to_server = {}

    def resolve_category(server_id, local_id):
        if server_id not in (None, ""):
            obj = Category.objects.filter(id=int(server_id), store_id=merchant_id).first()
            if obj:
                return obj
        if local_id not in (None, ""):
            mapped = category_local_to_server.get(int(local_id))
            if mapped:
                return mapped
        return None

    def resolve_product(product_id=None, product_access_id=None, product_server_id=None, product_local_id=None):
        if product_server_id not in (None, ""):
            obj = Product.objects.filter(id=int(product_server_id), store_id=merchant_id).first()
            if obj:
                return obj
        if product_local_id not in (None, ""):
            mapped = product_local_to_server.get(int(product_local_id))
            if mapped:
                return mapped
        if product_id not in (None, ""):
            obj = Product.objects.filter(id=int(product_id), store_id=merchant_id).first()
            if obj:
                return obj
        if product_access_id not in (None, ""):
            return Product.objects.filter(store_id=merchant_id, access_id=int(product_access_id)).first()
        return None

    def resolve_barcode_product(payload_item):
        return resolve_product(
            payload_item.get("product_id"),
            payload_item.get("product_access_id"),
            payload_item.get("product_server_id"),
            payload_item.get("product_local_id"),
        )

    upserts = [item for item in changes if str(item.get("action", "upsert")).lower() != "delete"]
    deletes = [item for item in changes if str(item.get("action", "upsert")).lower() == "delete"]

    def entity_priority(item):
        return {"category": 0, "product": 1, "barcode": 2}.get(str(item.get("entity")), 99)

    upserts.sort(key=entity_priority)
    deletes.sort(key=entity_priority, reverse=True)

    try:
        with transaction.atomic():
            for item in upserts:
                entity = str(item.get("entity", "")).lower()
                local_id = item.get("local_id")
                server_id = item.get("server_id")
                payload_item = item.get("payload") or {}

                if entity == "category":
                    obj, action = _apply_category_change(
                        store,
                        payload_item,
                        server_id=_to_int(server_id),
                    )
                    if local_id not in (None, ""):
                        category_local_to_server[int(local_id)] = obj
                    applied.append({
                        "entity": "category",
                        "action": action,
                        "local_id": local_id,
                        "server_id": obj.id,
                        "update_time": obj.update_time or 0,
                    })
                elif entity == "product":
                    obj, action = _apply_product_change(
                        store,
                        payload_item,
                        server_id=_to_int(server_id),
                        category_resolver=resolve_category,
                    )
                    if local_id not in (None, ""):
                        product_local_to_server[int(local_id)] = obj
                    applied.append({
                        "entity": "product",
                        "action": action,
                        "local_id": local_id,
                        "server_id": obj.id,
                        "update_time": obj.update_time or 0,
                    })
                elif entity == "barcode":
                    payload_item = dict(payload_item)
                    if "product_id" not in payload_item and "product_server_id" not in payload_item and "product_local_id" not in payload_item:
                        payload_item["product_server_id"] = item.get("product_server_id")
                        payload_item["product_local_id"] = item.get("product_local_id")
                    obj, action = _apply_barcode_change(
                        store,
                        payload_item,
                        server_id=_to_int(server_id),
                        product_resolver=resolve_barcode_product,
                    )
                    applied.append({
                        "entity": "barcode",
                        "action": action,
                        "local_id": local_id,
                        "server_id": obj.id,
                        "update_time": obj.update_time or 0,
                    })
                elif entity == "customer":
                    obj, action = _apply_customer_change(
                        store,
                        payload_item,
                        server_id=_to_int(server_id),
                    )
                    if local_id not in (None, ""):
                        customer_local_to_server[int(local_id)] = obj
                    applied.append({
                        "entity": "customer",
                        "action": action,
                        "local_id": local_id,
                        "server_id": obj.id,
                        "update_time": obj.update_time or 0,
                    })

            for item in deletes:
                entity = str(item.get("entity", "")).lower()
                server_id = _to_int(item.get("server_id"))
                local_id = item.get("local_id")
                if server_id is None:
                    if local_id not in (None, ""):
                        applied.append({
                            "entity": entity,
                            "action": "skipped",
                            "local_id": local_id,
                            "server_id": None,
                        })
                    continue

                if entity == "barcode":
                    obj = ProductBarcode.objects.filter(id=server_id, product__store_id=merchant_id).first()
                    if obj:
                        obj._skip_mobile_delete_sync = True
                        obj.delete()
                        applied.append({
                            "entity": "barcode",
                            "action": "deleted",
                            "local_id": local_id,
                            "server_id": server_id,
                        })
                elif entity == "product":
                    obj = Product.objects.filter(id=server_id, store_id=merchant_id).first()
                    if obj:
                        for barcode in ProductBarcode.objects.filter(product_id=obj.id):
                            barcode._skip_mobile_delete_sync = True
                            barcode.delete()
                        obj._skip_mobile_delete_sync = True
                        obj.delete()
                        applied.append({
                            "entity": "product",
                            "action": "deleted",
                            "local_id": local_id,
                            "server_id": server_id,
                        })
                elif entity == "category":
                    obj = Category.objects.filter(id=server_id, store_id=merchant_id).first()
                    if obj:
                        obj._skip_mobile_delete_sync = True
                        obj.delete()
                        applied.append({
                            "entity": "category",
                            "action": "deleted",
                            "local_id": local_id,
                            "server_id": server_id,
                        })
                elif entity == "customer":
                    obj = Customer.objects.filter(id=server_id, store_id=merchant_id).first()
                    if obj:
                        obj._skip_mobile_delete_sync = True
                        obj.delete()
                        applied.append({
                            "entity": "customer",
                            "action": "deleted",
                            "local_id": local_id,
                            "server_id": server_id,
                        })

        return Response({"status": "ok", "applied": applied, "errors": errors})
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def deletes_pull(request):
    merchant_id = request.query_params.get("merchant_id")
    since = request.query_params.get("since")

    if not merchant_id:
        return Response({"detail": "merchant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        merchant_id_int = int(merchant_id)
    except (TypeError, ValueError):
        return Response({"detail": "merchant_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    qs = MobileDeleteSync.objects.filter(merchant_id=merchant_id_int).order_by("id")
    if since not in (None, "", "0"):
        try:
            since_int = int(since)
        except (TypeError, ValueError):
            return Response({"detail": "since must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(id__gt=since_int)

    items = [
        {
            "id": row.id,
            "store_record_id": row.store_record_id,
            "store_model_name": row.store_model_name,
            "access_record_id": row.access_record_id,
            "access_table_name": row.access_table_name,
        }
        for row in qs
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": items,
            "max_id": max((x["id"] for x in items), default=0),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def barcodes_pull(request):
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

    qs = ProductBarcode.objects.filter(product__store_id=merchant_id_int).order_by("id")

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
            "id": b.id,
            "value": b.value,
            "product_id": b.product_id,
            "access_id": b.access_id,
            "update_time": b.update_time or 0,
        }
        for b in qs.only("id", "value", "product_id", "access_id", "update_time")
    ]

    return Response(
        {
            "merchant_id": merchant_id_int,
            "items": data,
            "max_update_time": max((x["update_time"] for x in data), default=0),
        }
    )
