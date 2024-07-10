from django.contrib.auth.views import LoginView
from django.urls import path, include

from apps.views import ProductListView, ProductDetailView, SettingsUpdateView, RegisterCreateView, LogoutView, CartView, \
    CartDeleteView, AddToCartView, update_quantity, AddressCreateView

urlpatterns = [
    path('', ProductListView.as_view(), name='list_view'),
    path('detail/<int:pk>', ProductDetailView.as_view(), name='detail_view'),
    path('settings', SettingsUpdateView.as_view(), name='settings_page'),
    path('register', RegisterCreateView.as_view(), name='register_page'),
    path('login', LoginView.as_view(
        template_name='apps/auth/login.html',
        redirect_authenticated_user=True,
        next_page='list_view'
    ), name='login_page'),
    path('logout', LogoutView.as_view(), name='logout_page'),
    path('shopping-cart', CartView.as_view(), name='cart_page'),
    path('shopping-cart/delete/<int:pk>', CartDeleteView.as_view(), name='cart_delete'),
    path('shopping-cart/add-to-cart/<int:pk>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update-quantity/<int:pk>/', update_quantity, name='update_quantity'),
    path('address-create', AddressCreateView.as_view(), name='create_address')
]
