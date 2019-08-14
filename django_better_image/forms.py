# 2019-08-14 : Created by Eric Lapouyade

from django import forms
from .formfields import BetterImageFormField
from .widgets import BetterImageWidget


class BetterImageFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name,f in self.fields.items():
            widget = f.widget
            if isinstance(widget, BetterImageWidget):
                f.bi_fieldname = name
                f.bi_form = self
                widget.bi_formfield = f
                widget.bi_form = self

    def keep_original_image_field(self, fieldname, formfield):
        if isinstance(formfield,BetterImageFormField):
            ofieldname = formfield.widget.keep_original_in
            if ofieldname:
                image_field = getattr(self.instance, fieldname, None)
                backup_field = getattr(self.instance, ofieldname, None)
                # if backup_field exists in model
                if backup_field is not None:
                    # if backup_field exists anf has no Image specified
                    if backup_field:
                        if not image_field:
                            setattr(self.instance, ofieldname,None)
                    else:
                        if image_field:
                            setattr(self.instance, ofieldname,image_field)

    def keep_original_image_fields(self):
        if hasattr(self,'instance'):
            for fieldname,formfield in self.fields.items():
                self.keep_original_image_field(fieldname, formfield)

    def crop_original_image_field(self, fieldname, formfield):
        if isinstance(formfield,BetterImageFormField):
            ofieldname = formfield.widget.keep_original_in
            if ofieldname:
                image_field = getattr(self.instance, ofieldname, None)
                cropped = formfield.crop_from_json_data(image_field)
                if cropped:
                    setattr(self.instance, fieldname, cropped)
                    self.instance._bi_crop_original_done = True

    def crop_original_image_fields(self):
        if hasattr(self,'instance'):
            for fieldname,formfield in self.fields.items():
                self.crop_original_image_field(fieldname, formfield)
            if hasattr(self.instance,'_bi_crop_original_done'):
                self.instance.save()

    def save(self, commit=True):
        self.keep_original_image_fields()
        instance = super().save(commit)
        self.crop_original_image_fields()
        return instance


class BetterImageModelForm(BetterImageFormMixin, forms.ModelForm):
    pass


class BetterImageForm(BetterImageFormMixin, forms.Form):
    pass
