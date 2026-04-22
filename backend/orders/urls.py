from django.urls import path
from .views import (
    cart_page,
    cart_add,
    cart_update,
    cart_remove,
    checkout_now,
    order_detail_page,
    payment_page,
)

urlpatterns = [
    path("cart/", cart_page, name="cart_page"),
    path("cart/add/<int:product_id>/", cart_add, name="cart_add"),
    path("cart/update/<int:item_id>/", cart_update, name="cart_update"),
    path("cart/remove/<int:item_id>/", cart_remove, name="cart_remove"),
    path("checkout/", checkout_now, name="checkout_now"),
    path("<int:order_id>/", order_detail_page, name="order_detail"),
    path("<int:order_id>/payment/", payment_page, name="payment_page"),
]
