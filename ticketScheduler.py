import traceback, os
from subprocess import Popen, PIPE, STDOUT

import commvaultToCsv, commvaultFPEditor, credentials
from email_util import sendMail

def main():
	try:
		#commvaultToCsv.main()
		#commvaultFPEditor.main()
		subject = 'Commvault usage to Footprints Success!'
		msg = 'Commvault usage was successfully pushed to Footprints\n\nThanks to,\ncloud-web-util'
	except:
		subject = 'Error running commvault scripts'
		msg = traceback.format_exc()

	#sendMail('cloud-web-util@ucsd.edu', ['c1mckay@sdsc.edu'], subject, msg)

	os.environ['OS_TENANT_NAME'] = credentials.open_stack_username
	os.environ['OS_USERNAME'] = credentials.open_stack_username
	os.environ['OS_PASSWORD'] = credentials.open_stack_pw
	os.environ['OS_AUTH_URL_V3'] = credentials.open_stack_url

	cmd = 'cloud-billing -s 20161220 -e 20170120 -b reports/20170020.csv -i project_ignore_list.txt -p itemized/201700/ --graphite --skip-glance --skip-cinder --skip-cinder-snapshots'.split(' ')
	sp = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd='billing')
	out, err = sp.communicate()
	if out:
	    print "standard output of subprocess:"
	    print out
	if err:
	    print "standard error of subprocess:"
	    print err


if __name__ == "__main__":
	main()