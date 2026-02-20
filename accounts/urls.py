from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("addresses/", views.AddressListView.as_view(), name="addresses"),
    path("addresses/new/", views.AddressCreateView.as_view(), name="address_new"),
    path("addresses/<int:pk>/edit/", views.AddressUpdateView.as_view(), name="address_edit"),
    path("users/", views.UsersListView.as_view(), name="users"),
    path("staff/new/", views.StaffCreateView.as_view(), name="staff_new"),
    path("users/<int:pk>/toggle/", views.toggle_user_active, name="user_toggle"),
]
