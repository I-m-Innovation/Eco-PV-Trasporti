from copy import copy


def patch_django_context_copy():
    try:
        from django.template import Context
        from django.template.context import BaseContext
    except Exception:
        return

    try:
        copy(Context({}))
        return
    except AttributeError as exc:
        if "dicts" not in str(exc):
            raise

    def copy_base_context(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = copy_base_context
