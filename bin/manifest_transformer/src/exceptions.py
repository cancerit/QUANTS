# -*- coding: utf-8 -*-


class ValidationError(Exception):
    pass


class UndevelopedFeatureError(NotImplementedError):
    pass


class DelimiterError(ValidationError):
    pass


class UserInterventionRequired(ValidationError):
    pass
