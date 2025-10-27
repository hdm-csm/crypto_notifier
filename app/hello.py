def say_hello(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    print("new")
    return a + b


if __name__ == "__main__":
    print(say_hello("World"))
    print("2 + 3 =", add(2, 3))
