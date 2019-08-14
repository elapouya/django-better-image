# 2019-08-14 : Created by Eric Lapouyade

from django.db import models
from .formfields import BetterImageFormField


class BetterImageField(models.ImageField):
    def __init__(self, verbose_name=None, name=None, **kwargs):
        formfield_params_keys = BetterImageFormField.get_params_keys()
        self.formfield_params = { k:kwargs.pop(k)
                                  for k in formfield_params_keys
                                  if k in kwargs }
        super().__init__(verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        params = { **self.formfield_params, **kwargs }
        return super().formfield(**{
            'form_class': BetterImageFormField,
            **params,
        })

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.update(self.formfield_params)
        return name, path, args, kwargs

class BetterImageOriginalField(models.ImageField):
    def formfield(self, **kwargs):
        return None