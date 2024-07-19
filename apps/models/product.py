from datetime import timedelta

from django.db.models import Model, CharField, IntegerField, ImageField, ForeignKey, CASCADE, JSONField, \
    ManyToManyField, PositiveSmallIntegerField, CheckConstraint, Q
from django.db.models import PositiveIntegerField
from django.db.models import TextField, \
    EmailField, BooleanField
from django.utils.timezone import now
from django_ckeditor_5.fields import CKEditor5Field
from mptt.models import MPTTModel, TreeForeignKey

from apps.models import SlugBaseModel, CreatedBaseModel


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
        return self.product_review.count()

    @property
    def first_five(self):
        if self.specification:
            return list(self.specification.values())[:5]


class ProductImage(Model):
    image = ImageField(upload_to='product_image/')
    product = ForeignKey('apps.Product', CASCADE, related_name='images')

    def __str__(self):
        return self.product.name


class Review(CreatedBaseModel):
    RATING = (
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    )

    name = CharField(max_length=255)
    review_text = TextField()
    email_address = EmailField()
    product = ForeignKey('apps.Product', CASCADE, related_name='product_review')
    rating = IntegerField(choices=RATING)
    user = ForeignKey('apps.User', CASCADE, related_name='user_review')

    def __str__(self):
        return F'Review_NAME-{self.name},   Product_NAME-{self.product.name}'


class Favorite(Model):
    is_liked = BooleanField(blank=True, null=True)
    user = ForeignKey('apps.User', CASCADE, related_name='like')
    product = ForeignKey('apps.Product', CASCADE, related_name='product_like')

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
