import os

if os.environ.get('UPSTREAM_CONF_DIR'):
	conf_dir = os.environ.get('UPSTREAM_CONF_DIR')
else:
	conf_dir = '/etc/upstream/conf'

if os.environ.get('UPSTREAM_DATA_DIR'):
	data_dir = os.environ.get('UPSTREAM_DATA_DIR')
else:
	data_dir = '/usr/share/upstream'

if os.environ.get('UPSTREAM_LOCALE_DIR'):
	locale_dir = os.environ.get('UPSTREAM_LOCALE_DIR')
else:
	locale_dir = '../po' # what is default?

if os.environ.get('UPSTREAM_GLADE_DIR'):
	glade_dir = os.environ.get('UPSTREAM_GLADE_DIR')
else:
	glade_dir = data_dir # is this sensible?

locale_app = 'upstream'
