import os
import json
from var import Var

class Env:
    def __init__(self, path_to_config='env.json', milestone=None):
        self.config = self.__get_config(path_to_config)
        self.milestone = milestone
        self.variables = dict()
        self.__update_config()

    def __getitem__(self, title):
        try:
            return self.variables[title]
        except KeyError:
            return None

    def __setitem__(self, title, value):
        try:
            self.variables[title].value = value
            self.__update_config()
        except KeyError:
            var = Var(title=title)
            self.variables[var.title] = var
            self[title] = value

    def __getattr__(self, title):
        try:
            return self[title].value
        except AttributeError:
            raise ValueError("Variable %s is not set" % title)

    def __get_config(self, path_to_config):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            path_to_config
        )

    def to_list(self, only_verbose=False):
        if only_verbose:
            env_vars = [v for v in self.variables.values() if v.verbose]
        else:
            env_vars = [v for v in self.variables.values()]
        return [v.to_dict() for v in env_vars]

    def to_json(self, only_verbose=False, indent=4):
        return json.dumps(
            self.to_list(only_verbose),
            indent=indent,
        )

    def __update_config(self):
        with open(self.config, 'w+') as f:
            try:
                data = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                data = []

            for item in data:
                var = Var(item)
                self.variables[var.title] = var

            for k, v in os.environ.items():
                if not k in self.variables:
                    var = Var(title=k, added_at=self.milestone)
                    self.variables[var.title] = var

            f.write(self.to_json())
