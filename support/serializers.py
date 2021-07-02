from rest_framework import serializers
from .models import Support


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = ['name', 'email', 'support_type', 'support_message']
