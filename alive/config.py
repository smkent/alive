import os

import yaml

DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.alive')
CONFIG_DIR_MODE = 0o0700


class Config(object):
    def __init__(self, config_dir):
        self._config_dir = config_dir
        self._ensure_config_dir()
        self._config = None
        self._load()

    def _ensure_config_dir(self):
        if not os.path.isdir(self._config_dir):
            try:
                print('Creating directory {}'.format(self._config_dir))
                os.makedirs(self._config_dir, CONFIG_DIR_MODE)
            except Exception as e:
                raise Exception('Error creating configuration directory {}: {}'
                                .format(self._config_dir, str(e)))
        config_dir_stat = os.stat(self._config_dir)
        if config_dir_stat.st_mode & CONFIG_DIR_MODE != CONFIG_DIR_MODE:
            print('Correcting mode on {}'.format(self._config_dir))
            os.chmod(self._config_dir, CONFIG_DIR_MODE)

    def _load(self):
        file_name = os.path.join(self._config_dir, 'config.yaml')
        with open(file_name, 'r') as config_f:
            loaded = yaml.load(config_f)
            self._config = loaded

    def __getattr__(self, name, default_value=None):
        if not self._config:
            return default_value
        if name in self._config:
            return self._config.get(name, default_value)
        if default_value:
            return default_value
        raise ValueError('{} not in {}'.format(name, self))

    def __contains__(self, name):
        return name in self._config
