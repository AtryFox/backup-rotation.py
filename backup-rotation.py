#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
import os
import sys
import json
import re
import tarfile
from datetime import datetime
from collections import defaultdict


class Log(object):
    log_file_opened = False

    log_level_file = 1
    log_level_console = 1

    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

    def __init__(self, filename, log_level_file, log_level_console):
        if filename != "":
            self.log_file = codecs.open(filename, "a+", "utf-8")
            self.log_file_opened = True
            self.log_level_file = log_level_file
        else:
            self.log_level_file = 4

        self.log_level_console = log_level_console

    def __del__(self):
        if self.log_file_opened:
            self.log_file.close()

    def log(self, text, log_level=1):
        msg = "[{0}] [{1}] {2}".format(self.gettimestamp(), self.log_levels[log_level], text)

        if log_level >= self.log_level_file:
            self.log_file.write(msg + "\n")

        if log_level >= self.log_level_console:
            print(msg)

    @staticmethod
    def gettimestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class BackupRotation(object):
    __version__ = "v1.1.0"

    # modified copy of tarfile.add (https://hg.python.org/cpython/file/v3.5.1/Lib/tarfile.py)
    def add(self, tar, name, arcname=None, recursive=True, exclude=None, *, filter=None):
        tar._check("aw")

        if arcname is None:
            arcname = name

        # Exclude pathnames.
        if exclude is not None:
            import warnings
            warnings.warn("use the filter argument instead",
                          DeprecationWarning, 2)
            if exclude(name):
                tar._dbg(2, "tarfile: Excluded %r" % name)
                return

        # Skip if somebody tries to archive the archive...
        if tar.name is not None and os.path.abspath(name) == tar.name:
            tar._dbg(2, "tarfile: Skipped %r" % name)
            return

        tar._dbg(1, name)

        # Create a TarInfo object from the file.
        tarinfo = tar.gettarinfo(name, arcname)

        if tarinfo is None:
            tar._dbg(1, "tarfile: Unsupported type %r" % name)
            return

        # Change or exclude the TarInfo object.
        if filter is not None:
            tarinfo = filter(tarinfo)
            if tarinfo is None:
                tar._dbg(2, "tarfile: Excluded %r" % name)
                return

        bltn_open = tar.open

        # Append the tar header and data to the archive.
        if tarinfo.isreg():
            with bltn_open(name, "rb") as f:
                try:
                    tar.addfile(tarinfo, f)
                except Exception as e:
                    self.log("An error occurred: %s" % e.strerror, 3)

        elif tarinfo.isdir():
            tar.addfile(tarinfo)
            if recursive:
                for f in os.listdir(name):
                    try:
                        tar.add(os.path.join(name, f), os.path.join(arcname, f),
                                recursive, exclude, filter=filter)
                    except Exception as e:
                        self.log("An error occurred: %s" % e.strerror, 3)

        else:
            try:
                tar.addfile(tarinfo)
            except Exception as e:
                self.log("An error occurred: %s" % e.strerror, 3)

    def create_backup(self, backup_item, file_name):
        self.log("Creating backup... Filename: %s" % file_name)

        mode = "w:" + backup_item["compression"]

        file_path = os.path.normpath(os.path.join(backup_item["destination"], file_name))

        if os.path.exists(file_path):
            self.log("%s already exists. Skipping..." % file_name)
            return

        with tarfile.open(file_path, mode) as tar:
            BackupRotation.add(self, tar, backup_item["source"], arcname=os.path.basename(backup_item["source"]))

    def load_config(self, config_path):
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

        i = 0
        for raw_backup_item in data["backup_items"]:
            if "source" not in raw_backup_item or "destination" not in raw_backup_item:
                self.log("Backup item no {0} invalid. Skipping...".format(i), 2)
            elif not os.path.isdir(raw_backup_item["source"]):
                self.log("Source path \"{0}\" not valid! (backup item no {1})".format(raw_backup_item["source"], i), 2)
            elif not os.path.isdir(raw_backup_item["destination"]):
                self.log("Destination path \"{0}\" not valid! (backup item no {1})".format(raw_backup_item["source"], i), 2)
            else:
                backup_item = result["default"].copy()
                backup_item.update(raw_backup_item)
                backup_items.append(backup_item)

            i += 1

        result["backup_items"] = backup_items

        return result

    def __init__(self):
        config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "config.json"))
        log_path = ""
        log_level_file = 1
        log_level_console = 1

        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg == "-q":
                log_level_console = 4
            elif arg == "-c":
                if len(sys.argv) > i + 1:
                    config_path = sys.argv[i + 1]
            elif arg == "-l":
                if len(sys.argv) > i + 1:
                    log_path = sys.argv[i + 1]
            elif arg == "-lv":
                if len(sys.argv) > i + 1:
                    log_level_file = int(sys.argv[i + 1])

        self.log = Log(log_path, log_level_file, log_level_console).log

        self.log("backup-rotation.py " + self.__version__)

        if not os.path.isfile(config_path):
            self.log("Stated configfile not found, aborting...", 3)
            exit()

        config_data = self.load_config(config_path)
        self.log("Configuration loaded: %s" % config_path, 1)

        now = datetime.now()

        # Start rotation for every backup item
        for backup_item in config_data["backup_items"]:
            self.log("Starting backup routine for %s..." % backup_item["source"])

            if not backup_item["compression"] in ["gz", "xz", "bz2"]:
                self.log("Unknown compression type \"{0}\". Using lzma.".format(backup_item["compression"]), 2)
                backup_item["compression"] = "xz"

            file_extension = ".tar." + backup_item["compression"]

            file_prefix = now.strftime("%Y-%m-%d")

            no_backups_created = True

            timetuple = now.timetuple()

            for max_backups, current_date, backup_date, period_name in [
                (backup_item["daily_backups"], None, None, "DAILY"),
                (backup_item["weekly_backups"], timetuple.tm_wday, backup_item["create_backup_day_of_week"], "WEEKLY"),
                (backup_item["monthly_backups"], timetuple.tm_mday, backup_item["create_backup_day_of_month"],
                 "MONTHLY"),
                (backup_item["yearly_backups"], timetuple.tm_yday, backup_item["create_backup_day_of_year"], "YEARLY")
            ]:
                if max_backups > 0:
                    if current_date == backup_date:
                        file_name = file_prefix + "-" + period_name + file_extension
                        self.create_backup(backup_item, file_name)
                        no_backups_created = False

            if no_backups_created:
                self.log("No backups created.")

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
                    self.log("Overhang found ({0} backups). Deleting {1} old backup(s)...".format(period_name, overhang))

                    files = sorted(files, key=os.path.getctime)

                    for i in range(0, overhang):
                        self.log("Deleting {0}...".format(os.path.basename(files[i])))
                        os.remove(files[i])

        self.log("Backup rotation finished.")


if __name__ == "__main__":
    try:
        BackupRotation()
    except KeyboardInterrupt:
        print("Aborting...")
