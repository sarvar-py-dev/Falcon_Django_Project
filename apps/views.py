from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Q, Avg
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView

from apps.forms import UserRegisterModelForm, OrderCreateModelForm
from apps.models import Product, Category, User, CartItem, Address, Review, SiteSettings
from apps.models.order import Order, OrderItem
from apps.models.product import Favorite
from apps.tasks import send_to_email
from generate_pdf import make_pdf


# from django.core.cache import cache


class CategoryMixin:
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductListView(CategoryMixin, ListView):
    queryset = Product.objects.all()
    template_name = 'apps/product/product-list.html'
    context_object_name = 'products'

    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.GET.get('category')
        if tags_slug := self.request.GET.get('tag'):
            qs = qs.filter(tags__slug=tags_slug)
        elif category_slug:
            qs = qs.filter(category__slug=category_slug)
        if ordering := self.request.GET.get('sorting'):
            qs.order_by(ordering)
        if search := self.request.GET.get('search'):
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search) | Q(about__icontains=search))

        # if cache.get('product_list'):
        #     return cache.get('product_list')
        # cache.set('product_list', qs, timeout=7200)
        if self.request.user.is_authenticated and (self.request.user.has_pro or self.request.user.is_superuser or self.request.user.is_sta):
            return qs
        return qs.filter(is_premium=False)

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        avg_ratings = []
        blank_stars = []
        for product in ctx[self.context_object_name]:
            avg_rating = int(Review.objects.filter(product=product).aggregate(rating=Avg('rating'))['rating'] or 0)
            avg_ratings.append(avg_rating)
            blank_stars.append(5 - avg_rating)

        ctx['avg_ratings'] = avg_ratings
        ctx['blank_stars'] = blank_stars

        return ctx


class ProductDetailView(CategoryMixin, DetailView):
    queryset = Product.objects.all()
    template_name = 'apps/product/product-details.html'
    context_object_name = 'product'

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        avg_rating = int(Review.objects.filter(product=self.object).aggregate(rating=Avg('rating'))['rating'])
        ctx['avg_rating'] = avg_rating
        ctx['blank_star'] = 5 - avg_rating

        return ctx


class SettingsUpdateView(LoginRequiredMixin, CategoryMixin, UpdateView):
    queryset = User.objects.all()
    template_name = 'apps/auth/settings.html'
    fields = 'first_name', 'last_name', 'email'
    success_url = reverse_lazy('settings_page')

    def get_object(self, queryset=None):
        return self.request.user


class RegisterCreateView(CreateView):
    template_name = 'apps/auth/register.html'
    form_class = UserRegisterModelForm
    success_url = reverse_lazy('list_view')

    def form_valid(self, form):
        form.save()
        send_to_email.delay('Your account has been created', form.data['email'])
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            redirect_to = reverse_lazy('list_view')
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('list_view')


class ReviewCreateView(CategoryMixin, CreateView):
    model = Review
    fields = 'name', 'review_text', 'email_address', 'rating'
    template_name = 'apps/product/product-details.html'
    success_url = reverse_lazy('detail_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        # form.instance.product = self.request.GET.get()
        return super().form_valid(form)


class CartListView(CategoryMixin, ListView):
    queryset = CartItem.objects.all()
    template_name = 'apps/shopping/shopping-cart.html'
    context_object_name = 'shopping_cart'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        qs = self.get_queryset()

        context.update(
            **qs.aggregate(
                total_sum=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100),
                total_count=Sum(F('quantity'))
            )
        )

        return context


def update_quantity(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(CartItem, pk=pk)
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            product.quantity = new_quantity
            product.save()

            total_sum = CartItem.objects.aggregate(
                total_sum=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100)
            )['total_sum'] or 0

            total_count = CartItem.objects.aggregate(
                total_count=Sum('quantity')
            )['total_count'] or 0

            return JsonResponse({'new_quantity': new_quantity, 'total_sum': total_sum, 'total_count': total_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class CartDeleteView(DeleteView):
    model = CartItem
    success_url = reverse_lazy('cart_page')


class AddToCartView(View):
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, id=pk)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return redirect('cart_page')


class AddressCreateView(CategoryMixin, CreateView):
    model = Address
    template_name = 'apps/address/create-address.html'
    fields = 'city', 'street', 'zip_code', 'phone', 'full_name'
    context_object_name = 'create_address'
    success_url = reverse_lazy("checkout_page")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AddressUpdateView(CategoryMixin, UpdateView):
    model = Address
    template_name = 'apps/address/update-address.html'
    fields = 'city', 'street', 'phone', 'zip_code'
    success_url = reverse_lazy('checkout_page')


class CheckoutListView(LoginRequiredMixin, CategoryMixin, ListView):
    template_name = 'apps/shopping/checkout.html'
    model = CartItem
    context_object_name = 'cart_items'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        qs = self.get_queryset()

        context.update(
            **qs.aggregate(
                subtotal=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100),
                shipping_cost=Sum(F('product__shipping_cost'))
            )
        )
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['tax'] = SiteSettings.objects.first().tax
        return context


class OrderListView(CategoryMixin, ListView):
    model = Order
    template_name = 'apps/orders/order-list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['tax'] = SiteSettings.objects.first().tax

        return context


class OrderDetailView(CategoryMixin, DetailView):
    model = Order
    template_name = 'apps/orders/order-details.html'
    context_object_name = 'order'

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        qs = OrderItem.objects.filter(order_id=context['order'].id)

        context.update(
            **qs.aggregate(
                subtotal=Sum(F('quantity') * (F('product__price') * (
                        100 - F('product__discount')) / 100)),
                shipping_cost=Sum(F('product__shipping_cost'))
            )
        )
        context['tax'] = SiteSettings.objects.first().tax
        return context


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('orders_list')


class OrderCreateView(LoginRequiredMixin, CategoryMixin, CreateView):
    model = Order
    template_name = 'apps/shopping/checkout.html'
    form_class = OrderCreateModelForm
    success_url = reverse_lazy('orders_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CustomerListView(CategoryMixin, ListView):
    model = User
    template_name = 'apps/customers/customers.html'
    paginate_by = 10
    context_object_name = 'customers_list'

    def get(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return super().get(request, *args, **kwargs)
        return redirect('list_view')


class FavouriteView(LoginRequiredMixin, CategoryMixin, View):
    def get(self, request, pk, *args, **kwargs):
        obj, created = Favorite.objects.get_or_create(user=request.user, product_id=pk)
        if not created:
            obj.delete()
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        else:
            return redirect('product_detail', pk=pk)


class OrderPdfCreateView(View):
    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        order = Order.objects.filter(pk=pk)
        if file := order.pdf_file:
            pass

        else:
            make_pdf(order)
