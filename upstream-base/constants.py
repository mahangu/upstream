import os

if os.environ.get('UPSTREAM_CONF_DIR'):
	conf_dir = os.environ.get('UPSTREAM_CONF_DIR')
else:
	# FIXME: change before release:  conf_dir = '/etc/upstream'
	conf_dir = '../conf'

if os.environ.get('UPSTREAM_DATA_DIR'):
	data_dir = os.environ.get('UPSTREAM_DATA_DIR')
else:
	# FIXME: change before release:  data_dir = '/usr/share/upstream'
	data_dir = '../extras'

if os.environ.get('UPSTREAM_LOCALE_DIR'):
	locale_dir = os.environ.get('UPSTREAM_LOCALE_DIR')
else:
	# FIXME: you get the idea...
	locale_dir = '../po' # what is default?

if os.environ.get('UPSTREAM_GLADE_DIR'):
	glade_dir = os.environ.get('UPSTREAM_GLADE_DIR')
else:
	glade_dir = data_dir # is this sensible?
	
if os.environ.get('UPSTREAM_IMAGE_DIR'):
	image_dir = os.environ.get('UPSTREAM_IMAGE_DIR')
else:
	image_dir = data_dir # is this sensible?

locale_app = 'upstream'
