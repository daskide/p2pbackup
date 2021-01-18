import random
import string

key_length = 64

def gen_key(length = key_length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return  ("a" * key_length)#result_str
