import datetime
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db.models import Model, CharField, IntegerField, ImageField, ForeignKey, CASCADE, TextField, \
    JSONField, DateField, ManyToManyField, EmailField, PositiveSmallIntegerField, SlugField, CheckConstraint, Q, \
    DateTimeField, BooleanField, TextChoices, PositiveIntegerField, OneToOneField
from django.utils.text import slugify
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field
from mptt.models import MPTTModel, TreeForeignKey


class User(AbstractUser):
    @property
    def cart_count(self):
        return self.cartitem_set.count()


class CreatedBaseModel(Model):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class SlugBaseModel(Model):
    name = CharField(max_length=255)
    slug = SlugField(max_length=255, unique=True, editable=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.name)
        while self.__class__.objects.filter(slug=self.slug).exists():
            self.slug += '-1'

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Category(SlugBaseModel, MPTTModel):
    parent = TreeForeignKey('self', CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']


class Tag(SlugBaseModel):
    pass


class Product(CreatedBaseModel):
    name = CharField(max_length=255)
    price = IntegerField()
    discount = PositiveSmallIntegerField(default=0, db_default=0)
    shipping_cost = IntegerField()
    description = CKEditor5Field()
    specification = JSONField(null=True, blank=True)
    about = CKEditor5Field()
    quantity = PositiveSmallIntegerField()
    category = ForeignKey('apps.Category', CASCADE)
    tags = ManyToManyField('apps.Tag', blank=True)

    class Meta:
        constraints = [
            CheckConstraint(check=Q(discount__lte=100), name='discount__lte__100')
        ]

    def __str__(self):
        return self.name

    @property
    def is_new(self):
        return self.created_at >= now() - timedelta(days=7)

    @property
    def new_price(self):
        return self.price * (100 - self.discount) // 100

    @property
    def review_num(self):
        return self.review_set.count()

    @property
    def first_five(self):
        if self.specification:
            return list(self.specification.values())[:5]


class Review(CreatedBaseModel):
    name = CharField(max_length=255)
    review_text = TextField()
    email_address = EmailField()
    product = ForeignKey('apps.Product', CASCADE)

    def __str__(self):
        return F'Review_NAME-{self.name},   Product_NAME-{self.product.name}'


class ProductImage(Model):
    image = ImageField(upload_to='product_image/')
    product = ForeignKey('apps.Product', CASCADE, related_name='images')

    def __str__(self):
        return self.product.name


class CartItem(Model):
    user = ForeignKey('apps.User', CASCADE)
    quantity = PositiveIntegerField(default=1)
    product = ForeignKey('apps.Product', CASCADE, related_name='product_cart')

    def __str__(self):
        return self.product.name

    @property
    def amount(self):
        return self.quantity * self.product.new_price


class Favorite(Model):
    is_liked = BooleanField(blank=True, null=True)
    user = ForeignKey('apps.User', CASCADE)
    product = ForeignKey('apps.Product', CASCADE, related_name='product_like')

    def __str__(self):
        return self.product.name


class Address(CreatedBaseModel):
    user = ForeignKey('apps.User', CASCADE)
    city = CharField(max_length=255)
    street = CharField(max_length=255)
    zip_code = PositiveIntegerField()
    phone = CharField(max_length=255)
    full_name = CharField(max_length=255)

    def __str__(self):
        return self.city


class Order(CreatedBaseModel):
    class Status(TextChoices):
        PROCESSING = 'Processing', 'Processing'
        ON_HOLD = 'on_hold', 'On Hold'
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'

    class PaymentMethod(TextChoices):
        PAYPAL = 'paypal', 'PayPal'
        CREDIT_CARD = 'credit_card', 'Credit Card'

    payment_method = CharField(max_length=25, choices=PaymentMethod.choices)
    status = CharField(max_length=25, choices=Status.choices, default=Status.PROCESSING)
    address = ForeignKey('apps.Address', CASCADE, related_name='orders')
    owner = ForeignKey('apps.User', CASCADE, related_name='orders')


class OrderItem(Model):
    product = ForeignKey('apps.Product', CASCADE)
    order = ForeignKey('apps.Order', CASCADE)
    quantity = PositiveIntegerField(default=1)


class CreditCard(CreatedBaseModel):
    order = OneToOneField('apps.Order', CASCADE)
    number = CharField(max_length=16)
    cvv = CharField(max_length=3)
    expire_data = DateField()


class SiteSettings(Model):
    tax = PositiveSmallIntegerField()
