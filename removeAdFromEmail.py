from holonetComm import queryHolonet, getColumnNames


def main():
	for x in getColumnNames():
		print x

	possible_names = ['MRSUBMITTER', 'MRASSIGNEES', 'MREF_TO_AB', 'ITEM__B0__SELLER', 'MRREF_TO_MR']
	possible_names = ['MRSUBMITTER', 'MRASSIGNEES','MRREF_TO_AB', 'ITEM__B1__BSELLER', 'MRREF_TO_MRX', 'MRREF_TO_MR']

	qString = "SELECT MRID, "

	for x in possible_names:
		qString += x
		qString += ", "

	qString = qString[:-2]

	qString += " FROM FOOTPRINTS.MASTER3 WHERE "
	for x in possible_names[:-1]:
		qString += x
		qString += " LIKE '%ad.sdsc.edu%' or "

	qString += possible_names[-1]
	qString += " LIKE '%ad.sdsc.edu%' OR MRID = 79889"

	print qString

	print queryHolonet(qString)


if __name__ == "__main__":
	main()
