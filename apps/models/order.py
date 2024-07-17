from django.db.models import Model, CharField, ForeignKey, CASCADE, TextChoices, PositiveIntegerField, OneToOneField, \
    DateField

from apps.models import CreatedBaseModel


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
    order = ForeignKey('apps.Order', CASCADE, related_name='order_items')
    quantity = PositiveIntegerField()


class CreditCard(CreatedBaseModel):
    order = ForeignKey('apps.Order', CASCADE)
    number = CharField(max_length=16)
    cvv = CharField(max_length=3)
    expire_date = DateField()
    owner = ForeignKey('apps.User', CASCADE)
