# -*- coding: utf-8 -*-
""" Errors. """


class BaseError(StandardError):
    """ Base error. """
    pass

class FileNotFoundError(BaseError):
    """ Raise when the file is not found. """
    pass

class SaveImageFailed(BaseError):
    """ Raise when fail to save error. """
    pass

class CropFailed(BaseError):
    """ Raise when fail to crop image. """
    pass