#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(r'JsonTableSchema/')
import ConfigParser
import JsonTableSchema
from droidcsvhandlerclass import *
from rosettacsvsectionsclass import RosettaCSVSections
from ImportSheetGenerator import ImportSheetGenerator

class RosettaCSVGenerator:

   def __init__(self):
      self.config = ConfigParser.RawConfigParser()
      self.config.read('rosetta-csv-mapping.cfg')   

      self.droidcsv = False
      self.exportcsv = False
      self.rosettaschema = False

   def __init__(self, droidcsv=False, exportsheet=False, rosettaschema=False):
      self.config = ConfigParser.RawConfigParser()
      self.config.read('rosetta-csv-mapping.cfg')   
      
      self.droidcsv = droidcsv
      self.exportsheet = exportsheet
      
      #NOTE: A bit of a hack, compare with import schema work and refactor
      self.rosettaschema = rosettaschema
      self.readRosettaSchema()
      
      #Grab Rosetta Sections
      rs = RosettaCSVSections()
      self.rosettasections = rs.sections
      
      #Get some functions from ImportGenerator
      self.impgen = ImportSheetGenerator()

   def add_csv_value(self, value):
      field = ''
      if type(value) is int:              #TODO: probably a better way to do this (type-agnostic)
         field = '"' + str(value) + '"'
      else:
         field = '"' + value.encode('utf-8') + '"'
      return field

   def readRosettaSchema(self):
      f = open(self.rosettaschema, 'rb')
      importschemajson = f.read()
      importschema = JsonTableSchema.JSONTableSchema(importschemajson)
      
      importschemadict = importschema.as_dict()
      importschemaheader = importschema.as_csv_header()

      self.rosettacsvheader = importschemaheader + "\n"  #TODO: Add newline in JSON Handler class? 
      self.rosettacsvdict = importschemadict['fields']
      f.close()

   def createcolumns(self, columno):
      columns = ''
      for column in range(columno):
         columns = columns + '"",'
      return columns

   def grabdroidvalue(self, md5, itemtitle, field, rosettafield, pathmask):
   
      #TODO: Potentially index droidlist by MD5 or SHA-256 in future...
      returnfield = ""      
      for drow in self.droidlist:
         if drow['MD5_HASH'] == md5:
            if self.impgen.get_title(drow['NAME']) == itemtitle:
               droidfield = drow[rosettafield]
               if field == 'File Location':
                  returnfield = os.path.dirname(droidfield).replace(pathmask, '').replace('\\','/') + '/'
               if field == 'File Original Path':
                  returnfield = droidfield.replace(pathmask, '').replace('\\','/')
               if field == 'File Name':
                  returnfield = droidfield
      return returnfield
     
   def csvstringoutput(self, csvlist):
      #String output...
      csvrows = self.rosettacsvheader

      #TODO: Understand how to get this in rosettacsvsectionclass
      #NOTE: Possibly put all basic RosettaCSV stuff in rosettacsvsectionclass?
      #Static ROW in CSV Ingest Sheet
      SIPROW = ['"",'] * len(self.rosettacsvdict)
      SIPROW[0] = '"SIP",'
      SIPROW[1] = '"CSV Load",'
     
      csvrows = csvrows + ''.join(SIPROW).rstrip(',') + '\n'
      
      for sectionrows in csvlist:
         rowdata = ""
         for sectionrow in sectionrows:
            for fielddata in sectionrow:
               rowdata = rowdata + fielddata + ','
            rowdata = rowdata.rstrip(',') + '\n'
         csvrows = csvrows + rowdata
      sys.stdout.write(csvrows)

   def createrosettacsv(self):
      
      CSVINDEXSTARTPOS = 2
      csvindex = CSVINDEXSTARTPOS
      
      fields = []

      for item in self.exportlist:
         itemrow = []
         
         for sections in self.rosettasections:
            sectionrow = ['""'] * len(self.rosettacsvdict)
            sectionrow[0] = self.add_csv_value(sections.keys()[0])            
            for field in sections[sections.keys()[0]]:
               if field == self.rosettacsvdict[csvindex]['name']:
                  if self.config.has_option('rosetta mapping', field):
                     rosettafield = self.config.get('rosetta mapping', field)
                     addvalue = item[rosettafield]
                     if field == 'Access':
                        if self.config.has_option('access values', addvalue):
                           addvalue = self.config.get('access values', addvalue)
                     sectionrow[csvindex] = self.add_csv_value(addvalue)                     
                  elif self.config.has_option('static values', field):
                     rosettafield = self.config.get('static values', field)
                     sectionrow[csvindex] = self.add_csv_value(rosettafield)
                  elif self.config.has_option('droid mapping', field):          
                     rosettafield = self.config.get('droid mapping', field)
                     
                     #get pathmask for location values...
                     #TODO: Only need to do this once somewhere... e.g. Constructor
                     pathmask = ""
                     if self.config.has_option('path values', 'pathmask'):
                        pathmask = self.config.get('path values', 'pathmask')
     
                     sectionrow[csvindex] = self.add_csv_value(self.grabdroidvalue(item['Missing Comment'], item['Title'], field, rosettafield, pathmask))
                  else:
                     sectionrow[csvindex] = self.add_csv_value(field)
               else:
                  sys.exit(0)
               csvindex+=1
               
            itemrow.append(sectionrow)
         fields.append(itemrow)
         csvindex=CSVINDEXSTARTPOS
      
      self.csvstringoutput(fields)

   def readExportCSV(self):
      if self.exportsheet != False:
         csvhandler = genericCSVHandler()
         exportlist = csvhandler.csvaslist(self.exportsheet)
         return exportlist
   
   def readDROIDCSV(self):
      if self.droidcsv != False:
         droidcsvhandler = droidCSVHandler()
         droidlist = droidcsvhandler.readDROIDCSV(self.droidcsv)
         droidlist = droidcsvhandler.removefolders(droidlist)
         return droidcsvhandler.removecontainercontents(droidlist)        
      
   def export2rosettacsv(self):
      if self.droidcsv != False and self.exportsheet != False:
         self.droidlist = self.readDROIDCSV()
         self.exportlist = self.readExportCSV()
         #self.readRosettaSchema()  #NOTE: Moved to constructor... TODO: Refactor
         self.createrosettacsv()