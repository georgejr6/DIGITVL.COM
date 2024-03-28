# Define the network client

import json
from decimal import Decimal

from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import views, permissions, status
from rest_framework.response import Response
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountInfo
from xrpl.wallet import generate_faucet_wallet

from accounts.models import User
from xrpwallet.models import XRPWallet
import xrpl
from xrpl.wallet import Wallet

from xrpwallet.serializers import SendXrpSerializer


class CreateUserXrpWalletView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    schema = None

    def post(self, request, *args, **kwargs):

        user = get_object_or_404(User, id=request.user.id)
        if user is not None:
            JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
            client = JsonRpcClient(JSON_RPC_URL)
            # https://xrpl.org/xrp-testnet-faucet.html

            test_wallet = generate_faucet_wallet(client, debug=True)

            # Create an account str from the wallet
            test_account = test_wallet.classic_address
            secret_key = test_wallet.seed

            acct_info = AccountInfo(
                account=test_account,
                ledger_index="validated",
                strict=True,
            )
            xrp_response = client.request(acct_info)
            result = xrp_response.result

            XRPWallet.objects.get_or_create(user=user, xrp_public_address=test_account,
                                            xrp_balance=result["account_data"]["Balance"],
                                            xrp_sequence=result["account_data"]["Sequence"])

            return Response({'status': True, 'wallet': 'Successfully wallet added', 'data': result,
                             'secret_key': secret_key},
                            status=status.HTTP_200_OK)

        else:
            return Response({'status': True, 'wallet': 'something went wrong!'},
                            status=status.HTTP_200_OK)


# Based on User Listening History
class SendXrpToUsersView(views.APIView):
    serializer_class = SendXrpSerializer
    schema = None

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = {}
        public_address = request.POST.get('public_address')
        xrp_amount = request.POST.get('xrp_amount')
        xrp_amount = Decimal(xrp_amount)

        test_wallet = Wallet(seed="snR5QCYdRf5rvHPmaXaEXtXtAPkR2", sequence=30862095)
        print(test_wallet.classic_address)
        # "rMCcNuTcajgw7YTgBy1sys3b89QqjUrMpH"

        # Connect ----------------------------------------------------------------------

        testnet_url = "https://s.altnet.rippletest.net:51234"
        client = xrpl.clients.JsonRpcClient(testnet_url)

        # Prepare transaction ----------------------------------------------------------
        my_payment = xrpl.models.transactions.Payment(
            account=test_wallet.classic_address,
            amount=xrpl.utils.xrp_to_drops(xrp_amount),
            destination=public_address,
        )
        print("Payment object:", my_payment)

        # Sign transaction -------------------------------------------------------------
        signed_tx = xrpl.transaction.safe_sign_and_autofill_transaction(
            my_payment, test_wallet, client)
        max_ledger = signed_tx.last_ledger_sequence
        tx_id = signed_tx.get_hash()
        print("Signed transaction:", signed_tx)
        print("Transaction cost:", xrpl.utils.drops_to_xrp(signed_tx.fee), "XRP")
        print("Transaction expires after ledger:", max_ledger)
        print("Identifying hash:", tx_id)

        try:

            tx_response = xrpl.transaction.send_reliable_submission(signed_tx, client)

            explorer_link = f'https://testnet.xrpl.org/transactions/{tx_id}'
            metadata = tx_response.result.get("meta", {})
            if metadata.get("TransactionResult"):
                print("Result code:", metadata["TransactionResult"])
            if metadata.get("delivered_amount"):
                print("XRP delivered:", xrpl.utils.drops_to_xrp(
                    metadata["delivered_amount"]))
            transaction_response = tx_response.result
            # print(transaction_response)
            data = {
                "Transaction Response": transaction_response,
                # "Signed transaction": signed_tx,
                "Transaction cost XRP": xrpl.utils.drops_to_xrp(signed_tx.fee),
                "Transaction expires after ledger": max_ledger,
                "Identifying hash": tx_id,
                "Explore Link": explorer_link,
                "Result Code": metadata["TransactionResult"],
                "XRP Delivered": metadata["delivered_amount"],
            }

            return Response({'status': True, 'message': 'Transaction Successfully Succeed.', 'data': data},
                            status=status.HTTP_200_OK)
        except Exception as e:
            # exit(f"Submit failed: {e}")
            return Response({'status': True, 'message': 'Transaction Failed.', 'data': e})


# view for adding balance to user account
class AddXrpToBalanceView(views.APIView):
    # serializer_class = SendXrpSerializer
    permission_classes = (permissions.IsAuthenticated,)
    schema = None

    def post(self, request, *args, **kwargs):
        try:
            xrp_token_amount_earn = request.POST.get('xrp_token_amount_earn')

            user_xrp_wallet = XRPWallet.objects.get(user=request.user)
            user_xrp_wallet.xrp_token_earn = F('xrp_token_earn') + xrp_token_amount_earn
            user_xrp_wallet.save()
            return Response({'status': True, 'message': 'token earn successfully added.'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': True, 'message': 'something went wrong.'},
                            status=status.HTTP_200_OK)

