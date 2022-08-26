import os
import json
import shutil
from typing import Any
from datetime import datetime, timedelta
from .var import Var


class Env:
    def __init__(
            self,
            path_to_config='env.json',
            group=None,
            milestone=None,
            mute=False,
            timeout=10
            ):
        self.config = self.__get_config(path_to_config)
        self.group = group
        self.__mute = mute
        self.__timeout = timeout
        self.__milestone = milestone
        self.__modified = False
        self.__variables = dict()

    def __getitem__(self, title):
        try:
            var = self.__variables[title]
            self.__set_verbose(var)
            self.__check_group(var)
            return var
        except KeyError:
            return None

    def __setitem__(self, title, value):
        try:
            self.__variables[title].value = value
        except KeyError:
            var = Var(title=title)
            self.__variables[var.title] = var
            self[title] = value

    def __set_verbose(self, var):
        if not var.verbose:
            var.verbose = True
            self.update()

    def __check_group(self, var):
        if self.group and self.group not in var.group and var.verbose:
            var.group.append(self.group)
            self.__modified = True
            self.update()

    def __getattr__(self, title):
        try:
            return self[title].value
        except AttributeError:
            self.__add_var(title=title, added_at=self.__milestone)
            self.__modified = True
            self.update()
            return self[title].value

    def __get_config(self, path_to_config):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            path_to_config
        )

    def __add_var(self, *args, **kwargs):
        var = Var(*args, **kwargs)
        self.__variables[var.title] = var
        if not self.__mute:
            var.log()

    def with_lock(func: Any):
        def wrapper(self, *args, **kwargs):
            start = datetime.now()
            while True:
                try:
                    os.rename(self.config, self.config+'.lock')
                    result = func(self, *args, **kwargs)
                    os.rename(self.config+'.lock', self.config)
                    return result
                except FileNotFoundError:
                    if datetime.now()-start >= timedelta(seconds=self.__timeout):
                        raise OSError(
                            "Unable to write to environment config. "
                            "Could be a deadlock."
                        )
        return wrapper

    def config_backup(func: Any):
        def wrapper(self, *args, **kwargs):
            try:
                shutil.copyfile(self.config+'.lock', self.config+'.back')
                result = func(self, *args, **kwargs)
                os.remove(self.config+'.back')
                return result
            except Exception as e:
                try:
                    shutil.copyfile(self.config+'.back', self.config)
                except FileNotFoundError:
                    pass
                try:
                    os.remove(self.config+'.lock')
                except FileNotFoundError:
                    pass
                try:
                    os.remove(self.config+'.back')
                except FileNotFoundError:
                    pass
                raise e
        return wrapper

    def __read_config(self):
        start = datetime.now()
        while True:
            try:
                with open(self.config, 'r') as f:
                    data = json.loads(f.read())
                    break
            except FileNotFoundError:
                if datetime.now()-start >= timedelta(seconds=self.__timeout):
                    raise OSError(
                        "Unable to write to environment config. "
                        "Could be a deadlock."
                    )

        for k in data:
            if k['title'] in self.__variables:
                if self.group and self.group not in k['group']:
                    k['group'].append(self.group)
                    self.__modified = True
            else:
                self.__add_var(k)

    @with_lock
    @config_backup
    def __write_config(self):
        if self.__modified:
            with open(self.config+'.lock', 'w') as f:
                f.write(self.to_json(only_verbose=True))
            self.__modified = False

    def update(self):
        self.__read_config()
        self.__write_config()
        return self

    def get(self, var, default=None):
        return self[var].get(default)

    def to_list(self, only_verbose=False):
        if only_verbose:
            env_vars = [v for v in self.__variables.values() if v.verbose]
        else:
            env_vars = [v for v in self.__variables.values()]
        return [v.to_dict() for v in env_vars]

    def to_dict(self, only_verbose=False):
        if only_verbose:
            env_vars = [v for v in self.__variables.values() if v.verbose]
        else:
            env_vars = [v for v in self.__variables.values()]
        return {v.title: v.value for v in env_vars}

    def to_json(self, only_verbose=False, indent=4):
        return json.dumps(
            self.to_list(only_verbose),
            indent=indent,
        )
