# Generated by Django 2.2 on 2021-09-30 11:43

from django.db import migrations

def forward_func(apps, schema_editor):
    OrganizationUserInvite = apps.get_model("brand", "OrganizationUserInvite")
    LicenseUserInvite = apps.get_model("brand", "LicenseUserInvite")
    for obj in OrganizationUserInvite.objects.all():
        for license in obj.licenses.all():
            qs = LicenseUserInvite.objects.filter(
                email=obj.email,
                license=license,
                is_invite_accepted=obj.is_invite_accepted,
                status=obj.status,
                created_by_id=obj.created_by_id,
            )
            if qs.exists():
                lic_inv_obj = qs.first()
                # if not lic_inv_obj.roles.filter(id=obj.role_id):
                lic_inv_obj.roles.add(obj.role)
                lic_inv_obj.save()

            else:
                lic_inv_obj = LicenseUserInvite.objects.create(
                    full_name=obj.full_name,
                    email=obj.email,
                    phone=obj.phone,
                    license=license,
                    is_invite_accepted=obj.is_invite_accepted,
                    status=obj.status,
                    created_by_id=obj.created_by_id,
                )
                lic_inv_obj.roles.add(obj.role)
                lic_inv_obj.save()


def reverse_func(apps, schema_editor):
    LicenseUserInvite = apps.get_model("brand", "LicenseUserInvite")
    OrganizationUserInvite = apps.get_model("brand", "OrganizationUserInvite")
    for obj in LicenseUserInvite.objects.all():
        for role in obj.roles.all():
            qs = OrganizationUserInvite.objects.filter(
                email=obj.email,
                role=role,
                is_invite_accepted=obj.is_invite_accepted,
                status=obj.status,
                created_by_id=obj.created_by_id,
            )
            if qs.exists():
                org_inv_obj = qs.first()
                org_inv_obj.licenses.add(obj.license)
                org_inv_obj.save()

            else:
                org_inv_obj = LicenseUserInvite.objects.create(
                    full_name=obj.full_name,
                    email=obj.email,
                    phone=obj.phone,
                    role=role,
                    is_invite_accepted=obj.is_invite_accepted,
                    status=obj.status,
                    created_by_id=obj.created_by_id,
                )
                org_inv_obj.roles.add(obj.role)
                org_inv_obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0104_licenseuserinvite'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_code=reverse_func),
    ]
