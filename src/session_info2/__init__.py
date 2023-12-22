from importlib.metadata import packages_distributions


def main():
    pkg2dist = packages_distributions()
    print(pkg2dist)
