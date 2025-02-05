"""
A script for cloning the FERC Form 1 database into SQLite.

This script generates a SQLite database that is a clone/mirror of the original
FERC Form1 database. We use this cloned database as the starting point for the
main PUDL ETL process. The underlying work in the script is being done in
:mod:`pudl.extract.ferc1`.
"""

import argparse
import logging
import pathlib
import sys

import coloredlogs
import yaml

import pudl
import pudl.constants as pc

# Create a logger to output any messages we might have...
logger = logging.getLogger(__name__)


def parse_command_line(argv):
    """
    Parse command line arguments. See the -h option.

    Args:
        argv (str): Command line arguments, including caller filename.

    Returns:
        dict: Dictionary of command line arguments and their parsed values.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings_file", type=str, default='',
                        help="path to YAML settings file.")
    arguments = parser.parse_args(argv[1:])
    return arguments


def main():
    """Clone the FERC Form 1 FoxPro database into SQLite."""
    # Display logged output from the PUDL package:
    logger = logging.getLogger(pudl.__name__)
    log_format = '%(asctime)s [%(levelname)8s] %(name)s:%(lineno)s %(message)s'
    coloredlogs.install(fmt=log_format, level='INFO', logger=logger)

    args = parse_command_line(sys.argv)
    with pathlib.Path(args.settings_file).open() as f:
        script_settings = yaml.safe_load(f)

    try:
        pudl_in = script_settings["pudl_in"]
    except KeyError:
        pudl_in = pudl.workspace.setup.get_defaults()["pudl_in"]
    try:
        pudl_out = script_settings["pudl_out"]
    except KeyError:
        pudl_out = pudl.workspace.setup.get_defaults()["pudl_out"]

    pudl_settings = pudl.workspace.setup.derive_paths(
        pudl_in=pudl_in, pudl_out=pudl_out)

    # Make sure the required input files are available before we go doing a
    # bunch of work cloning the database...
    pudl.helpers.verify_input_files(
        ferc1_years=script_settings['ferc1_to_sqlite_years'],
        eia860_years=[],
        eia923_years=[],
        epacems_years=[],
        epacems_states=[],
        pudl_settings=pudl_settings
    )

    # Check args for basic validity:
    for table in script_settings['ferc1_to_sqlite_tables']:
        if table not in pc.ferc1_tbl2dbf:
            raise ValueError(
                f"{table} was not found in the list of "
                f"available FERC Form 1 tables."
            )
    if script_settings['ferc1_to_sqlite_refyear'] \
            not in pc.data_years['ferc1']:
        raise ValueError(
            f"Reference year {script_settings['ferc1_to_sqlite_refyear']} "
            f"is outside the range of available FERC Form 1 data "
            f"({min(pc.data_years['ferc1'])}-"
            f"{max(pc.data_years['ferc1'])})."
        )
    for year in script_settings['ferc1_to_sqlite_years']:
        if year not in pc.data_years['ferc1']:
            raise ValueError(
                f"Requested data from {year} is outside the range of "
                f"available FERC Form 1 data "
                f"({min(pc.data_years['ferc1'])}-"
                f"{max(pc.data_years['ferc1'])})."
            )

    pudl.extract.ferc1.dbf2sqlite(
        tables=script_settings['ferc1_to_sqlite_tables'],
        years=script_settings['ferc1_to_sqlite_years'],
        refyear=script_settings['ferc1_to_sqlite_refyear'],
        pudl_settings=pudl_settings,
        bad_cols=script_settings['ferc1_to_sqlite_bad_cols'])


if __name__ == '__main__':
    sys.exit(main())
