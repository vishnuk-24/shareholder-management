from django.contrib import admin

from .models import Country, Share, Shareholder, Payment

admin.site.register(Country)
admin.site.register(Shareholder)
admin.site.register(Share)
admin.site.register(Payment)
