import random
from .tasks import (send_async_invitation, )

def get_unique_org_name(organization_model):
    name = f'My Organization {int(random.random()*100000):05}'
    if not organization_model.objects.filter(name=name).exists():
        return name
    return get_unique_org_name(organization_model)

def get_invitation_context(invite_obj):
    context = {
        'full_name': invite_obj.full_name,
        'email': invite_obj.email,
        'organization': invite_obj.organization.name,
        'role': invite_obj.role.name,
        'licenses': [ f"{x.license_number} | {x.legal_business_name}" for x in invite_obj.licenses.all()],
        'phone': invite_obj.phone.as_e164,
        'token': invite_obj.get_invite_token(),
        # 'link':  '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME, instance.get_invite_token()),
    }
    return context

def send_invitation(invite_obj):
    return send_async_invitation.delay(get_invitation_context(invite_obj))