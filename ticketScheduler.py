import traceback, os, datetime, calendar
from subprocess import Popen, PIPE, STDOUT

import commvaultToCsv, commvaultFPEditor, credentials
import pyfootprints.csvToFootprints
from email_util import sendMail

FROM = 'cloud-web-util@ucsd.edu'
TO = ['c1mckay@sdsc.edu']

def runProc(cmd):
	my_env = os.environ.copy()

	my_env['OS_TENANT_NAME'] = credentials.open_stack_username
	my_env['OS_USERNAME'] = credentials.open_stack_username
	my_env['OS_PASSWORD'] = credentials.open_stack_pw
	my_env['OS_AUTH_URL_V3'] = credentials.open_stack_url
	my_env['OS_AUTH_URL'] = credentials.open_stack_url_dep

	if type(cmd) != type([]):
		cmd = cmd.split(' ')
	sp = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd='billing', shell=False, env=my_env)
	out, err = sp.communicate()

	return err

def main():
	try:
		commvaultToCsv.main()
		commvaultFPEditor.main()
		subject = 'Commvault usage to Footprints Success!'
		msg = 'Commvault usage was successfully pushed to Footprints\n\nThanks to,\ncloud-web-util'
	except:
		subject = 'Error running commvault scripts'
		msg = traceback.format_exc()

	sendMail(FROM, ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu', 'kcoakley@sdsc.edu'], subject, msg)


	args = []	

	month_ago = commvaultToCsv.month_ago

	now = datetime.date.today()

	if now.day <= 20: #usually not going to hit, as its run after the 19th
		now = month_ago(now)

	cYear = now.year
	cMonth = now.month
	cDay = 20
	endTime = datetime.date(cYear, cMonth, cDay)
	startTime = month_ago(endTime)

	today = datetime.date.today()
	today_f = today.strftime("%Y%m%d")

	cmd = 'cloud-billing -s {0} -e {1} -b reports/{2}.csv -i project_ignore_list.txt -p itemized/{3}/ --graphite --skip-glance --skip-cinder --skip-cinder-snapshots'
	cmd = cmd.format(startTime.strftime("%Y%m%d"), endTime.strftime("%Y%m%d"), today_f, endTime.strftime("%Y%m"))

	args.append(cmd)
	args.append('git add itemized/{0}/'.format(endTime.strftime("%Y%m")))
	args.append('git add reports/{0}.csv'.format(today_f))
	args.append(['git', 'commit', '-m', '"{0} Billing"'.format(today.strftime("%b %Y"))])
	args.append('git push origin master')

	for arg in args:
		error = runProc(arg)
		if error:
			subject = 'Cloud Billing Failed'
			msg = error
			msg += '\n\n'
			msg += arg
			sendMail(FROM, TO, subject, msg)
			print error
			break

	if not error:
		try:
			pyfootprints.csvToFootprints.main('billing/reports/{0}.csv'.format(today_f))
			subject = 'Cloud Billing to Footprints Success!'
			msg = 'Cloud Billing was successfully pushed to Footprints\n\nThanks to,\ncloud-web-util'
		except:
			subject = 'Error running Cloud to FP scripts'
			msg = traceback.format_exc()
		sendMail(FROM, ['c1mckay@sdsc.edu', 'ranakashima@sdsc.edu', 'dferbert@sdsc.edu'], subject, msg)
	



if __name__ == "__main__":
	main()
