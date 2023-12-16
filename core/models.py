from datetime import date, timedelta

from collections.abc import Iterable
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from .choices import InstallmentType, PaymentStatus


class TimeStampModel(models.Model):
    """Abstract model for provides created_at and updated_at timestamps."""

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-created_on',)


class Country(models.Model):
    name = models.CharField(max_length=255)
    iso_code = models.CharField(max_length=2, unique=True)
    currency_code = models.CharField(max_length=3, unique=True)
    currency_symbol = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return str(self.name)


class Shareholder(TimeStampModel):
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Share(TimeStampModel):
    shareholder = models.ForeignKey(Shareholder, on_delete=models.CASCADE)
    annual_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Share duration in years",
                                           validators=[
                                               MinValueValidator(1),
                                               MaxValueValidator(5),
                                           ])
    start_date = models.DateField(default=timezone.now)
    installment_type = models.CharField(max_length=20, choices=InstallmentType.choices)
    custom_installment_period = models.PositiveIntegerField(
        help_text="Custom Installment Period", blank=True, null=True)
    custom_installment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Share for {self.shareholder} (Rs.{self.annual_amount})"

    @property
    def share_payments(self):
        return self.payment_set.all()

    def calculate_installment_amount(self):
        if self.installment_type == 'monthly':
            return self.annual_amount / (12 * self.duration)
        elif self.installment_type == 'quarterly':
            return self.annual_amount / (4 * self.duration)
        elif self.installment_type == 'half_yearly':
            return self.annual_amount / (2 * self.duration)
        elif self.installment_type == 'annual':
            return self.annual_amount / self.duration
        elif self.installment_type == 'custom':
            return self.custom_installment_amount

    def get_remaining_installments(self):
        # today = timezone.now().date()
        paid_installments = Payment.objects.filter(share=self).count()
        total_installments = (self.duration * 12) if self.installment_type == 'monthly' else (self.duration * 4) if self.installment_type == 'quarterly' else (self.duration * 2) if self.installment_type == 'half-yearly' else self.duration
        amount = total_installments - paid_installments
        return round(amount, 2)

    def get_outstanding_amount(self):
        paid_amount = Payment.objects.filter(share=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        amount = self.annual_amount - paid_amount
        return round(amount, 2)

    @property
    def total_installment_amount(self):
        """
        Returns the total installment amount for this share.
        """
        if self.custom_installment_period and self.custom_installment_amount:
            # Use custom values if provided
            amount = self.custom_installment_period * self.custom_installment_amount
            return round(amount, 2)
        else:
            amount = self.duration * self.calculate_installment_amount()
            return round(amount, 2)

    # @staticmethod
    def generate_payment_schedule(self):
        """
        Generates a dictionary with dates and amounts for each installment.

        Args:
            self: A Share model instance.

        Returns:
            A dictionary with keys as dates (datetime.date) and values as amounts (Decimal).
        """
        payment_schedule = {}
        installment_amount = self.calculate_installment_amount()
        current_date = self.start_date

        # Loop based on chosen installment type and duration
        if self.installment_type == 'monthly':
            for _ in range(12 * self.duration):
                payment_schedule[current_date.isoformat()] = round(installment_amount, 2)
                current_date += timedelta(days=30)
        elif self.installment_type == 'quarterly':
            for _ in range(4 * self.duration):
                payment_schedule[current_date.isoformat()] = round(installment_amount, 2)
                current_date += timedelta(days=90)
        elif self.installment_type == 'half-yearly':
            for _ in range(2 * self.duration):
                payment_schedule[current_date.isoformat()] = round(installment_amount, 2)
                current_date += timedelta(days=180)
        elif self.installment_type == 'annual':
            for _ in range(self.duration):
                payment_schedule[current_date.isoformat()] = round(installment_amount, 2)
                current_date += timedelta(days=365)
        elif self.installment_type == 'custom':
            if self.custom_installment_period:
                for _ in range(self.duration):
                    payment_schedule[current_date.isoformat()] = round(self.custom_installment_amount, 2)
                    current_date += timedelta(days=self.custom_installment_period)
        return payment_schedule


class Payment(TimeStampModel):
    share = models.ForeignKey(Share, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=24, choices=PaymentStatus.choices,
                              default=PaymentStatus.PENDING)
    payment_date = models.DateField(blank=True, null=True)
    allocated_installment = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"Payment of Rs.{self.amount} on {self.due_date} for Share {self.share}"
