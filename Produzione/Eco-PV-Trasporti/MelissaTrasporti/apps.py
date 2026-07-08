from django.apps import AppConfig


class MelissatrasportiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MelissaTrasporti'
    verbose_name = 'Logistica Eco-PV'

    def ready(self):
        from .compat import patch_django_context_copy

        patch_django_context_copy()
