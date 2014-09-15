#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from RosettaCSVGenerator import RosettaCSVGenerator

def rosettacsvgeneration(droidcsv, rosettaschema):
   csvgen = RosettaCSVGenerator(droidcsv, rosettaschema)
   csvgen.export2rosettacsv()

def main():

   #	Usage: 	--csv [droid report]
   #	Handle command line arguments for the script
   parser = argparse.ArgumentParser(description='Generate Archway Import Sheet and Rosetta Ingest CSV from DROID CSV Reports.')

   #TODO: Consider optional and mandatory elements... behaviour might change depending on output...
   #other options droid csv and rosetta schema
   #NOTE: class on its own might be used to create a blank import csv with just static options
   parser.add_argument('--csv', help='Single DROID CSV to read.', default=False, required=False)
   parser.add_argument('--ros', help='Rosetta CSV validation schema', default=False, required=False)

   if len(sys.argv)==1:
      parser.print_help()
      sys.exit(1)

   #	Parse arguments into namespace object to reference later in the script
   global args
   args = parser.parse_args()
   
   if args.csv and args.ros:
      rosettacsvgeneration(args.csv, args.exp, args.ros)
   else:
      parser.print_help()
      sys.exit(1)

if __name__ == "__main__":
   main()
