import os
import sys

from app.hello import add, say_hello

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))
# print(sys.path)



def test_say_hello():
    assert say_hello("ChatGPT") == "Hello, ChatGPT!"

def test_add():
    assert add(2, 3) == 5

