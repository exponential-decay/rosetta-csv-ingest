#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(r'JsonTableSchema/')
import ConfigParser
import JsonTableSchema
from droidcsvhandlerclass import *
from rosettacsvsectionsclass import RosettaCSVSections

class RosettaCSVGenerator:

   includezips = False

   def __init__(self, droidcsv=False, rosettaschema=False, configfile=False):
      self.config = ConfigParser.RawConfigParser()
      self.config.read(configfile)   

      if self.config.has_option('application configuration', 'includezips'):
         self.includezips = self.__handle_text_boolean__(self.config.get('application configuration', 'includezips'))

      self.droidcsv = droidcsv
      
      #NOTE: A bit of a hack, compare with import schema work and refactor
      self.rosettaschema = rosettaschema
      self.readRosettaSchema()
      
      #Grab Rosetta Sections
      rs = RosettaCSVSections(configfile)
      self.rosettasections = rs.sections

   def __handle_text_boolean__(self, boolvalue):
      if boolvalue.lower() == 'true':
         return True
      else:
         return False

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

      for item in self.droidlist:
         itemrow = []
         for sections in self.rosettasections:
         
            sectionrow = ['""'] * len(self.rosettacsvdict)
            sectionrow[0] = self.add_csv_value(sections.keys()[0])
            for field in sections[sections.keys()[0]]:
               if field == self.rosettacsvdict[csvindex]['name']:

                  if self.config.has_option('rosetta mapping', field):
                     rosettafield = self.config.get('rosetta mapping', field)
                     addvalue = item[rosettafield]
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

                        addvalue = item[rosettafield]

                        if field == 'File Location':
                           if not self.includezips:
                              addvalue = os.path.dirname(item[rosettafield]).replace(pathmask, '').replace('\\','/') + '/'
                           else:
                              path = item['URI']
                              addvalue = "/".join(urlparse(path).path.split('/')[1:-1]).replace(pathmask, '').replace('\\','/') + '/'
                        if field == 'File Original Path':
                           addvalue = item[rosettafield].replace(pathmask, '').replace('\\','/')

                     sectionrow[csvindex] = self.add_csv_value(addvalue)
                  else:
                     sectionrow[csvindex] = self.add_csv_value(field)

               
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
         if not self.includezips:         
            droidlist = droidcsvhandler.removecontainercontents(droidlist)        
         return droidlist      

   def export2rosettacsv(self):
      if self.droidcsv != False:
         self.droidlist = self.readDROIDCSV()
         self.createrosettacsv()
