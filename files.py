import os

BUFFER_SIZE = 16384 #16384


def get_absolute_file_paths(directory):
    files = []
    for dirpath,_,filenames in os.walk(os.path.abspath(directory)):
        for f in filenames:
            files.append(os.path.join(dirpath, f))
    return files


def get_save_location(file_name, directory):
    drive_tail = os.path.splitdrive(file_name)
    save_location = f"{directory}" + drive_tail[1] #drive_tail[0] +
    return save_location


def make_dirs(file):
    dir_path = os.path.dirname(os.path.realpath(file))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
