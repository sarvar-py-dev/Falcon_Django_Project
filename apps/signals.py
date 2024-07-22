# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from apps.models import Order
# from apps.utils import make_pdf
#
#
# @receiver(post_save, sender=Order)
# def post_save_order(sender, instance: Order, **kwargs):
#     if kwargs.get('created'):
#         make_pdf(instance)
