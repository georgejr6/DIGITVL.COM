from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from beats.views import StandardResultsSetPagination
from .models import Blogs
from .serializers import BlogSerializer
from rest_framework.permissions import IsAdminUser


# Create your views here


class BlogCreateApiView(views.APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        error_result = {}
        serializer = BlogSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            new_blog = serializer.save(added_by=self.request.user)
            new_blog.save()
            output = "your blog is added."
            content = {'status': True, 'message': output, 'result': serializer.data,
                       }
            # feeds handling
            # create_action(request.user, 'posted a tweet', new_t, verb_id=1)
            return Response(content, status=status.HTTP_200_OK)
        content = {'status': False, 'message': serializer.errors, 'result': error_result}
        return Response(content, status=status.HTTP_200_OK)


class BlogsDetailApiView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = BlogSerializer

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, slug, *args, **kwargs):
        blog_detail = get_object_or_404(Blogs, slug=slug)
        resp_obj = dict(
            blog_detail=self.serializer_class(blog_detail, context={"request": request}).data)
        return views.Response(resp_obj, status=status.HTTP_200_OK)


class BlogsListView(ListAPIView):
    schema = None
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    queryset = Blogs.objects.select_related('added_by').all()
    serializer_class = BlogSerializer
