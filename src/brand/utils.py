import random

def get_unique_org_name(organization_model):
    name = f'My Organization {int(random.random()*100000):05}'
    if not organization_model.objects.filter(name=name).exists():
        return name
    return get_unique_org_name(organization_model)
