from django.urls import path

from .views import (
    BrfnLoginView,
    BrfnLogoutView,
    after_login,
    expire_ephemeral_session,
    init_ephemeral_session,
    register_choice,
    register_customer,
    register_producer,
)

urlpatterns = [
    path("login/", BrfnLoginView.as_view(), name="login"),
    path("logout/", BrfnLogoutView.as_view(), name="logout"),
    path("session/init/", init_ephemeral_session, name="init_ephemeral_session"),
    path("session/expire/", expire_ephemeral_session, name="expire_ephemeral_session"),
    path("after-login/", after_login, name="after_login"),
    path("register/", register_choice, name="register_choice"),
    path("register/customer/", register_customer, name="register_customer"),
    path("register/producer/", register_producer, name="register_producer"),
]
