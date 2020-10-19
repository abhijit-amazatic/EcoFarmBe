import django.conf


class Settings:
    """
    This is a simple class to take the place of the global settings object. An
    instance will contain all of our settings as attributes, with default values
    if they are not specified by the configuration.
    """
    prefix = 'TWO_FACTOR_'
    defaults = {
        'PHONE_TOTP_DIGITS': 6, # The number of digits to expect in a token.
        'PHONE_TOTP_STEPS': 10,
        'LOGIN_TOKEN_VALID_FOR_SEC': 1800,
        'AUTHENTICATOR_TOTP_ISSUER': 'thrive-society.com',
    }

    def __getattr__(self, name):
        return getattr(
            django.conf.settings, 'two_factor', {}
        ).get(
            name,
            getattr(
                django.conf.settings,
                self.prefix+name,
                self.get_defaults(name)
            )
        )

    def get_defaults(self, name):
        if name in self.defaults:
            return getattr(django.conf.settings, name, self.defaults[name])
        else:
            return getattr(django.conf.settings, name)


settings = Settings()