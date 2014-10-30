#!/usr/local/bin/python3.4

import datetime
import urllib.request
import calendar
import fileinput
import os
import sys
import re
import linecache

class video:
	def __init__(self, videoName, teamName, teamAbbrev, folderURL):
		self.videoName = videoName
		self.compressions = []
		self.teamName = teamName
		self.teamAbbrev = teamAbbrev
		self.fileNameEnd = 'k.mp4'
		if folderURL:
			self.folderURL = folderURL.split('?')[0]
	def newCompression(self, compression):
		self.compressions.append(compression)
		self.compressions.sort(reverse = True)
	def noCompressions(self):
		self.compressions = None
	def setValidCompressions(self, acceptableCompressions):
		# the intersection of available and valid compressions, sorted largest to smallest
		if self.compressions:
			self.validCompressions = list(set(self.compressions).intersection(acceptableCompressions))
			self.validCompressions.sort(reverse = True)
			try:
				self.validCompressions[0]
				return True
			except IndexError:
				return False
		else:
			self.validCompressions = None
			return True
	def release(self, destEmailAddress, feedType, liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot):
		self.sendEmailAlert(destEmailAddress, feedType, liveStatus)
		self.logEmailAlert(logFile, feedType)
		if downloadOrNot == 'download':
			self.download(pathToContentDirectories, teamsList)
	def sendEmailAlert(self, destEmailAddress, feedType, liveStatus):
		fromAddress = 'alerts@sldesksite.com'
		toAddress = destEmailAddress
		smtpUsername = 'dummy address'
		smtpPassword = 'dummy pass'
		smtpServer = 'smtp.sendgrid.net'
		smtpPort = '587'
		smtpString = str.join(':', (smtpServer, smtpPort))
		messageSubject = str.join(' ', (teamName, feedType, liveStatus))
		messageBody = self.videoName + str(self.bestCompression) + self.fileNameEnd
		# this is the literal command that is executed by the OS shell
		compiledSendEmailCommand = str.join(' ', ('/usr/bin/sendemail -xu', smtpUsername, '-xp', smtpPassword, '-s', smtpString, '-f', fromAddress, '-t', toAddress, '-u', messageSubject, '-m', messageBody))#, '>> /dev/null'))
		# this is the execution of that command
		exitStatus = int(1)
		while not exitStatus == 0:
			exitStatus = os.system(compiledSendEmailCommand)
	def logEmailAlert(self, logFile, feedType):
		with open(logFile, 'a+') as logFileOpened:
			currentDate = datetime.datetime.now().strftime('%G-%m-%d %X %a %b %d')
			logEntry = currentDate + ' ' + self.videoName + ' ' + feedType + ' ' + self.teamName + '\n'
			logFileOpened.write(logEntry)
	def download(self, pathToContentDirectories, teamsList):
		fullURL = self.folderURL + self.videoName + str(self.bestCompression) + self.fileNameEnd
		teamNameCapitalized = teamName.capitalize()
		localFolderName = pathToContentDirectories + os.sep + teamNameCapitalized + ' (' + teamsList[teamNameCapitalized] + ')' + os.sep + '_exports' + os.sep + datetime.datetime.now().strftime('%Y%m%d')
		videoDestination = localFolderName + os.sep + self.videoName + str(self.bestCompression) + self.fileNameEnd
		try:
			os.stat(localFolderName)
		except:
			os.mkdir(localFolderName)
		videoOnTheWeb = urllib.request.urlopen(fullURL)
		serverResponse = urllib.request.urlretrieve(fullURL, videoDestination)
		videoOnTheWeb.close()
	def determineBestAvailableCompression(self, maxFileSize, acceptableCompressions):
		# all the available compressions that are usable, in descending order
		if self.compressions:
			if self.setValidCompressions(acceptableCompressions):
				fullURL = self.folderURL + self.videoName + str(self.validCompressions[0]) + self.fileNameEnd
				with urllib.request.urlopen(fullURL) as videoOnTheWeb:
					filesize = videoOnTheWeb.length
					for compression in self.validCompressions:
						try:
							if filesize < maxFileSize:
								self.bestCompression = compression
								return True
							# file too big, find the size of the smaller, more appropriate file
							else:
								# this compression / the next best one
								try:
									ratio = compression / self.validCompressions[self.validCompressions.index(compression) + 1]
									filesize = filesize / ratio
								except IndexError:
									self.bestCompression = compression
									return True
						except TypeError:
							# sometimes, videos don't show filesize information. Rare, but it happens.
								self.bestCompression = compression
								return True

			else:
				return False
		else:
			#no compression information
			self.fileNameEnd = '.mp4'
			self.bestCompression = ''
			return True

def getCurrentBackendVideos(teamName, teamAbbrev, backendURL):
	# get the page
	try:
		currentPage = urllib.request.urlopen(backendURL)
		html = currentPage.read()
		htmlDecoded = html.decode('utf-8', 'ignore')
	except urllib.error.HTTPError as err:
		if err.code == 404:
			htmlDecoded = ''
		else:
			raise
	return extractVideosFromPage(htmlDecoded, teamName, teamAbbrev, backendURL)

def getCurrentFrontendVideos(teamName, teamAbbrev, frontendURL, backendURL):
	# get the page
	currentPage = urllib.request.urlopen(frontendURL)
	html = currentPage.read()
	htmlDecoded = html.decode('utf-8', 'ignore')

	return extractVideosFromPage(htmlDecoded, teamName, teamAbbrev, backendURL)

def extractVideosFromPage(htmlDecoded, teamName, teamAbbrev, backendURL):
	# initialize the return list
	currentVideos = dict()

	# search for mp4s in the page
	for line in htmlDecoded.split('\"'):
		if line.endswith('.mp4'):
			if re.search(r'/', line):
			# behaves slightly differently if its from the frontend because frontend videos can come from different folders
				splitLine = line.split('/')
				folderURL = '/'.join(splitLine[:-1]) + '/'
				line = splitLine[-1]
			else:
				folderURL = backendURL
			# splits the video into its filename root and the compression
			if line.endswith('5000k.mp4'):
				videoName = line[:-9]
				compression = int(line[-9:-5])
			elif line.endswith('3200k.mp4'):
				videoName = line[:-9]
				compression = int(line[-9:-5])
			elif line.endswith('2000k.mp4'):
				videoName = line[:-9]
				compression = int(line[-9:-5])
			elif line.endswith('1200k.mp4'):
				videoName = line[:-9]
				compression = int(line[-9:-5])
			elif line.endswith('700k.mp4'):
				videoName = line[:-8]
				compression = int(line[-8:-5])
			elif line.endswith('500k.mp4'):
				videoName = line[:-8]
				compression = int(line[-8:-5])
			elif line.endswith('320k.mp4'):
				videoName = line[:-8]
				compression = int(line[-8:-5])
			elif line.endswith('180k.mp4'):
				videoName = line[:-8]
				compression = int(line[-8:-5])
			# if there is no compression, proceed anyways. This is handled later
			elif line.endswith('.mp4'):
				videoName = line[:-4]
				compression = None
			# put the information into the dictionary of videos
			if not videoName in currentVideos:
				currentVideos[videoName] = video(videoName, teamName, teamAbbrev, folderURL)
				if compression:
					currentVideos[videoName].newCompression(compression)
				else:
					currentVideos[videoName].noCompressions()
			else:
				if not compression in currentVideos[videoName].compressions:
					currentVideos[videoName].newCompression(compression)
	return currentVideos

def getOldVideosFromFile(file, teamName, teamAbbrev):
	oldVideos = dict()
	try:
		with open(file, 'r') as oldVideosFile:
			for line in oldVideosFile:
				lineFields = line.split()
				videoName = lineFields.pop(0)
				oldVideos[videoName] = video(videoName, teamName, teamAbbrev, None)
				for compression in lineFields:
					if not compression == 'None':
						oldVideos[videoName].newCompression(int(compression))
					else:
						oldVideos[videoName].noCompressions()
				oldVideos[videoName].setValidCompressions(AcceptableCompressions)
	except FileNotFoundError:
		pass
	return oldVideos

def releaseAppropriateVideos(currentVideos, oldVideos, destEmailAddress, feedType, liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot):
	for videoIndex in currentVideos:
		video = currentVideos[videoIndex]
		try:
			oldVideo = oldVideos[video.videoName]
			if video.compressions:
				# if the video has compression information
				# otherwise, don't release it, because it can't be new, or this would have broken on the oldVideo lookup
				if video.setValidCompressions(AcceptableCompressions):				
					if not oldVideo.setValidCompressions(AcceptableCompressions):
						oldVideo.validCompressions = [0]
					if video.validCompressions[0] > oldVideo.validCompressions[0] and video.determineBestAvailableCompression(MaximumVideoSize, AcceptableCompressions):
						# if the new compressions are better than the old compressions
						if not video.bestCompression in oldVideo.validCompressions:
							video.release(destEmailAddress, feedType, liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot)
		except KeyError:
			# means that the video is new
			if video.determineBestAvailableCompression(MaximumVideoSize, AcceptableCompressions):
				video.release(destEmailAddress, feedType, liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot)

def updateOldVideosFile(file, newVideos):
	# update modified lines
	updatedFile = []
	try:
		with open(file, 'r') as oldVideosFile:
			for line in oldVideosFile:
				videoIndex = line.split()[0]
				if videoIndex in newVideos:
					newVideo = newVideos.pop(videoIndex)
					compiledLine = newVideo.videoName
					try:
						for compression in newVideo.compressions:
							compiledLine = compiledLine + ' ' + str(compression)
						updatedLine = compiledLine + '\n'
					except TypeError:
						updatedLine = compiledLine + ' ' + 'None' + '\n'
				else:
					updatedLine = line
				updatedFile.append(updatedLine)
	except FileNotFoundError:
		pass
	for newVideo in newVideos:
		video = newVideos[newVideo]
		compiledLine = video.videoName
		try:
			for compression in video.compressions:
				compiledLine = compiledLine + ' ' + str(compression)
		except TypeError:
			compiledLine = compiledLine + ' ' + 'None'
		compiledLine = compiledLine + '\n'
		updatedFile.append(compiledLine)
	with open(file, 'w') as oldVideosFile:
		for line in updatedFile:
			oldVideosFile.write(line)

def readListOfTeams(filesPath):
	listOfTeams = filesPath + 'contentDirectoryStructure.list'
	with open(listOfTeams, 'r') as teamsList:
		return dict(line.strip().split() for line in teamsList)

def sendErrorEmail(errorMessage):
		fromAddress = 'alerts@sldesksite.com'
		toAddress = 'dummy recipient'
		smtpUsername = 'dummy address'
		smtpPassword = 'dummy pass'
		smtpServer = 'smtp.sendgrid.net'
		smtpPort = '587'
		smtpString = str.join(':', (smtpServer, smtpPort))
		messageSubject = "feedalert error"
		try:
			messageBody = sys.argv[1]
		except:
			messageBody = 'cannot get teamName '
		messageBody = ' \'' + messageBody + errorMessage + '\''
			
		# this is the literal command that is executed by the OS shell
		compiledSendEmailCommand = str.join(' ', ('/usr/bin/sendemail -xu', smtpUsername, '-xp', smtpPassword, '-s', smtpString, '-f', fromAddress, '-t', toAddress, '-u', messageSubject, '-m', messageBody))#, '>> /dev/null'))
		# this is the execution of that command
		exitStatus = int(1)
		while not exitStatus == 0:
			exitStatus = os.system(compiledSendEmailCommand)


if __name__ == "__main__":
	try:
		teamName = sys.argv[1]
		teamNameForFrontend = sys.argv[2]
		teamAbbrev = sys.argv[3]
		destEmailAddress = sys.argv[4]
		downloadOrNot = sys.argv[5]
		feedType = sys.argv[6]
		liveStatus = sys.argv[7]
		filesPath = '/home/webmon/python/'
		oldFrontendVideosFile = str.join('', (filesPath, teamName, ".frontendvideos.list"))
		oldBackendVideosFile = str.join('', (filesPath, teamName, ".backendvideos.list"))
		logFile = filesPath + 'contentegress.log'
		emailLogFile = filesPath + 'emailegress.log'
		teamsList = readListOfTeams(filesPath)
		pathToContentDirectories = '/mnt/NFL'

		# URL for the backend	
		baseURL = str.join('', ('http://prod.video.', teamName, '.clubs.nfl.com/', teamAbbrev, '/videos/dct/video_audio/'))
		yearString = str(datetime.datetime.now().year)
		monthNumericString = str(datetime.datetime.today().month).zfill(2)
		monthNameString = calendar.month_name[datetime.datetime.now().month]
		microsecondString = str(datetime.datetime.now().microsecond)
		currentDateFolder = str.join('', (yearString, '/', monthNumericString, '-', monthNameString, '/?', microsecondString))
		backendURL = str.join('', (baseURL, currentDateFolder))
		# URL for the frontend
		frontendURL = str.join('', ('http://www.', teamNameForFrontend, '.com/cda-web/feeds/video'))


		# global variables
		# frankly, I should make most of these global. It would make the program a hell of a lot easier to read
		MaximumVideoSize = 100000000
		AcceptableCompressions = [2000, 1200, 700]
	
		currentFrontendVideos = getCurrentFrontendVideos(teamName, teamAbbrev, frontendURL, backendURL)
		currentBackendVideos = getCurrentBackendVideos(teamName, teamAbbrev, backendURL)
		oldFrontendVideos = getOldVideosFromFile(oldFrontendVideosFile, teamName, teamAbbrev)
		oldBackendVideos = getOldVideosFromFile(oldBackendVideosFile, teamName, teamAbbrev)

		if feedType == 'frontend' or feedType == 'both':
			releaseAppropriateVideos(currentFrontendVideos, oldFrontendVideos, destEmailAddress, 'frontend', liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot)
		if feedType == 'backend' or feedType == 'both':
			releaseAppropriateVideos(currentBackendVideos, oldBackendVideos, destEmailAddress, 'backend', liveStatus, logFile, pathToContentDirectories, teamsList, downloadOrNot)
	
		updateOldVideosFile(oldFrontendVideosFile, currentFrontendVideos)
		updateOldVideosFile(oldBackendVideosFile, currentBackendVideos)
	except:
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filename = f.f_code.co_filename
		linecache.checkcache(filename)
		line = linecache.getline(filename, lineno, f.f_globals)
		errorMessage = str('EXCEPTION IN ({}\n LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)) + ' ' + frontendURL
		sendErrorEmail(errorMessage)
		print('unhandled exception')
