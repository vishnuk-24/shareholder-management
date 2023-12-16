from rest_framework import serializers
from .choices import InstallmentType
from .models import Shareholder, Share, Payment


class ShareholderModelSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField()

    class Meta:
        model = Shareholder
        fields = '__all__'

    def get_country_name(self, obj):
        return obj.country.name if obj.country else None


class ShareModelSerializer(serializers.ModelSerializer):
    shareholder = ShareholderModelSerializer()
    total_installment_amount = serializers.SerializerMethodField()
    remaining_installments = serializers.SerializerMethodField()
    outstanding_amount = serializers.SerializerMethodField()

    def validate(self, data):
        if data['installment_type'] == 'custom' and not data.get('custom_installment_amount'):
            raise serializers.ValidationError({'custom_installment_amount': 'Required for custom installment type.'})
        return super().validate(data)

    class Meta:
        model = Share
        fields = '__all__'

    def get_total_installment_amount(self, obj):
        return obj.total_installment_amount

    def get_remaining_installments(self, obj):
        return obj.get_remaining_installments()

    def get_outstanding_amount(self, obj):
        return obj.get_outstanding_amount()


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ('due_date', 'amount', 'status', 'payment_date', 'allocated_installment',)


class PaymentModelSerializer(serializers.ModelSerializer):
    share = serializers.PrimaryKeyRelatedField(queryset=Share.objects.all())
    due_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Payment
        fields = '__all__'


class ShareSerializer(serializers.ModelSerializer):
    shareholder = ShareholderModelSerializer(read_only=True)
    payment = PaymentSerializer(source='share_payments', many=True)
    total_installment_amount = serializers.SerializerMethodField()
    remaining_installments = serializers.SerializerMethodField()
    outstanding_amount = serializers.SerializerMethodField()
    payment_schedule = serializers.SerializerMethodField()

    class Meta:
        model = Share
        fields = (
            'pk', 'shareholder', 'annual_amount', 'duration', 'start_date', 'installment_type',
            'custom_installment_period', 'custom_installment_amount', 'total_installment_amount',
            'remaining_installments', 'outstanding_amount', 'payment_schedule', 'payment'
        )

    def get_total_installment_amount(self, obj):
        return obj.total_installment_amount

    def get_remaining_installments(self, obj):
        return obj.get_remaining_installments()

    def get_outstanding_amount(self, obj):
        return obj.get_outstanding_amount()

    def get_payment_schedule(self, obj):
        """
        Returns a dictionary with dates and amounts for each installment.
        """
        return obj.generate_payment_schedule()

    def validate(self, data):
        return super().validate(data)

    def create(self, validated_data):
        # Create a new Share and Payment objects
        share = Share.objects.create(**validated_data)
        installment_type = validated_data.get("installment_type")
        # Generate and save payment objects based on the payment schedule            
        payment_schedule = share.generate_payment_schedule()
        for date, amount in payment_schedule.items():
            if installment_type == InstallmentType.CUSTOM:
                Payment.objects.create(share=share, amount=amount)
            else:
                Payment.objects.create(share=share, due_date=date, amount=amount)
        return share

    def update(self, instance, validated_data):
        # Update Share and Payment objects
        updated_instance = super().update(instance, validated_data)
        payment_schedule = updated_instance.generate_payment_schedule()
        for date, amount in payment_schedule.items():
            payment, _ = Payment.objects.get_or_create(share=updated_instance, due_date=date)
            payment.amount = amount
            payment.save()
        return updated_instance


class ShareSummarySerializer(serializers.Serializer):
    month = serializers.IntegerField(required=False)
    year = serializers.IntegerField(required=False)
    total_collected = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expected = serializers.DecimalField(max_digits=10, decimal_places=2)
    due_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class InstallmentDueDetailsSerializer(serializers.ModelSerializer):
    shareholder_name = serializers.CharField(source='share.shareholder.name')
    mobile_number = serializers.CharField(source='share.shareholder.phone_number')
    due_date = serializers.DateField()
    # due_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_date = serializers.DateField(required=False)
    balance_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        exclude = ('created_on', 'updated_on', 'allocated_installment', 'share')

    def get_balance_amount(self, obj):
        return obj.share.get_remaining_installments()
