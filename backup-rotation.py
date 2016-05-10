#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import tarfile
from datetime import datetime
from collections import defaultdict

__version__ = "v1.0.0-rc1"


# modified copy of tarfile.add (https://hg.python.org/cpython/file/v3.5.1/Lib/tarfile.py)
def add(self, name, arcname=None, recursive=True, exclude=None, *, filter=None):
    self._check("aw")

    if arcname is None:
        arcname = name

    # Exclude pathnames.
    if exclude is not None:
        import warnings
        warnings.warn("use the filter argument instead",
                      DeprecationWarning, 2)
        if exclude(name):
            self._dbg(2, "tarfile: Excluded %r" % name)
            return

    # Skip if somebody tries to archive the archive...
    if self.name is not None and os.path.abspath(name) == self.name:
        self._dbg(2, "tarfile: Skipped %r" % name)
        return

    self._dbg(1, name)

    # Create a TarInfo object from the file.
    tarinfo = self.gettarinfo(name, arcname)

    if tarinfo is None:
        self._dbg(1, "tarfile: Unsupported type %r" % name)
        return

    # Change or exclude the TarInfo object.
    if filter is not None:
        tarinfo = filter(tarinfo)
        if tarinfo is None:
            self._dbg(2, "tarfile: Excluded %r" % name)
            return

    bltn_open = self.open

    # Append the tar header and data to the archive.
    if tarinfo.isreg():
        with bltn_open(name, "rb") as f:
            try:
                self.addfile(tarinfo, f)
            except Exception as e:
                print("   An error occurred: %s" % e.strerror)

    elif tarinfo.isdir():
        self.addfile(tarinfo)
        if recursive:
            for f in os.listdir(name):
                try:
                    self.add(os.path.join(name, f), os.path.join(arcname, f),
                             recursive, exclude, filter=filter)
                except Exception as e:
                    print("   An error occurred: %s" % e.strerror)

    else:
        try:
            self.addfile(tarinfo)
        except Exception as e:
            print("   An error occurred: %s" % e.strerror)


def create_backup(backup_item, file_name):
    print("Creating backup... Filename: %s" % file_name)

    mode = "w:" + backup_item["compression"]

    file_path = os.path.normpath(os.path.join(backup_item["destination"], file_name))

    if os.path.exists(file_path):
        print("   %s already exists. Skipping..." % file_name)
        return

    with tarfile.open(file_path, mode) as tar:
        add(tar, backup_item["source"], arcname=os.path.basename(backup_item["source"]))


def load_config(config_path):
    with open(config_path) as config_file:
        data = json.load(config_file)

    result = dict()

    result["default"] = {
        'create_backup_day_of_week': 0,
        'create_backup_day_of_month': 1,
        'create_backup_day_of_year': 1,

        'daily_backups': 7,
        'weekly_backups': 4,
        'monthly_backups': 6,
        'yearly_backups': 4,

        'compression': 'xz',
    }

    result["default"].update(data["default"])

    backup_items = list()

    for raw_backup_item in data["backup_items"]:
        if "source" not in raw_backup_item or "destination" not in raw_backup_item:
            print("Backup item invalid. Skipping...")
        elif not os.path.isdir(raw_backup_item["source"]):
            print("Source path \"{0}\" not valid!".format(raw_backup_item["source"]))
        elif not os.path.isdir(raw_backup_item["destination"]):
            print("Destination path \"{0}\" not valid!".format(raw_backup_item["source"]))
        else:
            backup_item = result["default"].copy()
            backup_item.update(raw_backup_item)
            backup_items.append(backup_item)

    result["backup_items"] = backup_items

    return result


def main():
    print("backup-rotation.py", __version__)

    # Load configuration
    if len(sys.argv) < 2:
        config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "config.json"))
        print("No configfile stated, using default ({0})".format(config_path))
    else:
        config_path = sys.argv[1]

    if not os.path.isfile(config_path):
        print("Stated configfile not found, aborting...")
        exit()

    config_data = load_config(config_path)
    print("Configuration loaded: %s" % config_path)

    now = datetime.now()

    # Start rotation for every backup item
    for backup_item in config_data["backup_items"]:
        print("\nStarting backup routine for %s..." % backup_item["source"])

        if not backup_item["compression"] in ["gz", "xz", "bz2"]:
            print("Unknown compression type \"{0}\". Using lzma.".format(backup_item["compression"]))
            backup_item["compression"] = "xz"

        file_extension = ".tar." + backup_item["compression"]

        file_prefix = now.strftime("%Y-%m-%d")

        no_backups_created = True

        # Create backups if necessary
        if backup_item["daily_backups"] > 0:
            file_name = file_prefix + "-DAILY" + file_extension
            create_backup(backup_item, file_name)
            no_backups_created = False

        if backup_item["weekly_backups"] > 0:
            if now.timetuple().tm_wday == backup_item["create_backup_day_of_week"]:
                file_name = file_prefix + "-WEEKLY" + file_extension
                create_backup(backup_item, file_name)
                no_backups_created = False

        if backup_item["monthly_backups"] > 0:
            if now.timetuple().tm_mday == backup_item["create_backup_day_of_month"]:
                file_name = file_prefix + "-MONTHLY" + file_extension
                create_backup(backup_item, file_name)
                no_backups_created = False

        if backup_item["yearly_backups"] > 0:
            if now.timetuple().tm_yday == backup_item["create_backup_day_of_year"]:
                file_name = file_prefix + "-YEARLY" + file_extension
                create_backup(backup_item, file_name)
                no_backups_created = False

        if no_backups_created:
            print("No backups created.")

        # Check for old backups
        backups = os.listdir(backup_item["destination"])

        old_backups = defaultdict(list)

        for str_ in backups:
            match = re.match("\d{4}-\d{2}-\d{2}-(DAILY|WEEKLY|MONTHLY|YEARLY)" + re.escape(file_extension), str_)

            if match:
                old_backups[match.group(1)].append(os.path.normpath(os.path.join(backup_item["destination"], str_)))

        # Check for overhang in old backups and delete it
        for period_name, max_backups in [
            ('DAILY', backup_item["daily_backups"]),
            ('WEEKLY', backup_item["weekly_backups"]),
            ('MONTHLY', backup_item["monthly_backups"]),
            ('YEARLY', backup_item["yearly_backups"]),
        ]:

            files = old_backups[period_name]
            overhang = len(files) - max_backups

            if overhang > 0:
                print("Overhang found ({0} backups). Deleting {1} old backup(s)...".format(period_name, overhang))

                files = sorted(files, key=os.path.getctime)

                for i in range(0, overhang):
                    print("   Deleting {0}...".format(os.path.basename(files[i])))
                    os.remove(files[i])

    print("\nBackup rotation finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborting...")
