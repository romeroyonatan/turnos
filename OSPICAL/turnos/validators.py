import re
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)

class PasswordValidator(object):
    min_length = 6
    message = _('Enter a valid value.')
    code = 'invalid'

    def __init__(self, min_length=None, message=None, code=None, 
                 lower=False, upper=False, 
                 number=False, special_characters=False):
        self.regexs = list()
        if min_length is not None:
            self.min_length = min_length
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if lower:
            self.regexs.append(re.compile('[a-z]'))
        if upper:
            self.regexs.append(re.compile('[A-Z]'))
        if number:
            self.regexs.append(re.compile('\d'))
        if special_characters:
            self.regexs.append(re.compile('[=!\-@._*$]'))

    def __call__(self, value):
        """
        Validates that the input matches the regular expression.
        """
        valid = True
        for regex in self.regexs:
            search = regex.search(value)
            valid = valid and ( search != None)
        if not valid or len(value) < self.min_length:
            raise ValidationError(self.message, code=self.code)