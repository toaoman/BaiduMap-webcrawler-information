# -*- coding: utf-8 -*- 
import requests
import os
import re
import csv
import json
import time

import wx
import wx.xrc

import frame
import threading

from wx.lib.pubsub import pub
from bs4 import BeautifulSoup

class BaiduMap():
	"""docstring for BaiduMap"""
	def __init__(self):
		super(BaiduMap, self).__init__()

	def getCityData(self,cityName):

		try:
			webData = requests.get("http://map.baidu.com/?newmap=1&qt=cur&ie=utf-8&wd=" + cityName + "&oue=1&res=jc").text
			jsonData = json.loads(webData)

			if 'weather' in jsonData: #存在天气预报的情况下
				weatherData = json.loads(jsonData['weather'])
				wx.CallAfter(pub.sendMessage, "updateText", content=weatherData['OriginQuery']+" PM2.5:"+weatherData['pm25']+weatherData['weather0']+"["+weatherData['temp0']+"]["+weatherData['wind0']+"]")
			if 'cur_area_id' in jsonData:
				wx.CallAfter(pub.sendMessage, "updateText", content="城市id:" + str(jsonData['cur_area_id']))
				return jsonData['cur_area_id']
			else:
				return -1

		except Exception as e:
			raise

	def createAndWrite(self,fileName,rowHeader,rowData=[]):

		if os.path.exists(fileName):
			fileName = str(time.time()) + "_" + fileName

		csvFile = open(fileName,'w',newline='')
		writer  = csv.writer(csvFile)

		writer.writerow(rowHeader)
		if len(rowData) > 0:
			writer.writerows(rowData)
		csvFile.close()

	def getMapData(self,cityId,info_): 

		if cityId < 0 :
			return -1

		loopValue = 1
		loopCount = 1

		allData   = []

		qt        = "s"
		rn        = "10" 
		modNum    = "10"

		rowHeader = ['name','address','address_norm']
		

		while loopValue <= loopCount:

			getUrl    = "http://api.map.baidu.com/?qt=" + qt + "&c=" + str(cityId) + "&wd=" + info_ + "&rn=" + rn + "&pn=" + str(loopValue - 1) + "&ie=utf-8&oue=1&fromproduct=jsapi&res=api&callback=BMap._rd._cbk7303&ak=E4805d16520de693a3fe707cdc962045";

			webData   = requests.get(getUrl).text
			tempValue = int(re.search("\"total\":([\\s\\S]*?),",webData).group(1)) #数量

			if tempValue > 0:
				if loopValue == 1:
					modNum    = tempValue % 10 # 第一次
					if modNum > 0:
						loopCount = (int)(tempValue / 10 + 1)
					else :
						loopCount = (int)(tempValue / 10)

					wx.CallAfter(pub.sendMessage, "updateText", content="总共需要循环：" + str(loopCount))

				reJson   = re.search("content\":([\\s\\S]*?),\"current_city",webData).group(1)
				jsonData = json.loads(reJson)
				# 数据处理
				wx.CallAfter(pub.sendMessage, "updateText", content="retrieving: page " + str(loopValue))
				# print(jsonData)
				for x in range(0,len(jsonData)):
					try:
						# print(jsonData[x]['name'] + " " + jsonData[x]['address_norm'] + " " + jsonData[x]['addr'])
						tempArr = [jsonData[x]['name'],jsonData[x]['addr'],jsonData[x]['address_norm']]
						allData.append(tempArr)
					except Exception as e:
						print(jsonData[x])
						# exit()
					
				# 处理结束
				loopValue = loopValue + 1
			else :
				
				break

		if len(allData) > 0:
			wx.CallAfter(pub.sendMessage, "updateText", content="ok . writing file!!!")
			rstr = r"[\/\\\:\*\?\"\<\>\|\$$]"
			self.createAndWrite(str(cityId) + "_" + re.sub(rstr,"_",info_) + ".csv",rowHeader,allData)

			wx.CallAfter(pub.sendMessage, "updateText", content="over")

		else :
			wx.CallAfter(pub.sendMessage, "updateText", content="error content")

class windowGUI(frame.MyFrame1):
	"""docstring for windowGUI"""
	obj = BaiduMap()

	def __init__(self,parent):
		super(windowGUI, self).__init__(parent)

	def checkCity( self, event ):
		print(event)
	
	def startJob( self, event ):
		newThread = webThread(1,"Thread-1",1)
		newThread.start()

class webThread(threading.Thread):
	"""docstring for webThread"""
	def __init__(self,threadID, name ,counter):

		super(webThread, self).__init__()
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter
	
	def run(self):
		obj = BaiduMap()
		obj.getMapData(obj.getCityData("潮州"),"古巷镇$$美食")
# wx.CallAfter(pub.sendMessage, "update", msg=i)
if __name__ == '__main__':

	app    = wx.App(False)
	frame1 = windowGUI(None)
	frame1.Show(True)
	app.MainLoop()
	# obj   = BaiduMap()
	# obj.getMapData(obj.getCityData("潮州"),"古巷镇$$美食")