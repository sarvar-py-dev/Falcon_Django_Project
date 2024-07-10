from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView

from apps.forms import UserRegisterModelForm
from apps.models import Product, Category, User, CartItem, Address
from apps.tasks import send_to_email


class ProductListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/product/product-list.html'
    context_object_name = 'products'

    paginate_by = 2

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
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductDetailView(DetailView):
    queryset = Product.objects.all()
    template_name = 'apps/product/product-details.html'
    context_object_name = 'product'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


class SettingsUpdateView(LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    template_name = 'apps/auth/settings.html'
    fields = 'first_name', 'last_name', 'email'
    success_url = reverse_lazy('settings_page')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


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


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('list_view')


class CartView(ListView):
    queryset = CartItem.objects.all()
    template_name = 'apps/product/shopping-cart.html'
    context_object_name = 'shopping_cart'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()

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


class AddressCreateView(CreateView):
    model = Address
    template_name = 'apps/address/create-address.html'
    fields = 'city', 'street', 'zip_code', 'phone', 'full_name'
    context_object_name = 'create_address'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)