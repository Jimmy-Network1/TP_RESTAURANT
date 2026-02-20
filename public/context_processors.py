def cart_count(request):
    cart = request.session.get("cart", {})
    try:
        count = sum(int(v) for v in cart.values())
    except Exception:
        count = 0
    return {"cart_count": count}
