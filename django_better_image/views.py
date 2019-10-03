# 2019-08-14 : Created by Eric Lapouyade

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.generic import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.apps import apps
from django.conf import settings
from .formfields import BetterImageFormField
import base64
import json
import hashlib
from PIL import Image
from django.core.files import File

class BetterImageViewException(Exception):
    pass

class BetterImageBaseView(View):
    def get(self, request, *args, **kwargs):
        try:
            error = self.get_target_info()
            if error:
                return error
            data = self.get_data()
            return JsonResponse(data)
        except ValidationError as e:
            message = str(e.message) or ', '.join(e.messages)
            return HttpResponseBadRequest(message.encode('utf-8'))
        except Exception as e:
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
            return HttpResponseBadRequest(str(e).encode('utf-8'))

    post = get

    def get_target_info(self):
        upload_params = self.request.POST.get('upload_params')
        upload_params_chk = self.request.POST.get('upload_params_chk')
        if not upload_params or not upload_params_chk:
            raise BetterImageViewException(_('Upload params missing'))
        params_chk = hashlib.md5(
            upload_params.encode('utf-8') + settings.SECRET_KEY.encode('utf-8')
        ).hexdigest()
        if upload_params_chk != params_chk:
            raise BetterImageViewException(_('Upload params corrupted'))
        upload_params = json.loads(base64.b64decode(upload_params.encode()).decode('utf-8'))
        field_ref = upload_params.get('field_ref')
        app_label = upload_params.get('app_label')
        model_name = upload_params.get('model_name')
        pk = upload_params.get('pk')

        if not all((app_label, model_name, field_ref, pk)):
            raise BetterImageViewException(
                _('Some parameters are missing while uploading image'))
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except KeyError:
            raise BetterImageViewException(
                _('Image destination app/model incorrect'))
        try:
            self.instance = model.objects.get(pk=pk)
        except model.DoesNotExist:
            raise BetterImageViewException(
                _('{model_name} #{pk} does not exist')
                .format(model_name=model_name,pk=pk) )
        try:
            self.form_class_name, self.fieldname = field_ref.rsplit('.',1)
        except ValueError:
            raise BetterImageViewException(
                _('Bad field reference : %s') % field_ref )
        if not hasattr(self.instance, self.fieldname):
            raise BetterImageViewException(
                _('{model_name} has no field {field_name}')
                .format(model_name=model_name,field_name=self.fieldname) )
        form_class = import_string(self.form_class_name)
        self.form = form_class(instance=self.instance, files=self.request.FILES)
        self.formfield = self.form.fields.get(self.fieldname)
        if not self.formfield:
            raise BetterImageViewException(
                _('{field_name} does not exist in {form_name}')
                .format(field_name=self.fieldname,
                        form_name=self.form_class_name) )
        if not hasattr(self.form, 'keep_original_image_field'):
            raise BetterImageViewException(
                _('Please use the BetterImageFormMixin in %s') %
                self.form.__class__.__name__
            )

    def get_widget_output(self):
        value = getattr(self.instance, self.fieldname, None)
        html = self.formfield.widget.render(self.fieldname, value)
        return { 'status':'success', 'replace_html':html }


class BetterImageUploadView(BetterImageBaseView):
    def get_data(self):
        if self.fieldname not in self.request.FILES:
            raise BetterImageViewException(
                _('No "{field_name}" in posted files')
                .format(field_name=self.fieldname) )
        value = self.request.FILES.get(self.fieldname)
        self.formfield.clean(value, value)
        setattr(self.instance, self.fieldname, value)
        self.form.keep_original_image_field(self.fieldname, self.formfield)
        self.instance.save()
        return self.get_widget_output()


class BetterImageClearView(BetterImageBaseView):
    def get_data(self):
        setattr(self.instance, self.fieldname, None)
        self.form.keep_original_image_field(self.fieldname, self.formfield)
        self.instance.save()
        return self.get_widget_output()


class BetterImageEditView(BetterImageBaseView):
    def get_data(self):
        dest_image = getattr(self.instance, self.fieldname, None)
        image_to_crop = None
        ofieldname = self.formfield.widget.keep_original_in
        if ofieldname:
            image_to_crop = getattr(self.instance, ofieldname, None)
        if not image_to_crop:
            image_to_crop = dest_image
        if not image_to_crop:
            raise BetterImageViewException(
                _('{field_name} has no image set.')
                .format(field_name=self.fieldname) )

        pil_image = Image.open(image_to_crop)

        x = float(self.request.POST.get('x'))
        y = float(self.request.POST.get('y'))
        width = float(self.request.POST.get('width'))
        height = float(self.request.POST.get('height'))
        rotate = float(self.request.POST.get('rotate'))
        scaleX = float(self.request.POST.get('scaleX'))
        scaleY = float(self.request.POST.get('scaleY'))
        imgWidth = float(self.request.POST.get('imgWidth'))   # image size used in cropperjs
        imgHeight = float(self.request.POST.get('imgHeight')) # (may be smaller than original on mobile devices (iOS mainly)
        format = self.formfield.widget.crop_file_format
        quality = self.formfield.widget.crop_file_quality

        in_memory_image = BetterImageFormField.crop_image(
            pil_image, x, y, width, height, rotate, scaleX, scaleY,
            imgWidth, imgHeight, format, quality)

        path = slugify('{instance}-{field}'.format(
            instance=str(self.instance).replace('object',''),
            field=self.fieldname
        )) + f'.{format.lower()}'
        dest_image.save(path, File(in_memory_image), save=False)
        self.instance.save()
        return self.get_widget_output()
