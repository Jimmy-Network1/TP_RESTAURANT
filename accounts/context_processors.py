def _group_names(user):
    if not user.is_authenticated:
        return set()
    return {g.strip().lower() for g in user.groups.values_list("name", flat=True)}


def role_flags(request):
    user = request.user
    groups = _group_names(user)
    is_manager = user.is_superuser or user.is_staff or bool(groups.intersection({"gerant", "manager", "admin"}))
    is_server = "serveur" in groups
    is_cook = "cuisinier" in groups
    is_cashier = "caissier" in groups
    is_delivery = "livreur" in groups
    is_client = "client" in groups or (user.is_authenticated and not (is_manager or is_server or is_cook or is_cashier or is_delivery))
    return {
        "is_manager": is_manager,
        "is_server": is_server,
        "is_cook": is_cook,
        "is_cashier": is_cashier,
        "is_delivery": is_delivery,
        "is_client": is_client,
    }
