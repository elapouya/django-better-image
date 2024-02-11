# 2019-08-14 : Created by Eric Lapouyade

from django.urls import re_path

from .views import ( BetterImageClearView,
                     BetterImageEditView,
                     BetterImageUploadView )

urlpatterns = [
    re_path(r'^upload/$',
        BetterImageUploadView.as_view(),
        name='better_image_upload'),
    re_path(r'^clear/$',
        BetterImageClearView.as_view(),
        name='better_image_clear'),
    re_path(r'^edit/$',
        BetterImageEditView.as_view(),
        name='better_image_edit'),
]