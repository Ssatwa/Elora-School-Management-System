from django.contrib import admin

from apps.finance.models import FeeStructure, Invoice, Payment, PaymentAllocation, Receipt

admin.site.register(FeeStructure)
admin.site.register(Invoice)
admin.site.register(Payment)
admin.site.register(PaymentAllocation)
admin.site.register(Receipt)
