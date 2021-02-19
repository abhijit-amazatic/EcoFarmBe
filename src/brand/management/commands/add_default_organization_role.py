import os
from django.core.management.base import BaseCommand, CommandError

from brand.utils import  add_default_organization_role
#from pylama.main import check_path, parse_options



class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     super(Command, self).add_arguments(parser)

    def handle(self, *args, **options):
        add_default_organization_role()