from . import settings as base_settings


for setting_name in dir(base_settings):
	if setting_name.isupper():
		globals()[setting_name] = getattr(base_settings, setting_name)


DEBUG = False