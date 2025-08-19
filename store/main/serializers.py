from rest_framework import serializers
from .models import Store, StoreReport

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = "__all__"

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreReport
        fields = "__all__"   # include all fields from StoreReport
