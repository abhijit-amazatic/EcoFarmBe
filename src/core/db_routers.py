# import core.settings import DRF_API_LOGGER_DEFAULT_DATABASE


class LoggerRouter:
    # logger_db = DRF_API_LOGGER_DEFAULT_DATABASE
    logger_db = 'logger'
    logger_app_labels = {'drf_api_logger'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.logger_app_labels:
            return self.logger_db
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.logger_app_labels:
            return self.logger_db
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.logger_app_labels or
            obj2._meta.app_label in self.logger_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.logger_app_labels:
            return db == self.logger_db
        return None


# class defaultRouter:
#     # logger_db = DRF_API_LOGGER_DEFAULT_DATABASEWW
#     default_db_name = 'default'

#     def db_for_read(self, model, **hints):
#         return self.default_db_name

#     def db_for_write(self, model, **hints):
#         return self.default_db_name

#     def allow_relation(self, obj1, obj2, **hints):
#         if obj1._state.db == self.default_db_name and obj2._state.db == self.default_db_name:
#             return True
#         return None

#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         return True

