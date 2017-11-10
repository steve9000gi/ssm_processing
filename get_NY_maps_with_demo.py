#!/usr/bin/env python

""" get_NY_maps_with_demo.py: Retrieve and write as .json files all the system
    support maps (ssms) from the ssm database that have a "state" key in
    the "document" field and where the associated value is "NY".

    Usage:
        get_NY_maps_with_demo.py output_directory

    Args:
        output_directory: a directory into which all the ssm .json files are to
        be written. If it doesn't exist it will be created.

    The "SELECT * from maps" statement returns a list of tuples. Each tuple is
    an ssm plus its associated metadata and is comprised of the following
    elements:

    index type      contents                 column name in database
    ___________________________________________________________________________
    0     int       map id                   id
    1     int       owner id                 owner
    2     dict      the ssm                  document
    3     datetime  created timestamp        created_at
    4     datetime  last modified timestamp  modified_at
    5     str       map name                 name

    The tuples in the list are sorted in ascending order of the elements with
    index 4 (last modified timestamp).

    The element at index 3 in each tuple in the list is a dict which contains
    the actual system support map. For our present purposes we're interested
    only in those dicts which contain a "state" key and a corresponding value
    = "NY".

    For each one of those ssms that meets this criterion, print some useful
    tracking info to stdout and write the dict to file in .json format.

    From PostgreSQL database:
    -> extract list of tuples
    -> examine each tuple of metadata + dict
    -> write to file each dict with key "state" the value of which = "NY"
"""

import sys
import os
import collections
import json
import string
import re
import psycopg2
from ssm_utilities import connect, get_maps


def print_header():
    print ("      Size (bytes)     Last modified")
    print "_" * 75


def get_pad1(n):
    """ Whitespace padding for right-aligning printed integers.

        Arg:
            n: the integer to be right-aligned. Assumes that n < 10000.

       Returns:
            a string with the appropriate amount of whitespace.
    """
    if n < 10:
        return "   "
    if n < 100:
        return "  "
    if n < 1000:
        return " "
    return ""


def get_pad2(s1, s2):
    """ Returns a string of whitespace padding to insert between strings s1
        and s2 so that the length of s1 + padding + s2 = 40.
    """
    return " " * (12 - len(s1) - len(s2))


def print_row(n, sz, last_modified):
    """ Print some handy tracking info about an ssm to stdout.

        Args:
            n: integer row number.
            sz: integer size in bytes of the current ssm as a string.
            last_modified: string represenatation of datetime object.

        Returns:
            Nothing
    """
    print (get_pad1(n) + str(n) + ". " + get_pad2("", sz) + sz +
           " " * 2 + last_modified)


def build_output_file_path(dir, role, id):
    """ Create a full path for an ssm file.

        Args:
            dir: string path to directory, either relative or absolute. No
            checking to see if the path is valid.
            role: the value of the "role" node in the map
            id: integer to be used in assembling the file name.

        Returns:
            cleaned-up string (spurious whitespace and punctuation removed) to
            be used as full path to .json file.
    """
    clean_dir = dir.rstrip("/")
    punct = string.punctuation
    junk = punct + " "
    trantab = string.maketrans(junk, "_________________________________")
    clean_role = role.encode("ascii", "replace").strip(junk).translate(trantab)
    path = (clean_dir + "/" + clean_role + "-" + str(id) + ".json")
    return re.sub(r'(_)\1+', r'\1', path)


def write_map_to_file(dir, role, map_id, d):
    """ Write a dict to an ssm .json file.

        Args:
            dir: string path to directory.
            role: the value of the "role" node in the map
            map_id: int used to build file name.
            d: the dict that's to be written to file as .json.

        Returns:
            Nothing
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    path = build_output_file_path(dir, role, map_id)
    with open(path, "w") as f:
        json.dump(d, f, sort_keys=True, indent=4)
        f.close()


def get_role(ssm):
    """ Get the role the user entered in ssm.

        Arg:
            ssm: A System Support Map.

        Returns:
            the "name" value of the node with type "role," unless there is no
            such node, in which case "no role" is returned.
    """
    nodes = ssm["nodes"]
    for node in nodes:
        if node["type"] == "role":
            return node["name"]
    return "no role"


def main():
    IX_SSM_ID = 0
    IX_OWNER_ID = 1
    IX_DOC = 2
    IX_MODIFIED_AT = 4
    IX_SSM_NAME = 5
    dir = sys.argv[1]
    maps = get_maps(IX_MODIFIED_AT)
    n = 0
    print_header()
    for map in maps:
        map_id = map[IX_SSM_ID]
        owner = map[IX_OWNER_ID]
        last_modified = map[IX_MODIFIED_AT].strftime("%Y-%m-%d %H:%M")
        name = map[IX_SSM_NAME]
        d = map[IX_DOC]
        if "state" in d and str(d["state"]) == "NY" and owner not in [2]: #noSC
            # and owner not in [2, 20]: # exclude SC, KHL
            n += 1
            sz = str(len(str(d)))
            role = get_role(d)
            print_row(n, sz, last_modified)
            write_map_to_file(dir, role, map_id, d)


if __name__ == "__main__":
    main()
