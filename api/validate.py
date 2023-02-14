from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_percent(value):
    if value < 0 or value > 100:
        raise ValidationError(
            _('%(value)s - значение должно быть в диапазоне [0, 100]'),
            params={'value': value},
        )
