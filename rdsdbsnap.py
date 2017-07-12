#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""dbsnap is a DB snapshot management tool for Amazon RDS.
Demo tool used for educational purposes in http://blog.codebender.cc/2015/12/08/automating-db-snapshots-at-amazon-rds/

Expanded and updated by Grzegorz Adamowicz
"""

import boto3
import click
import time
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone

__version__ = '0.1.3'


class DBSnapshot(object):
    """DBSnapshot"""

    def __init__(self):
        self.client = boto3.client('rds')

    def create(self, prefix_name, db_instance, timestamp):
        """Creates a new DB snapshot"""
        snapshot = "{0}-{1}-{2}".format(prefix_name, db_instance, timestamp)
        self.client.create_db_snapshot(DBSnapshotIdentifier=snapshot, DBInstanceIdentifier=db_instance)
        time.sleep(2)  # wait 2 seconds before status request
        current_status = None

        while True:
            current_status = self.__status(snapshot=snapshot)
            if current_status == 'available' or current_status == 'failed':
                break

            # we need to wait a bit due to rate exceeded errors
            time.sleep(10)

        return current_status

    def delete(self, snapshot):
        """Deletes a user-specified DB snapshot"""
        # from botocore.errorfactory import InvalidDBSnapshotStateFault
        try:
            current_status = self.__status(snapshot=snapshot)
            if current_status == 'available':
                self.client.delete_db_snapshot(DBSnapshotIdentifier=snapshot)
                current_status = self.__status(snapshot=snapshot)
        except:
            current_status = 'does not exist'

        return current_status


    def list_instances(self):
        """Lists the available RDS instances"""
        return self.client.describe_db_instances()['DBInstances']

    def list_snapshots(self, db_instance):
        """Lists all available snapshots"""
        return self.client.describe_db_snapshots(DBInstanceIdentifier='{0}'.format(db_instance))['DBSnapshots']

    def __status(self, snapshot):
        """Returns the current status of the DB snapshot"""
        print(self.client.describe_db_snapshots(DBSnapshotIdentifier=snapshot)['DBSnapshots'][0]['Status'])
        return self.client.describe_db_snapshots(DBSnapshotIdentifier=snapshot)['DBSnapshots'][0]['Status']


@click.group()
@click.version_option(version=__version__)
def cli():
    """dbsnap is a DB snapshot management tool for Amazon RDS."""
    pass


@cli.command()
def instances():
    """Returns the available RDS instances"""
    dbcon = DBSnapshot()
    db_instances = dbcon.list_instances()
    click.echo("Database Instances:")
    for instance in db_instances:
        print("\t- {0}".format(instance['DBInstanceIdentifier']))

@cli.command()
@click.option('--db-instance', help='Database instance')
def list_snapshots(db_instance):
    """Returns the available RDS instance snapshots"""
    if not db_instance:
        click.echo("Please specify a database using --db-instance option", err=True)
        return sys.exit(1)

    dbcon = DBSnapshot()
    db_snapshots = sorted(dbcon.list_snapshots(db_instance=db_instance), key=lambda k: k['SnapshotCreateTime'], reverse=True)

    click.echo("Database Snapshosts:")

    for snapshot in db_snapshots:
        print("\t- {0}\t- {1}".format(snapshot['DBSnapshotIdentifier'], snapshot['SnapshotCreateTime']))


@cli.command()
@click.option('--db-instance', help='Database instance')
@click.option('--older-than-days', help='Remove snapshots older than provided number of days')
def delete_snapshots(db_instance, older_than_days):
    """Deletes snapshots older than X days"""
    if not db_instance:
        click.echo("Please specify a database using --db-instance option", err=True)
        return sys.exit(1)

    if not older_than_days:
        click.echo("Please specify number of days using --older-than-days option", err=True)
        return sys.exit(1)

    days = int(older_than_days)

    dbcon = DBSnapshot()
    db_snapshots = sorted(dbcon.list_snapshots(db_instance=db_instance), key=lambda k: k['SnapshotCreateTime'], reverse=True)

    # timestamp for snapshots older than this date minus X days
    delete_time = datetime.now(timezone.utc) - timedelta(days=days)

    deletion_counter = 0

    for snapshot in db_snapshots:
        # print(snapshot)
        start_time = snapshot['SnapshotCreateTime']

        if start_time < delete_time and snapshot['SnapshotType'] == "manual":
            print('Deleting snapshot {0}'.format(snapshot["DBSnapshotIdentifier"]))
            deletion_counter = deletion_counter + 1

            response = dbcon.delete(snapshot=snapshot["DBSnapshotIdentifier"])
            print("\tStatus: {0}".format(response))

    print("Deleted {0} snapshots".format(deletion_counter))

@cli.command()
@click.option('--db-instance', help='Database instance')
@click.option('--snapshot-prefix', default='script-automated-snapshot', help='Prefix for snapshot name, default: script-automated-snapshot')
def create(snapshot_prefix, db_instance):
    """Creates a new DB snapshot"""
    if not db_instance:
        click.echo("Please specify a database using --db-instance option", err=True)
        return sys.exit(1)

    dbcon = DBSnapshot()
    date = datetime.now()
    timestamp = date.strftime("%Y-%m-%d")
    click.echo("Creating a new snapshot from {0} instance...".format(db_instance))
    response = dbcon.create(prefix_name=snapshot_prefix, db_instance=db_instance, timestamp=timestamp)
    click.echo("Snapshot status: {0}".format(response))


@cli.command()
@click.option('--db-snapshot', help='Database snapshot')
def delete(db_snapshot):
    """Deletes a user-specified DB snapshot"""
    if not db_snapshot:
        click.echo("Please specify a database using --db-snapshot option", err=True)
        return sys.exit(1)
    dbcon = DBSnapshot()
    response = dbcon.delete(snapshot=db_snapshot)
    if response == 'does not exist':
        output = "Snapshot: {0} has been deleted".format(db_snapshot)
    else:
        output = "Snapshot: {0} deletion failed".format(db_snapshot)
    click.echo(output)


