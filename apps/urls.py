from django.contrib.auth.views import LoginView
from django.urls import path, include

from apps.models.order import Order
from apps.views import ProductListView, ProductDetailView, SettingsUpdateView, RegisterCreateView, LogoutView, \
    CartListView, \
    CartDeleteView, AddToCartView, update_quantity, AddressCreateView, CheckoutListView, AddressUpdateView, \
    ReviewCreateView, OrderListView, OrderDetailView, OrderDeleteView, OrderCreateView, CustomerListView, FavouriteView, \
    OrderPdfCreateView, CustomLoginView

urlpatterns = [
    path('', ProductListView.as_view(), name='list_view'),
    path('detail/<int:pk>', ProductDetailView.as_view(), name='detail_view'),
    path('settings', SettingsUpdateView.as_view(), name='settings_page'),
    path('register', RegisterCreateView.as_view(), name='register_page'),
    path('login', CustomLoginView.as_view(),name='login_page'),

    path('logout', LogoutView.as_view(), name='logout_page'),
    path('shopping-cart', CartListView.as_view(), name='cart_page'),
    path('shopping-cart/delete/<int:pk>', CartDeleteView.as_view(), name='cart_delete'),
    path('shopping-cart/add-to-cart/<int:pk>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update-quantity/<int:pk>/', update_quantity, name='update_quantity'),
    path('address-create', AddressCreateView.as_view(), name='create_address'),
    path('address-update/<int:pk>', AddressUpdateView.as_view(), name='update_address'),
    path('checkout', CheckoutListView.as_view(), name='checkout_page'),
    path('create-review', ReviewCreateView.as_view(), name='create_review'),
    path('orders', OrderListView.as_view(), name='orders_list'),
    path('order/<int:pk>', OrderDetailView.as_view(), name='order'),
    path('order-create', OrderCreateView.as_view(), name='create_order'),
    path('order/delete/<int:pk>', OrderDeleteView.as_view(), name='order_delete'),
    path('customers-list', CustomerListView.as_view(), name='customers_list'),
    path('favorite/<int:pk>', FavouriteView.as_view(), name='favorite_page'),
    path('download-pdf/<int:pk>', OrderPdfCreateView.as_view(), name='download_pdf')
]
