from abc import ABC

from rest_framework import serializers

from xrpwallet.models import XRPWallet


class UserXrpWalletDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = XRPWallet
        fields = ('id', 'xrp_public_address', 'xrp_balance', 'xrp_token_earn', 'xrp_sequence')


class SendXrpSerializer(serializers.Serializer):
    public_address = serializers.CharField(max_length=400)
    xrp_amount = serializers.DecimalField(max_digits=6, decimal_places=2)
