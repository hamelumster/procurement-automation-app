from django.contrib import admin

from users.models import UserProfile, SupplierProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_supplier', 'created_at', 'updated_at')
    list_select_related = ('user',)

    def is_supplier(self, obj):
        return hasattr(obj.user, 'supplier_profile')

    is_supplier.boolean = True

@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('user', )
