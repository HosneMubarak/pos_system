from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *


# ... Your other registrations and admin classes ...

class CustomUserAdmin(ImportExportModelAdmin):
    model = CustomUser


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        fields = '__all__'


admin.site.register(CustomUser, CustomUserAdmin)
