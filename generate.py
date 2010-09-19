#!/usr/bin/python
 # -*- coding: UTF-8 -*-
import PyRSS2Gen, ConfigParser
import flickrapi
import shutil
import os, string, sys
from datetime import datetime
from  image_page import image_page
from browse import browse
from os import path
   
class Zenit:
   max = 0
   photos = {}
   def sortDict(self,adict):
      keys = adict.keys()
      keys.sort(reverse = True)
      return map(adict.get, keys)
   
   def getElementByAttrValue(self,element, childType, attributeName, value):
      for el in element.findall(childType):
          if el.get(attributeName) == value: return el
      return None
   
   def generate(self):
      self.config = ConfigParser.ConfigParser()
      self.config.read([os.path.expanduser('~/.zenit')]) 
      
      self.flickr = flickrapi.FlickrAPI(self.config.get('zenit','api_key'), self.config.get('zenit','api_secret'))
      
            
      (token, frob) = self.flickr.get_token_part_one(perms='write')
      if not token: raw_input("Press ENTER after you authorized this program")
      self.flickr.get_token_part_two((token, frob))
      
      self.starttime = datetime.strptime(self.config.get('zenit','start_time'),"%Y%m%d")
      self.currentweek = (datetime.now() - self.starttime).days / 7
      self.loadPhotos()
      self.generatePhotoPages()
      self.generateBrowsePage()
      self.generateRss()
   
   
   def loadPhotos(self):
     set_id = self.config.get('zenit','set_id')
     print "getting photos from set " + set_id
     setphotos = self.flickr.walk_set(set_id)
     limit = 4
     idx = 1
     for photo in setphotos:
        print "loading photo information for photo No. " + str(idx)
        exif = self.flickr.photos_getExif(photo_id=photo.get('id'),secret = photo.get('secret'));
        sizes = self.flickr.photos_getSizes(photo_id=photo.get('id'));
        normal = self.getElementByAttrValue(sizes,'sizes/size','label','Medium 640')
        
        p = Photo()
        origdate = ""
        for ex in exif.findall('photo/exif'):
           if (ex.get('tag') == 'DateTimeOriginal'):
            origdate = ex.find('raw').text
        p.imagetime = datetime.strptime(origdate,"%Y:%m:%d %H:%M:%S")
        a = p.imagetime - self.starttime
        p.week = (a.days / 7) + 1
        
        small = self.getElementByAttrValue(sizes,'sizes/size','label','Thumbnail');
        p.small_url = small.get('source')
        p.normal_url = normal.get('source')
        p.width = normal.get('width')
        p.height = normal.get('height')
        self.photos[p.week] = p        
        
        #calculate max week
        if (self.max == 0 or self.max<p.week): 
           self.max = p.week
           
        idx+=1
        if (idx>limit):
           break
      
   def generatePhotoPages(self):
      max = 0
      i = 0
      images = {}
      for week in iter(self.photos):         
         photo = self.photos[week]
         self.generatePhotoPage(photo)
         print "generating page " + str(photo.week) + ".html"
         
         
                
      shutil.copyfile(str(self.max)+".html","index.html")

   def generatePhotoPage(self,photo):
      tpl = image_page()         
      tpl.currentweek = self.currentweek
      tpl.photo = photo
   
      out = open(str(photo.week) + '.html','w')
      out.write(tpl.respond())
      out.close()
      
   def generateBrowsePage(self):  
      #hianyzo hetek potlasa
      for w in range(1, self.currentweek):
         if not w in self.photos:
            p = Photo()
            p.small_url = 'thumb_unknown.jpg'
            p.week = w
            p.width = 500
            p.height = 333
            p.normal_url = 'small_unknown.jpg'
            p.imagetime = '???'
            self.generatePhotoPage(p)
            self.photos[w] = p   
            
      tpl = browse()
      tpl.photos = self.sortDict(self.photos)
      out = open("browse.html",'w')
      out.write(tpl.respond())
      out.close() 
      
   def generateRss(self):  
      url = self.config.get('zenit','start_time')
      items = []
      print self.max
      
      for week in range(self.max, max(self.max - 20,1),-1):
         photo = self.photos[week]
         items.append(PyRSS2Gen.RSSItem(
            title = str(photo.week),
            link = url + str(photo.week)+".html",
            description = '<img src="'+photo.normal_url+'\">',
            guid = PyRSS2Gen.Guid(url,str(photo.week)+".html"),
            pubDate = photo.imagetime))         
            
      rss = PyRSS2Gen.RSS2(
          title = "ES",
          link = url,
          description = "1 het -- 1 kep",
          lastBuildDate = self.photos[self.max].imagetime,
          items = items
          )
      
      rss.write_xml(open("atom.xml", "w"))

class Photo:
   pass   

z = Zenit()
z.generate()