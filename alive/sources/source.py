from __future__ import print_function

import abc
import os


class Source(object):
    def __init__(self, config):
        self.config = config
        self._timestamp_file = os.path.join(self.config._config_dir,
                                            '{}.timestamp'.format(self.name))

    @abc.abstractmethod
    def check(self):
        pass

    @property
    def _last_checked(self):
        if not os.path.isfile(self._timestamp_file):
            return 0
        with open(self._timestamp_file, 'r') as f:
            first_line = f.readline()
            try:
                return int(first_line.strip())
            except ValueError:
                print('Error: Invalid timestamp "{}" in file {}'
                      .format(first_line, self._timestamp_file))
                return 0

    @_last_checked.setter
    def _last_checked(self, new_value):
        with open(self._timestamp_file, 'w') as f:
            print(new_value, file=f)
