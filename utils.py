import os


def build_absolute_path(path):
    return os.path.join(
        os.getcwd(),
        path,
    )
