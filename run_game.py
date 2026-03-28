import sys

MIN_VER = (3, 12)

if sys.version_info[:2] < MIN_VER:
    sys.exit("This game requires Python {}.{}.".format(*MIN_VER))

from main import main  # noqa: E402

main()
