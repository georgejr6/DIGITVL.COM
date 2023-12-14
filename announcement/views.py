# from django.shortcuts import render
#
# # Create your views here.
# from rest_framework.decorators import permission_classes
# from rest_framework.generics import ListAPIView
# from rest_framework.permissions import AllowAny
#
# from announcement.models import Announcement
# from announcement.serializers import AnnouncementSerializer
#
#
# @permission_classes([AllowAny])
# class GetAnnouncementApiView(ListAPIView):
#     queryset = Announcement.objects.all()
#     serializer_class = AnnouncementSerializer
