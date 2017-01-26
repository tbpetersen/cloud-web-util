import datetime
import calendar, math
import json, urllib
from datetime import timedelta


FDATA_URL = "https://graphite.sdsc.edu:8443/render/?width=600&height=400&target=keepLastValue(services.commvault.frontend.{0})&from=00%3A00_{1}&until=23%3A59_{2}&format=json"
BDATA_URL = "https://graphite.sdsc.edu:8443/render/?width=600&height=400&target=keepLastValue(services.commvault.backend.{0})&from=00%3A00_{1}&until=23%3A59_{2}&format=json"



def month_ago(sourcedate):
	month = sourcedate.month
	year = sourcedate.year
	month -= 1
	if month == 0:
		month = 12
		year -= 1
	daysInLastMonth = calendar.monthrange(year, month)[1]
	daysToSubtract = max(sourcedate.day, daysInLastMonth)
	return sourcedate - datetime.timedelta(days = daysToSubtract)

def fixData(buckets, dataPoints, dataPointSize):
	timeData = {}
	for point in dataPoints:
		data = point[0]
		time = point[1]
		if data == None:
			continue
		time = datetime.datetime.fromtimestamp(time)
		if time not in buckets:
			print time
		if time in timeData:
			data = min(data, timeData[time])
		timeData[time] = data
	#these points, i have no data for
	errorPoints = [b for b in buckets if b not in timeData]
	# ePoints are hour intervals that I don't have data for
	# I need to fill in this data with later data, which is likely the same
	for ePoint in errorPoints:
		index = buckets.index(ePoint) + 1
		stoppedService = True
		while index < dataPointSize:
			ePointOffset = buckets[index]
			if ePointOffset in timeData:
				timeData[ePoint] = timeData[ePointOffset]
				stoppedService = False
				break
			else:
				index += 1
		if stoppedService:
			timeData[ePoint] = 0
	return timeData

def main():
	graphite_url = "https://graphite.sdsc.edu:8443/render/?width=600&height=400&target=services.commvault.frontend.*&from=00%3A00_{0}&until=23%3A59_{1}&format=json"

	now = datetime.date.today()

	if now.day <= 19: #usually not going to hit, as its run after the 19th
		now = month_ago(now)

	cYear = now.year
	cMonth = now.month
	cDay = 19
	endTime = datetime.date(cYear, cMonth, cDay)
	startTime = (month_ago(endTime) + datetime.timedelta(days = 1))
	dataPointSize = (endTime - startTime).days * 24 + 24

	startHour = datetime.datetime(startTime.year, startTime.month, startTime.day, 0)
	buckets = [timedelta(hours = i) + startHour for i in range(dataPointSize)]


	startTimeText = startTime.strftime('%Y%m%d')
	endTimeText = endTime.strftime('%Y%m%d')
	startTimeTextCSV = startTime.strftime('%Y-%m-%d')
	endTimeTextCSV = endTime.strftime('%Y-%m-%d')

	graphite_url = graphite_url.format(startTimeText, endTimeText)
	graphite_data = json.loads(urllib.urlopen(graphite_url).read())

	users = [service['target'].replace('services.commvault.frontend.', '') for service in graphite_data]

	csv_contents = ''
	for user in users:
		fdata_url = FDATA_URL.format(user, startTimeText, endTimeText)
		fdata = json.loads(urllib.urlopen(fdata_url).read())
		if len(fdata) != 0:
			fdata = fdata[0]
			entries = fixData(buckets, fdata['datapoints'], dataPointSize).values()
			faverage = sum(entries) / len(entries)
			faverage /= (1000 * 1000 * 1000 * 1000)
		else:
			faverage = 0
		bdata_url = BDATA_URL.format(user, startTimeText, endTimeText)
		bdata = json.loads(urllib.urlopen(bdata_url).read())
		if len(bdata) != 0:
			bdata = bdata[0]
			entries = fixData(buckets, bdata['datapoints'], dataPointSize).values()
			baverage = sum(entries) / len(entries)
			baverage /= (1000 * 1000 * 1000 * 1000)
		else:
			baverage = 0
		if faverage != 0 and baverage != 0:
			faverage = math.ceil(faverage*100)/100
			baverage = math.ceil(baverage*100)/100
			line_item_f = '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n'
			line_item_f = line_item_f.format(startTimeTextCSV,endTimeTextCSV,user,'Andrew','Ferbert','dferbert@sdsc.edu','6','commvault-frontEnd (','SDSC Commvault','Commvault On-Disk TB','91.67',str(faverage))
			csv_contents += line_item_f
			line_item_b = '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n'
			line_item_b = line_item_b.format(startTimeTextCSV,endTimeTextCSV,user,'Andrew','Ferbert','dferbert@sdsc.edu','6','commvault-backEnd (','SRF Cloud','Commvault Storage','35.17',str(baverage))
			csv_contents += line_item_b

	file = open('commvault.csv', 'w+')
	file.write(csv_contents)
	file.close()


if __name__ == "__main__":
	main()
