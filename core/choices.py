from django.db import models
from django.utils.translation import gettext_lazy as _


class InstallmentType(models.TextChoices):
    MONTHLY = 'monthly', _("Monthly")
    QUARTERLY = 'quarterly', _("Quarterly")
    HALF_YEARLY = 'half_yearly', _("Half yearly")
    ANNUAL = 'annual', _("Annual")
    CUSTOM = 'custom', _("Custom")


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _("Pending")
    PAID = 'paid', _("Paid")
    OVERDUE = 'overdue', _("Overdue")
    CANCELLED = 'cancelled', _("Cancelled")
