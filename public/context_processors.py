def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def cart_count(request):
    cart = request.session.get("cart", {})
    try:
        count = sum(int(v) for v in cart.values())
    except Exception:
        count = 0
    user = request.user
    groups = _group_names(user)
    is_staff_role = user.is_superuser or user.is_staff or groups.intersection(
        {"gerant", "manager", "admin", "serveur", "cuisinier", "caissier", "livreur"}
    )
    is_client_role = "client" in groups
    return {"cart_count": count, "is_staff_role": bool(is_staff_role), "is_client_role": bool(is_client_role)}
