from django.shortcuts import render

# Create your views here.
# views.py

from django.http import JsonResponse
from rest_framework import views
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import EscrowCreate, EscrowFinish
from .models import XRPLEscrowTransaction

class CreateXRPLEscrow(views.APIView):
    def get(self, request, *args  ,**kwargs):
        sender = request.POST.get("sender")
        recipient = request.POST.get("recipient")
        amount = request.POST.get("amount")
        condition = request.POST.get("condition")
        client = JsonRpcClient("https://s1.ripple.com:51234/")
        escrow_create = EscrowCreate(
            account=sender,
            destination=recipient,
            amount=amount,
            condition=condition,
            cancel_after=...,
            finish_after=...,
            sequence=...,
            fee=...
        )
        signed_tx = escrow_create.sign(...)  # Sign the transaction
        response = client.submit(signed_tx)

        # Save transaction data to your model
        XRPLEscrowTransaction.objects.create(
            sender=sender,
            recipient=recipient,
            amount=amount,
            condition=condition,
            # ...
        )

        return JsonResponse({"message": "Escrow created successfully"})



def execute_escrow(request, escrow_id):
    escrow = XRPLEscrowTransaction.objects.get(pk=escrow_id)
    if not escrow.executed:
        escrow.executed = True
        escrow.save()
        return JsonResponse({"message": "Escrow executed"})
    else:
        return JsonResponse({"message": "Escrow already executed"})