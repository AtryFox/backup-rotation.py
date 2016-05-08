#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime


def main():
    if len(sys.argv) < 2:
        print("No configfile stated, using default (./config.json)")
        config_path = "config.json"
    else:
        if not os.path.isfile(sys.argv[1]):
            print("Stated configfile not found, aborting...")
            exit()
        config_path = sys.argv[1]

    config_data = Config(config_path)

    now = datetime.now()


class Config:
    def __init__(self, config_path):
        print(config_path)
        try:
            with open(config_path) as config_file:
                data = json.load(config_file)

                if "default" in data:
                    if "create_backup_day_of_week" in data["default"]:
                        self.create_backup_day_of_week = data["default"]["create_backup_day_of_week"]

                    if "create_backup_day_of_month" in data["default"]:
                        self.create_backup_day_of_month = data["default"]["create_backup_day_of_month"]

                    if "create_backup_day_of_year" in data["default"]:
                        self.create_backup_day_of_year = data["default"]["create_backup_day_of_year"]

                    if "daily_backups" in data["default"]:
                        self.daily_backups = data["default"]["daily_backups"]

                    if "weekly_backups" in data["default"]:
                        self.weekly_backups = data["default"]["weekly_backups"]

                    if "monthly_backups" in data["default"]:
                        self.monthly_backups = data["default"]["monthly_backups"]

                    if "yearly_backups" in data["default"]:
                        self.yearly_backups = data["default"]["yearly_backups"]

                    if "backup_items" in data:
                        for backups in data["backup_items"]:
                            if os.path.isdir(backups["source"]) & os.path.isdir(backups["source"]):
                                self.backup_items.append(BackupItem(self, backups))

                    for test in self.backup_items:
                        print("%s: %s" % (test.source, test.daily_backups))
        except FileNotFoundError:
            print("Could not find config file!")
            exit()

    create_backup_day_of_week = 0
    create_backup_day_of_month = 0
    create_backup_day_of_year = 0

    daily_backups = 7
    weekly_backups = 4
    monthly_backups = 6
    yearly_backups = 4

    compression = "bz2"

    backup_items = []


class BackupItem:
    _config = Config

    def __init__(self, config_data, data):
        _config = config_data

        self.source = data["source"]
        self.destination = data["destination"]

        if "create_backup_day_of_week" in data:
            self.create_backup_day_of_week = data["create_backup_day_of_week"]
        else:
            self.create_backup_day_of_week = _config.create_backup_day_of_week

        if "create_backup_day_of_month" in data:
            self.create_backup_day_of_month = data["create_backup_day_of_month"]
        else:
            self.create_backup_day_of_month = _config.create_backup_day_of_month

        if "create_backup_day_of_year" in data:
            self.create_backup_day_of_year = data["create_backup_day_of_year"]
        else:
            self.create_backup_day_of_year = _config.create_backup_day_of_year

        if "daily_backups" in data:
            self.daily_backups = data["daily_backups"]
        else:
            self.daily_backups = _config.daily_backups

        if "weekly_backups" in data:
            self.weekly_backups = data["weekly_backups"]
        else:
            self.weekly_backups = _config.weekly_backups

        if "monthly_backups" in data:
            self.monthly_backups = data["monthly_backups"]
        else:
            self.monthly_backups = _config.monthly_backups

        if "yearly_backups" in data:
            self.yearly_backups = data["yearly_backups"]
        else:
            self.yearly_backups = _config.yearly_backups

        if "compression" in data:
            self.compression = data["compression"]
        else:
            self.compression = _config.compression

    source = None
    destination = None

    create_backup_day_of_week = None
    create_backup_day_of_month = None
    create_backup_day_of_year = None

    daily_backups = None
    weekly_backups = None
    monthly_backups = None
    yearly_backups = None

    compression = None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        pass
