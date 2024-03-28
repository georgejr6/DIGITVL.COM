import redis
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import permission_classes
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated

from advertisement.models import Advertisement
from advertisement.serializers import AdvertisementSerializer
from rest_framework import permissions, status, views

# connect to redis
redis_cache = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


@permission_classes([AllowAny])
class GetAdvertisementApiView(ListAPIView):
    queryset = Advertisement.objects.all().order_by('?')[:1]
    serializer_class = AdvertisementSerializer
    schema = None


class GiveRewardOnAdvertisement(views.APIView):
    permission_classes = [IsAuthenticated]
    queryset = Advertisement.objects.all()
    schema = None

    def post(self, request, poster_id, *args, **kwargs):
        try:
            poster_object = get_object_or_404(self.queryset, id=poster_id)

            total_views = redis_cache.incr(f'poster:{poster_object.id}:views')
            redis_cache.hincrby('users:{}:coins'.format(request.user.id), request.user.id, 1)
            current_coins = redis_cache.hget('users:{}:coins'.format(request.user.id), request.user.id)
            return views.Response({'status': True, "message": "you get a reward of 1 Digitvl Coin",
                                   "total_views": total_views, 'current_coins': current_coins}, status=status.HTTP_200_OK)

        except TypeError:
            return views.Response({'status': False, "message": "something wrong or may be you don't have any coin",
                                   'result': {}}, status=status.HTTP_200_OK)
