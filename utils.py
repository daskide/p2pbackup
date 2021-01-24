import threading


def get_complement_values_from_list(list1, list2):
    return list(set(list1) - set(list2))


def start_new_thread(thread_function, args, daemon):
    x = threading.Thread(target=thread_function, args=args, daemon=daemon)
    x.start()
    return x