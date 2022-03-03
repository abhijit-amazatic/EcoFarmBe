"""
All periodic tasks related to brand.
"""
import traceback
from datetime import timedelta
from core.mailer import mail, mail_send
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from celery.task import periodic_task
from django.utils import timezone
from slacker import Slacker

from integration.apps.twilio import (
    send_sms,
)
from core.celery import app
from core.utility import (
    notify_admins_on_profile_user_registration,
)
from user.models import (
    User,
)
from ..models import (
    License,
    ProfileContact,
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    OnboardingDataFetch,
    LicenseUserInvite,
)

slack = Slacker(settings.SLACK_TOKEN)


@app.task(queue="general")
def invite_license_user_task(invite_obj_id):
    """
    Async send organization user invitation.
    """
    try:
        invite_obj = LicenseUserInvite.objects.get(id=invite_obj_id)
    except LicenseUserInvite.DoesNotExist:
        pass
    else:
        context = {
            "full_name": invite_obj.full_name,
            "email": invite_obj.email,
            "organization": invite_obj.license.organization.name,
            "roles": [x.name for x in invite_obj.roles.all()],
            "license": f"{invite_obj.license.license_number} | {invite_obj.license.legal_business_name}",
            "phone": invite_obj.phone.as_e164,
            "tll_in_hours": int(invite_obj.__class__.TLL/3600),
            # 'token': invite_obj.get_invite_token(),
            "link": "{}/verify-user-invitation?code={}".format(
                settings.FRONTEND_DOMAIN_NAME.rstrip("/"), invite_obj.get_invite_token()
            ),
        }
        # context['link'] = '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME.rstrip('/'), context['token'])

        try:
            mail_send(
                "email/user-invitation-mail.html",
                context,
                "Thrive Society Invitation.",
                context.get("email"),
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)
        else:
            msg = 'You have been invited to join license profile {license} under organization "{organization}".\nPlease check your email {email}'.format(
                **context
            )
            send_sms(context["phone"], msg)


@app.task(queue="general")
def invite_profile_contacts_task(profile_contact_id):
    """
    ->send invites to profile contacts
    """
    # role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
    # updated_role_map  =  {"Cultivation Manager":"farm_manager","Sales Manager":"sales_or_inventory","Logistics Manager":"logistics","Billing / Accounting":"billing","Owner":"owner"}

    pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id).first()
    if pro_contact_obj:
        license_obj = pro_contact_obj.license
        employee_data = pro_contact_obj.profile_contact_details.get("employees")
        extracted_employee = {}
        for employee in [i for i in employee_data if i.get("employee_email")]:
            if employee["employee_email"] in extracted_employee:
                roles = (
                    extracted_employee[employee["employee_email"]].get("roles") or []
                )
                new_roles = employee.get("roles") or []
                if new_roles:
                    extracted_employee[employee["employee_email"]]["roles"] = list(
                        set(roles).add(*new_roles)
                    )
            else:
                extracted_employee[employee["employee_email"]] = employee

        for employee in extracted_employee.values():
            roles = []
            for role_name in employee["roles"]:
                role, _ = OrganizationRole.objects.get_or_create(
                    organization=license_obj.organization,
                    name=role_name,
                )
                roles.append(role)
                if (
                    license_obj.organization.created_by.email
                    == employee["employee_email"]
                ):
                    user = license_obj.organization.created_by
                    organization_user, _ = OrganizationUser.objects.get_or_create(
                        organization=license_obj.organization,
                        user=user,
                    )
                    (
                        organization_user_role,
                        _,
                    ) = OrganizationUserRole.objects.get_or_create(
                        organization_user=organization_user,
                        role=role,
                    )
                    organization_user_role.licenses.add(license_obj)
                    organization_user.save()

            if (
                not license_obj.organization.created_by.email
                == employee["employee_email"]
            ):
                invite = LicenseUserInvite.objects.create(
                    full_name=employee["employee_name"],
                    email=employee["employee_email"],
                    phone=employee["phone"],
                    license=license_obj,
                    created_by_id=license_obj.organization.created_by_id,
                )
                invite.roles.set(roles)
                invite.save()
                invite_license_user_task.delay(invite.id)
