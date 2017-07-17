#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""check_snapshots is a Nagios/Icinga plugin that checks latest snapshot date
"""

import boto3
import click
import time
import sys
from datetime import timedelta
from datetime import datetime
from datetime import timezone
# from rdsdbsnap import DBSnapshot

__version__ = '0.1.0'

# All nagios return codes
nagios_codes = {
    'OK': 0,
    'WARNING': 1,
    'CRITICAL': 2,
    'UNKNOWN': 3,
    'DEPENDENT': 4,
}

class DBSnapshot(object):
    """DBSnapshot"""

    def __init__(self):
        self.client = boto3.client('rds')

    def newest_snapshot(self, db_instance):
        """Show newest snapshot"""
        snapshots = sorted(self.client.describe_db_snapshots(DBInstanceIdentifier='{0}'.format(db_instance))['DBSnapshots'], key=lambda k: k['SnapshotCreateTime'], reverse=True)
        return snapshots[0]


@click.group()
@click.version_option(version=__version__)
def cli():
    """check_snapshots is a Nagios/Icinga plugin that checks latest snapshot date"""
    pass

@cli.command()
@click.option('--db-instance', help='Database instance')
@click.option('--not-older-than-days', help='How old in days we expect our snapshot will be')
def status(db_instance, not_older_than_days):
    """Return date and time of newest snapshot"""
    if not db_instance:
        click.echo("Please specify a database using --db-instance option", err=True)
        return sys.exit(nagios_codes['UNKNOWN'])

    if not not_older_than_days:
    	click.echo("Please specify --not-older-than-days option", err=True)
    	return sys.exit(nagios_codes['UNKNOWN'])

    dbcon = DBSnapshot()
    snapshot_data = dbcon.newest_snapshot(db_instance=db_instance)

    snapshot_time = snapshot_data['SnapshotCreateTime']
    boundary_time = datetime.now(timezone.utc) - timedelta(days=int(not_older_than_days))

    # print(snapshot_time)
    # print(boundary_time)

    if snapshot_data['SnapshotCreateTime'] > boundary_time:
    	print('OK - Snapshot time is {0}, expected to be younger than {1}'.format(snapshot_time.strftime('%Y-%m-%d %H:%M'), boundary_time.strftime('%Y-%m-%d %H:%M')))
    	return sys.exit(nagios_codes['OK'])
    else:
    	print('CRITICAL - Snapshot time is {0}, expected to be younger than {1}'.format(snapshot_time.strftime('%Y-%m-%d %H:%M'), boundary_time.strftime('%Y-%m-%d %H:%M')))
    	return sys.exit(nagios_codes['CRITICAL'])

if __name__ == "__main__":
	cli()
