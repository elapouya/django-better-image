# 2019-08-14 : Created by Eric Lapouyade

from django.conf.urls import url

from .views import ( BetterImageClearView,
                     BetterImageEditView,
                     BetterImageUploadView )

urlpatterns = [
    url(r'^upload/$',
        BetterImageUploadView.as_view(),
        name='better_image_upload'),
    url(r'^clear/$',
        BetterImageClearView.as_view(),
        name='better_image_clear'),
    url(r'^edit/$',
        BetterImageEditView.as_view(),
        name='better_image_edit'),
]