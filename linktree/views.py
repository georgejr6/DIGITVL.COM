from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Create your views here.
from rest_framework import views, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from accounts.models import User
from linktree.models import LinkTree
from linktree.permission import LinkUpdatePermission
from linktree.serializers import LinkTreeSerializer, DataSerialzier


class LinkTreeCreateApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DataSerialzier

    @swagger_auto_schema(operation_description="Add Multiple Social Links on profile. the structure of this API is: '{'data':[{'title': 'instagram', 'url': 'https://instagram.com/xyz'}, {'title': 'facebook', 'www.facebook/com/xyz'}]}' \n\n",
                         request_body=DataSerialzier,
                         responses={200: openapi.Response('Response description', DataSerialzier)})
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid(raise_exception=True):
            print(serializer.data['data'])
            for link_tree_data in serializer.data['data']:
                LinkTree.objects.create(artist=request.user, title=link_tree_data['title'], url=link_tree_data['url'])
            return views.Response(serializer.data, status=status.HTTP_200_OK)

        # if serializer.is_valid(raise_exception=True):
        #     serializer.save(artist=self.request.user)

        return views.Response(serializer.data, status=status.HTTP_200_OK)


class GetLinkTreeApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LinkTreeSerializer

    @swagger_auto_schema(
        operation_description="Fetch Social Links of artist by their username_slug.' \n\n",
        responses={200: openapi.Response('Response description', LinkTreeSerializer)})
    def get(self, request, username_slug, *args, **kwargs):
        link_tree_data = LinkTree.objects.filter(artist__username_slug=username_slug)
        resp_obj = dict(
            link_tree_data=self.serializer_class(link_tree_data, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)

    # def get_queryset(self):
    #     """
    #     """
    #
    #     username_params = self.request.query_params.get('username', None)
    #     if username_params is not None:
    #         queryset = LinkTree.objects.filter(artist__username=self.request.query_params.get('username', None))
    #         return queryset
    #     elif self.request.user is not None:
    #         queryset = LinkTree.objects.filter(artist=self.request.user)
    #         return queryset
    #     return []


class GetCurrentUserLinkTreeApiView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LinkTreeSerializer

    @swagger_auto_schema(
        operation_description="Fetch Social Links of current user. \n\n",
        responses={200: openapi.Response('Response description', LinkTreeSerializer)})
    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)

        link_tree_data = user.artists_url.all()
        resp_obj = dict(
            link_tree_data=self.serializer_class(link_tree_data, context={"request": request}, many=True).data,

        )
        return views.Response(resp_obj, status=status.HTTP_200_OK)


class LinkUpdateApiView(RetrieveUpdateDestroyAPIView):
    permission_classes = [LinkUpdatePermission]
    lookup_field = 'id'
    serializer_class = LinkTreeSerializer
    queryset = LinkTree.objects.all()
    schema = None

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        # set partial=True to update a data partially
        serializer = self.serializer_class(instance=instance, data=request.data,
                                           partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            output = "Successfully url updated"
            content1 = {'success': [output]}
            content = {'status': True, 'message': content1, 'result': serializer.data}
            return views.Response(content, status=status.HTTP_200_OK)
        else:
            content = {'status': False, 'message': serializer.errors, 'result': {}}
            return views.Response(content, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # delete_action(instance, instance.id)
            instance.delete()
            content = {'status': True, 'message': {"Successfully deleted"}}
            return views.Response(content, status=status.HTTP_200_OK)
        except LinkTree.DoesNotExist:
            content = {'status': False, 'message': {"something went wrong"}}
            return views.Response(content, status=status.HTTP_200_OK)
