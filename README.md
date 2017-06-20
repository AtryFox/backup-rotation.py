backup-rotation.py
==================
Simple Python 3 script for rotating your backups. 

## Features ##
- [x] Create backups/backup rotations of multiple directories
- [x] Define different settings for every backup source
- [x] Support for diffrent compression methods
- [x] Logging


## Requirements ##
- Python 3

## Installation ##
1. Download the `backup-rotation.py` on your server and create a [configuration file](#configuration).

		wget https://raw.githubusercontent.com/DerAtrox/backup-rotation.py/master/backup-rotation.py

2. Test the script and your configuration.

		python3 backup-rotation.py -c [path to your config.json]

3. Add a cronjob, so the script runs daily.

		crontab -e

	Put the following line into your crontab. This will run the script every day 1 hour after midnight.

		0 1 * * * python3 -c [path to backup_rotation.py] -q

	Want some log files? Check out our [parameters](#parameters).

<div id='parameters'></div>

## Parameters ##
You can use some parameters to create log files or disable console output.

| Parameter     | Description                                                        | Default                           |
|:--------------|:-------------------------------------------------------------------|:----------------------------------|
| `-c <path>`   | `<path>` to your configuration file                                | config.json in the same directory |
| `-l <path>`   | `<path>` to your logfile                                           | no log output                     |
| `-lv <level>` | Specifies the [loglevel](#loglevels) for your logfile              | 1                                 |
| `-q`          | Quiet, no console output                                           |                                   |


<div id='loglevels'></div>

#### Loglevels ####
- Loglevel `0`: Debug messages
- Loglevel `1`: Generic information
- Loglevel `2`: Warnings (e.g. backupitem invalid)
- Loglevel `3`: Errors (e.g. config not found)


<div id='configuration'></div>

## Configuration ##
The configuration of `backup-rotation.py` is stored in a *.json*-file. To get started, just copy or download the `default-config.json` on your server.
```
wget https://raw.githubusercontent.com/DerAtrox/backup-rotation.py/master/default-config.json
```


#### Valid options ####

| Key                          | Target                      | Description                                              |
|:-----------------------------|:----------------------------|:---------------------------------------------------------|
| `create_backup_day_of_week`  | `default` and `backup_item` | The day of the week on which to create a backup          |
| `create_backup_day_of_month` | `default` and `backup_item` | The day of the month on which to create a backup         |
| `create_backup_day_of_year`  | `default` and `backup_item` | The day of the year on which to create a backup          |
| `daily_backups`              | `default` and `backup_item` | Count of how many daily backups to keep                  |
| `weekly_backups`             | `default` and `backup_item` | Count of how many weekly backups to keep                 |
| `monthly_backups`            | `default` and `backup_item` | Count of how many monthly backups to keep                |
| `yearly_backups`             | `default` and `backup_item` | Count of how many yearly backups to keep                 |
| `compression`                | `default` and `backup_item` | Compression type (Supported types: `gz`, `xz` and `bz2`) |
| `source`                     | `backup_item`               | Source directory of backup                               |
| `destination`                | `backup_item`               | Destination directory of backups                         |


#### Default section ####
All values inside of the `default`array are used as default values. These values are used unless otherwise defined by a backup item.

#### Backup_items section ####
`backup_items` is a array containing multiple `backup_item`s. One `backup_item` has to have the keys `source` and `destination`. All other values are optional.

#### Examples #####
Check out the `example-config.json` for more config samples.
