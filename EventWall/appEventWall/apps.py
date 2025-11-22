from django.apps import AppConfig


class AppeventwallConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appEventWall'

    def ready(self):
      import appEventWall.signals
