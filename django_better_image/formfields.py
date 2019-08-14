# 2019-08-14 : Created by Eric Lapouyade

import json
from io import BytesIO
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps
from django.http import QueryDict

from .widgets import BetterImageWidget


class BetterImageFormField(forms.ImageField):
    widget = BetterImageWidget

    def __init__(self, *args, **kwargs):
        widget_params_keys = BetterImageWidget.get_params_keys()
        widget_params = {}
        for k in widget_params_keys:
            if k in kwargs:
                widget_params[k]=kwargs.pop(k)
        super().__init__(**kwargs)
        self.widget.__dict__.update(widget_params)

    @classmethod
    def get_params_keys(cls):
        return BetterImageWidget.get_params_keys()

    @classmethod
    def crop_image(cls, pil_image, x, y, width, height, rotate,
                   scaleX, scaleY, imgWidth, imgHeight, format, quality):

        db_width, db_height = pil_image.size  # image size from original image stored in database
        ratio_w = db_width / imgWidth
        ratio_h = db_height / imgHeight

        crop_x1 = int(x * ratio_w)
        crop_y1 = int(y * ratio_h)
        crop_x2 = int((x + width) * ratio_w)
        crop_y2 = int((y + height) * ratio_h)
        if format != 'PNG':
            if pil_image.mode == 'RGBA':
                background = Image.new('RGBA', pil_image.size, (255, 255, 255))
                pil_image = Image.alpha_composite(background, pil_image)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
        if scaleX < 0:
            pil_image = ImageOps.mirror(pil_image)
        if scaleY < 0:
            pil_image = ImageOps.flip(pil_image)
        if rotate:
            pil_image = pil_image.rotate(-rotate, expand=True)
        if width:
            pil_image = pil_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        in_memory_image = BytesIO()
        pil_image.save(in_memory_image, format, quality=quality)

        return in_memory_image

    def crop_from_json_data(self, in_file):
        better_image_key = f'{self.bi_fieldname}__data'
        data_json = self.bi_form.data.get(better_image_key)
        if data_json and in_file:
            data = json.loads(data_json)
            if data:
                pil_image = Image.open(in_file)
                x = data.get('x')
                y = data.get('y')
                width = data.get('width')
                height = data.get('height')
                rotate = data.get('rotate')
                scaleX = data.get('scaleX')
                scaleY = data.get('scaleY')
                imgWidth = data.get('imgWidth')
                imgHeight = data.get('imgHeight')
                format = self.widget.crop_file_format
                quality = self.widget.crop_file_quality

                in_memory_image = self.crop_image(
                    pil_image, x, y, width, height, rotate, scaleX,
                    scaleY,
                    imgWidth, imgHeight, format, quality)

                return InMemoryUploadedFile(
                    in_memory_image, None, in_file.name,
                    f'image/{format}'.lower(), in_memory_image.tell(), None )
        return None

    def to_python(self, data):
        """
        Check that the file-upload field data contains a valid image (GIF, JPG,
        PNG, etc. -- whatever Pillow supports).
        """
        f = super().to_python(data)
        if f is None:
            return None

        if isinstance(self.bi_form.data, QueryDict):  # not a model instance
            # the cropping is not done here for fields that are backuped
            # see BetterImageFormMixin.save() for backuped case
            if not self.widget.keep_original_in:
                cropped = self.crop_from_json_data(f)
                return cropped or f
        return f