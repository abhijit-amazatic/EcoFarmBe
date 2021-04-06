from django.shortcuts import reverse

def reverse_admin_change_path(obj):
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=(obj.id,),
    )
