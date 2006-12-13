import os

		if os.environ.get('UPSTREAM_CONF_DIR'):
			conf_dir = os.environ.get('UPSTREAM_CONF_DIR')
		else:
			# FIXME: change before release:  conf_dir = '/etc/upstream'
			conf_dir = '/usr/local/etc/upstream'
		
		if os.environ.get('UPSTREAM_DATA_DIR'):
			data_dir = os.environ.get('UPSTREAM_DATA_DIR')
		else:
			# FIXME: change before release:  data_dir = '/usr/share/upstream'
			data_dir = '/usr/local/share/upstream'
		
		if os.environ.get('UPSTREAM_LOCALE_DIR'):
			locale_dir = os.environ.get('UPSTREAM_LOCALE_DIR')
		else:
			# FIXME: you get the idea...
			locale_dir = '/usr/local/share/locale' # what is default?
		
		if os.environ.get('UPSTREAM_GLADE_DIR'):
			glade_dir = os.environ.get('UPSTREAM_GLADE_DIR')
		else:
			glade_dir = '/usr/local/share/upstream' # is this sensible?
			
		if os.environ.get('UPSTREAM_IMAGE_DIR'):
			image_dir = os.environ.get('UPSTREAM_IMAGE_DIR')
		else:
			image_dir = '/usr/local/share/pixmaps' # is this sensible?
		
		locale_app = 'upstream''