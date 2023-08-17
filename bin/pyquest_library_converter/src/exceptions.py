class UserInterventionRequired(Exception):
    pass


class ValidationError(Exception):
    pass


class UndevelopedFeatureError(NotImplementedError):
    pass


class NullDataError(ValueError):
    pass
