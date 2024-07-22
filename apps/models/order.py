from django.db.models import Model, CharField, ForeignKey, CASCADE, TextChoices, PositiveIntegerField, OneToOneField, \
    DateField, Sum, F, FileField

from apps.models import CreatedBaseModel


class Order(CreatedBaseModel):
    class Status(TextChoices):
        PROCESSING = 'processing', 'Processing'
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
    pdf_file = FileField(upload_to='order/pdf/', null=True, blank=True)

    @property
    def total(self):
        return self.order_items.aggregate(
            total=Sum(F('quantity') * (F('product__price') * (
                    100 - F('product__discount')) / 100)) + Sum(F('product__shipping_cost'))
        )


class OrderItem(Model):
    product = ForeignKey('apps.Product', CASCADE)
    order = ForeignKey('apps.Order', CASCADE, related_name='order_items')
    quantity = PositiveIntegerField()

    @property
    def amount(self):
        return self.quantity * self.product.new_price


class CreditCard(CreatedBaseModel):
    order = OneToOneField('apps.Order', CASCADE)
    number = CharField(max_length=16)
    cvv = CharField(max_length=3)
    expire_date = DateField()
    owner = ForeignKey('apps.User', CASCADE)
