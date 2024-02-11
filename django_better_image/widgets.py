# 2019-08-14 : Created by Eric Lapouyade

from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import json
import base64
import hashlib


class BetterImageWidget(forms.ClearableFileInput):
    template_name = 'django_better_image/image_input_widget.html'
    dz_message = _('drag & drop<br>or click here to<br>upload an image')
    field_ref_errmsg = _('Please add "BetterImageFormMixin" in your modelForm '
                         '(see documentation).')
    buttons_placement = 'left'
    buttons_no_label = False
    buttons_no_icon = False
    edit_button_label = _('Edit')
    edit_button_icon = 'icon-pencil'
    edit_button_class = 'btn btn-primary btn-sm'
    edit_button_display = True
    clear_button_label = _('Clear')
    clear_button_icon = 'icon-trash'
    clear_button_class = 'btn btn-primary btn-sm'
    clear_confirm_message = _('Do you want to clear the field {field_label} ?')
    clear_button_display = True
    upload_button_label = _('Choose an image...')
    upload_button_icon = 'icon-upload'
    upload_button_class = 'btn btn-primary'
    fullsize_button_label = _('Full size')
    fullsize_button_icon = 'icon-resize-full-alt'
    fullsize_button_class = 'btn btn-primary btn-sm'
    fullsize_button_display = True
    image_saved_message = _('The image has been saved on the server')
    image_cleared_message = _('The image has been cleared on the server')
    image_processing_message = _('The image is being processed...<br>'
                                 '<span class="icon-spin4 animate-spin"></span>')
    remember_to_save_message = _('Remember to save the form')
    form_thumb_max_size = (150, 150)
    thumb_name = None
    thumb_aspect_ratio = None
    crop_on_upload = False
    crop_file_format = 'JPEG'
    crop_file_quality = 95
    crop_auto_select = 80
    use_dropzone = True
    dropzone_size = None
    dropzone_thumb_size = None
    keep_original_in = None


    @classmethod
    def get_params_keys(cls):
        params_keys = [
            'dz_message', 'field_ref_errmsg', 'edit_button_label',
            'edit_button_icon', 'edit_button_class', 'edit_button_display',
            'clear_button_label', 'clear_button_icon', 'clear_button_class',
            'clear_button_display', 'upload_button_label',
            'upload_button_icon', 'upload_button_class',
            'fullsize_button_label',
            'fullsize_button_icon', 'fullsize_button_class',
            'fullsize_button_display', 'image_saved_message',
            'image_cleared_message', 'image_processing_message',
            'remember_to_save_message',
            'form_thumb_max_size', 'thumb_name', 'thumb_aspect_ratio',
            'crop_on_upload', 'crop_file_format', 'crop_file_quality',
            'dropzone_size', 'dropzone_thumb_size', 'buttons_placement',
            'buttons_no_label', 'buttons_no_icon','keep_original_in',
            'use_dropzone', 'crop_auto_select',
        ]
        return params_keys

    def __init__(self, attrs=None, **kwargs):
        params_keys = self.get_params_keys()
        for k,v in kwargs:
            if v is not None and k in params_keys:
                setattr(self,k,v)
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Put in context all widget parameters
        context['widget'].update({ a:getattr(self,a,None)
                                   for a in self.get_params_keys() })
        if self.buttons_no_icon:
            context['widget'].update(
                clear_button_icon='',
                edit_button_icon='',
                fullsize_button_icon='')
        instance = getattr(value, 'instance', None)
        dropzone_size = self.dropzone_size or self.form_thumb_max_size
        dropzone_thumb_size = self.dropzone_thumb_size or self.form_thumb_max_size
        # only when an instance is already existing (object update, not create)
        form = getattr(self, 'bi_form', None)
        formfield = getattr(self, 'bi_formfield', None)
        if not form or not formfield:
            raise NotImplementedError(
                'Forms using django-better-image app '
                'must use BetterImageFormMixin as first parent class' )
        field_ref = ( f'{form.__module__}.{form.__class__.__name__}'
                      f'.{formfield.bi_fieldname}' )
        field_label = formfield.label.lower()
        if instance:
            data = {
                'field_ref' : field_ref,
                'app_label' : instance._meta.app_label,
                'model_name' : instance._meta.model_name,
                'pk' : instance.pk,
            }
            context['widget']['instance'] = instance
            context['widget']['field_ref'] = field_ref
            context['widget']['field_label'] = field_label
            # if a thumb field is specified : use it
            thumb_name = self.thumb_name or name
            # May be thumb_name is specified but do not exist :
            # falling back to actual image
            context['widget']['thumb'] = ( getattr(instance, thumb_name, None) or
                                           getattr(instance, name, None) )
            context['widget']['crop_image'] = value
            if self.keep_original_in:
                original_image = getattr(instance, self.keep_original_in, None)
                context['widget']['original'] = original_image
                if original_image:
                    context['widget']['crop_image'] = original_image
            serialized_data_bytes = base64.b64encode(json.dumps(data).encode('utf-8'))
            data_chk = hashlib.md5(
                serialized_data_bytes + settings.SECRET_KEY.encode('utf-8')
            ).hexdigest()
            context['widget']['serialized_data'] = serialized_data_bytes.decode()
            context['widget']['serialized_data_chk'] = data_chk
        context['widget']['dropzone_size'] = dropzone_size
        context['widget']['dropzone_thumb_size'] = dropzone_thumb_size
        context['widget']['edit_url'] = reverse('better_image_edit')
        context['widget']['clear_url'] = reverse('better_image_clear')
        context['widget']['upload_url'] = reverse('better_image_upload') # dropzone url
        context['widget']['clear_confirm_message'] = \
            self.clear_confirm_message.format(field_label=field_label)
        return context
