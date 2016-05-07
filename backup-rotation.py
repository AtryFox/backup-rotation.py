#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


def main():
    if len(sys.argv) < 2:
        print("No configfile stated, using default (./config.json)")
        config = "config.json"
    else:
        config = sys.argv[1]

    if not os.path.isfile(sys.argv[1]):
        print("Stated configfile not found, aborting...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        pass
