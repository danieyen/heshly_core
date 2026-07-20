from datetime import datetime, UTC


def print_test_header(name: str):

    print("\n================================")
    print(name)
    print("================================\n")



def print_success(message: str):

    print(f"✅ {message}")



def print_complete(name: str):

    print(
        f"\n🎉 {name} PASSED\n"
    )



def timestamp():

    return datetime.now(UTC)
