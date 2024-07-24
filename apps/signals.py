import os

from allauth.socialaccount.models import SocialAccount
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.models import User


@receiver(post_save, sender=SocialAccount)
def post_save_socialaccount(sender, instance: SocialAccount, **kwargs):
    user: User = instance.user
    photo_url = instance.extra_data.get('photo_url')
    if photo_url:
        import requests
        r = requests.get(photo_url, allow_redirects=True)  # to get content after redirection

        if r.status_code == 200:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(r.content)
            img_temp.flush()

            try:
                user.image.save(os.path.basename(photo_url), File(img_temp), save=True)
            except:
                pass


''''
https://t.me/i/userpic/320/u-C-e3ovVhVMfnaM_0_8fjXmc7vqhT95WeiQD7pPwuslJIjrRT69eNnS6SkWnMzN.jpg

https://cdn4.cdn-telegram.org/file/n4eDRFM7zj2ZcVkLG2-d2F4qq4kVowOPfSSteycuE_WlqDO9BcxtUhlLeYhlklspDBqKSZUG7Bd3cHTYOb_S_3EnDUoQvYllhQoi9vpU5__jhDEkXsClxGtozWR0dbmh16lkGzChnQYcehJPLRo_NHAFtluqNP0vJGnl0-p0i9TxnwJYb3ShyVIiV4_UgTnLIpQt3SgqPZb-rV2WGIDCV1EJ1TE63poClJFAtLKKCG4t3GBjiNvk0PoOlWPtRyhnxXJLDl9Yv3IdlwIujFqBjUkEB0tRFiNFVKoxlOQx7wO8O8g9GYdc5jBSlP1ucEDBSRjNnwWOYRqcDlFb_tAbSA.jpg


'''