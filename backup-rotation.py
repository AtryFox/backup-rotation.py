#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import tarfile
from datetime import datetime


def main():
    # Load configuration
    if len(sys.argv) < 2:
        print("No configfile stated, using default (./config.json)")
        config_path = "default_config.json"
    else:
        if not os.path.isfile(sys.argv[1]):
            print("Stated configfile not found, aborting...")
            exit()
        config_path = sys.argv[1]

    config_data = Config(config_path)

    now = datetime.now()

    # Start rotation for every backup item
    for backup_item in config_data.backup_items:
        if backup_item.compression == "bz2":
            file_type = ".tar.bz2"
        else:
            file_type = ".tar.gz"

        file_prefix = now.strftime("%Y-%m-%d")

        if backup_item.daily_backups > 0:
            file_name = file_prefix + "-DAILY" + file_type
            if os.path.exists(file_name):
                print("%s already exists. Skipping..." % file_name)
            else:
                create_backup(backup_item, file_name)

        if backup_item.weekly_backups > 0:
            if now.weekday() == backup_item.create_backup_day_of_week:
                file_name = file_prefix + "-WEEKLY" + file_type
                if os.path.exists(file_name):
                    print("%s already exists. Skipping..." % file_name)
                else:
                    create_backup(backup_item, file_name)

        if backup_item.monthly_backups > 0:
            if now.day == backup_item.create_backup_day_of_month:
                file_name = file_prefix + "-MONTHLY" + file_type
                if os.path.exists(file_name):
                    print("%s already exists. Skipping..." % file_name)
                else:
                    create_backup(backup_item, file_name)

        if backup_item.yearly_backups > 0:
            if now.timetuple().tm_yday == backup_item.create_backup_day_of_year:
                file_name = file_prefix + "-YEARLY" + file_type
                if os.path.exists(file_name):
                    print("%s already exists. Skipping..." % file_name)
                else:
                    create_backup(backup_item, file_name)

        # Check for old backups
        backups = os.listdir(backup_item.destination)

        backups_daily = []
        backups_weekly = []
        backups_monthly = []
        backups_yearly = []

        for str_ in backups:
            if re.match("\d{4}-\d{2}-\d{2}-DAILY" + file_type, str_):
                backups_daily.append(str_)
                continue

            if re.match("\d{4}-\d{2}-\d{2}-WEEKLY" + file_type, str_):
                backups_weekly.append(str_)
                continue

            if re.match("\d{4}-\d{2}-\d{2}-MONTHLY" + file_type, str_):
                backups_monthly.append(str_)
                continue

            if re.match("\d{4}-\d{2}-\d{2}-YEARLY" + file_type, str_):
                backups_yearly.append(str_)
                continue

        # TODO: Check for overhang and delete it


def create_backup(backup_item, file_name):
    print("Creating backup for %s. Filename: %s" % (backup_item.source, file_name))

    if backup_item.compression == "bz2":
        mode = "w:bz2"
    else:
        mode = "w:gz"

    file_name = os.path.normpath(os.path.join(backup_item.destination, file_name))

    with tarfile.open(file_name, mode) as tar:
        tar.add(backup_item.source, arcname=os.path.basename(backup_item.source))


class Config:
    def __init__(self, config_path):
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

                    if "compression" in data["default"]:
                        self.compression = data["default"]["compression"]

                    if "backup_items" in data:
                        for backups in data["backup_items"]:
                            if os.path.isdir(backups["source"]) & os.path.isdir(backups["source"]):
                                self.backup_items.append(BackupItem(self, backups))

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
        print("Aborting...")
        pass
