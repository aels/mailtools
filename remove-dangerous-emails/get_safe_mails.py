#!/usr/local/bin/python3

import threading, sys, time, re, os, signal, queue, resource, tempfile
try:
	import psutil, requests, IP2Location, dns.resolver, dns.reversename
except ImportError:
	print('\033[1;33minstalling missing packages...\033[0m')
	os.system(sys.executable+' -m pip install psutil requests dnspython IP2Location')
	import psutil, requests, IP2Location, dns.resolver, dns.reversename

if sys.version_info[0] < 3:
	exit('\033[0;31mpython 3 is required. try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

if sys.stdout.encoding is None:
	exit('\033[0;31mplease set python env PYTHONIOENCODING=UTF-8, example: \033[1mexport PYTHONIOENCODING=UTF-8\033[0m')

custom_dns_nameservers = '1.0.0.1,1.1.1.1,8.8.4.4,8.8.8.8,8.20.247.20,8.26.56.26,9.9.9.9,9.9.9.10,64.6.64.6,74.82.42.42,77.88.8.1,77.88.8.8,84.200.69.80,84.200.70.40,149.112.112.9,149.112.112.11,149.112.112.13,149.112.112.112,195.46.39.39,204.194.232.200,208.67.220.220,208.67.222.222'.split(',')
ip2location_url = 'https://github.com/aels/mailtools/releases/download/ip2location/ip2location.bin'
ip2location_path = tempfile.gettempdir()+'/ip2location.bin'
dangerous_users = r'customer|scanner|apps|service|info|sales|admin|director|^hr$|finance|contact|support|security|mail|manager|abuse|job|billing|home|account|report|office|about|help|webmaster|confirm|reply|tech|marketing|feedback|newsletter|orders|verification|calendar|regist|survey|excel|submission|contracts|invite|hello|staff|community|fax|twitter|postmaster|found|catch|test'
dangerous_zones = r'(\.us|\.gov|\.mil|\.edu)$'
dangerous_isps  = r'localhost|invalid|mx37\.m..p\.com|mailinator|mxcomet|mxstorm|proofpoint|perimeterwatch|securence|techtarget|cisco|spiceworks|gartner|fortinet|retarus|checkpoint|fireeye|mimecast|forcepoint|trendmicro|acronis|sophos|sonicwall|cloudflare|trellix|barracuda|security|clearswift|trustwave|broadcom|helpsystems|zyxel|mdaemon|mailchannels|cyren|opswat|duocircle|uni-muenster|proxmox|censornet|guard|indevis|n-able|plesk|spamtitan|avanan|ironscales|mimecast|trustifi|shield|barracuda|essentials|libraesva'
dangerous_isps2 = r'virus|bot|trap|honey|lab|virtual|vm\d|research|abus|security|filter|junk|rbl|ubl|spam|black|list|bad|brukalai|metunet|excello'
dangerous_title = r'<title>[^<]*(security|spam|filter|antivirus)[^<]*<'

resolver_obj = dns.resolver.Resolver()
resolver_obj.nameservers = custom_dns_nameservers
resolver_obj.rotate = True
requests.packages.urllib3.disable_warnings()

b   = '\033[1m'
z   = '\033[0m'
wl  = '\033[2K'
up  = '\033[F'
err = b+'[\033[31mx\033[37m] '+z
okk = b+'[\033[32m+\033[37m] '+z
wrn = b+'[\033[33m!\033[37m] '+z
inf = b+'[\033[34mi\033[37m] '+z
npt = b+'[\033[37m?\033[37m] '+z

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
          ╙     {b}Validol - Email Validator v22.10.23{z}
                Made by {b}Aels{z} for community: {b}https://xss.is{z} - forum of security professionals
                https://github.com/aels/mailtools
                https://t.me/freebug
	"""
	for line in banner.splitlines():
		print(line)
		time.sleep(0.05)

def red(s,type=0):
	return f'\033[{str(type)};31m'+str(s)+z

def green(s,type=0):
	return f'\033[{str(type)};32m'+str(s)+z

def orange(s,type=0):
	return f'\033[{str(type)};33m'+str(s)+z

def blue(s,type=0):
	return f'\033[{str(type)};34m'+str(s)+z

def violet(s,type=0):
	return f'\033[{str(type)};35m'+str(s)+z

def cyan(s,type=0):
	return f'\033[{str(type)};36m'+str(s)+z

def white(s,type=0):
	return f'\033[{str(type)};37m'+str(s)+z

def bold(s):
	return b+str(s)+z

def num(s):
	return f'{int(s):,}'

def debug(msg):
	global debugging, results_que
	if debugging:
		results_que.put((True, msg, ''))

def tune_network():
	try:
		resource.setrlimit(8, (2**14, 2**14))
		print(okk+'tuning rlimit_nofile:          '+', '.join([bold(num(i)) for i in resource.getrlimit(8)]))
	except Exception as e:
		print(wrn+'failed to set rlimit_nofile:   '+orange(e))

def check_database_exists():
	global ip2location_url, ip2location_path
	if not os.path.isfile(ip2location_path):
		print(inf+f'downloading {b}ip2location.bin{z} file. it will take some time...'+up)
		try:
			ip2location_body = requests.get(ip2location_url, timeout=5).content
			open(ip2location_path, 'wb').write(ip2location_body)
		except Exception as e:
			exit(wl+err+'cannot download ip2location.bin: '+red(e))
	print(wl+okk+'ip2location.bin path:          '+bold(ip2location_path))

def first(a):
	return (a or [''])[0]

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def get_url_body(host):
	try:
		return requests.get('https://'+host, timeout=3, verify=False).text
	except:
		return ''

def get_top_host(host):
	host_arr = host.split('.')
	return '.'.join(host_arr[-3 if len(host_arr[-2])<4 else -2:])

def get_ip_of_host(host):
	global resolver_obj
	try:
		host = resolver_obj.resolve(host, 'cname')[0].target
	except:
		pass
	try:
		return resolver_obj.resolve(host, 'a')[0].to_text()
	except Exception as e:
		return re.search(r'solution lifetime expired', str(e)) and (time.sleep(0.5) or get_ip_of_host(host))

def get_ptr(ip):
	global resolver_obj
	try:
		reverse_name = dns.reversename.from_address(ip)
		return str(resolver_obj.resolve(reverse_name, 'ptr')[0])[:-1]
	except Exception as e:
		return re.search(r'solution lifetime expired', str(e)) and (time.sleep(0.5) or get_ptr(ip))

def get_mx_server(domain):
	global resolver_obj
	try:
		return str(resolver_obj.resolve(domain, 'mx')[0].exchange)[:-1]
	except Exception as e:
		return re.search(r'solution lifetime expired', str(e)) and (time.sleep(0.5) or get_mx_server(domain))

def judge_email(email):
	global dangerous_users, dangerous_zones, dangerous_isps, dangerous_isps2, dangerous_title, bads_cache, database, selected_email_providers
	user, host = email.split('@')
	if host in bads_cache:
		raise Exception(bads_cache[host])
	for domain in selected_email_providers.split(','):
		if domain and domain in host:
			return host
	if re.search(dangerous_users, user.lower()):
		raise Exception('bad username: '+user)
	if re.search(dangerous_zones, host.lower()):
		raise Exception('bad zone: '+host)
	email_mx = get_mx_server(host)
	if not email_mx:
		raise Exception('no <mx> records found for: '+host)
	for domain in selected_email_providers.split(','):
		if domain and domain in email_mx:
			return email_mx
	if re.search(dangerous_isps+r'|'+dangerous_isps2, email_mx):
		raise Exception(email_mx)
	email_mx_ip = get_ip_of_host(email_mx)
	if not email_mx_ip:
		raise Exception('no <a> record found for mx server: '+email_mx)
	email_isp = database.get_isp(email_mx_ip) or ''
	if re.search(dangerous_isps+r'|'+dangerous_isps2, email_isp.lower()):
		raise Exception(email_isp)
	reversename = get_ptr(email_mx_ip) or ''
	if re.search(dangerous_isps2, reversename):
		raise Exception(reversename)
	email_mx_top_host = get_top_host(email_mx)
	if email_mx_top_host != email_mx:
		page_body = get_url_body(email_mx_top_host)
		title = first(re.findall(dangerous_title, page_body.lower()))
		if title:
			raise Exception(re.sub(r'<title>|<$', '', title))
	return email_mx

def is_safe_email(email):
	global goods_cache, bads_cache
	host = email.split('@')[-1]
	if not host in goods_cache:
		try:
			goods_cache[host] = judge_email(email)
		except Exception as e:
			bads_cache[host] = str(e)
			raise Exception(bads_cache[host])
	return goods_cache[host]

def extract_email(line):
	return first(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', line))

def quit(signum, frame):
	print('\r\n'+okk+'exiting... see ya later. bye.')
	sys.exit(0)

def wc_count(filename):
	return int(os.popen('wc -l '+filename).read().strip().split(' ')[0])

def worker_item(jobs_que, results_que):
	global min_threads, threads_counter, no_jobs_left, loop_times, goods, bads, progress
	while True:
		if (mem_usage>90 or cpu_usage>90) and threads_counter>min_threads or jobs_que.empty() and no_jobs_left:
			break
		if jobs_que.empty():
			time.sleep(1)
			continue
		else:
			time_start = time.perf_counter()
			line = jobs_que.get()
			try:
				email = extract_email(line)
				results_que.put((True, line, is_safe_email(email)))
				goods += 1
			except Exception as e:
				results_que.put((False, line, str(e)))
				bads += 1
			progress += 1
			time.sleep(0.08)
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
			speed.pop(0) if len(speed)>100 else 0
			progress_old = progress
			mem_usage = round(psutil.virtual_memory()[2])
			cpu_usage = round(sum(psutil.cpu_percent(percpu=True))/os.cpu_count())
			net_usage = psutil.net_io_counters().bytes_sent - net_usage_old
			net_usage_old += net_usage
			loop_time = round(sum(loop_times)/len(loop_times), 2) if len(loop_times) else 0
			if threads_counter<max_threads and mem_usage<80 and cpu_usage<80 and not no_jobs_left:
				threading.Thread(target=worker_item, args=(jobs_que, results_que), daemon=True).start()
				threads_counter += 1
		except:
			pass
		time.sleep(0.1)

def printer(jobs_que, results_que):
	global progress, total_lines, speed, loop_time, cpu_usage, mem_usage, net_usage, threads_counter, goods, bads
	with open(safe_filename, 'a') as safe_file_handle, open(dangerous_filename, 'a') as dangerous_file_handle:
		while True:
			status_bar = (
				f'{b}['+green('\u2665',int(time.time()*2)%2)+f'{b}]{z}'+
				f'[ progress: {bold(num(progress))}/{bold(num(total_lines))} ({bold(round(progress/total_lines*100))}%) ]'+
				f'[ speed: {bold(num(round(sum(speed)/(len(speed) or 1))))}lines/s ({bold(loop_time)}s/loop) ]'+
				f'[ cpu: {bold(cpu_usage)}% ]'+
				f'[ mem: {bold(mem_usage)}% ]'+
				f'[ net: {bold(bytes_to_mbit(net_usage*10))}Mbit/s ]'+
				f'[ threads: {bold(threads_counter)} ]'+
				f'[ goods/bads: {green(num(goods),1)}/{red(num(bads),1)} ]'
			)
			thread_statuses = []
			while not results_que.empty():
				is_ok, line, msg = results_que.get()
				if is_ok:
					thread_statuses.append(' '+line+': '+green(msg))
					safe_file_handle.write(line+'\n')
				else:
					thread_statuses.append(' '+line+': '+red(msg,2))
					dangerous_file_handle.write(line+': '+msg+'\n')
			if len(thread_statuses):
				print(wl+'\n'.join(thread_statuses))
			print(wl+status_bar+up)
			time.sleep(0.08)

signal.signal(signal.SIGINT, quit)
show_banner()
tune_network()
check_database_exists()
try:
	help_message = f'usage: \n{npt}python3 {sys.argv[0]} '+bold('list_with_emails.txt')+' [selected,email,providers]'
	list_filename = sys.argv[1] if len(sys.argv)>1 and os.path.isfile(sys.argv[1]) else ''
	selected_email_providers = sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!='debug' else ''
	debugging = 'debug' in sys.argv
	if not list_filename:
		print(inf+help_message)
		while not os.path.isfile(list_filename):
			list_filename = input(npt+'path to file with emails: ')
		selected_email_providers = input(npt+'domains to left in list, comma separated (leave empty if all): ')
	safe_filename = re.sub(r'\.([^.]+)$', r'_safe.\1', list_filename)
	dangerous_filename = re.sub(r'\.([^.]+)$', r'_dangerous.\1', list_filename)
except:
	print(err+help_message)

jobs_que = queue.Queue()
results_que = queue.Queue()
bads = 0
goods = 0
progress = 0
goods_cache = {}
bads_cache = {}
mem_usage = 0
cpu_usage = 0
net_usage = 0
min_threads = 50
max_threads = debugging and 1 or 300
threads_counter = 0
no_jobs_left = False
loop_times = []
loop_time = 0
speed = []
total_lines = wc_count(list_filename)
database = IP2Location.IP2Location(ip2location_path, 'SHARED_MEMORY')

print(inf+'source file:                   '+bold(list_filename))
print(inf+'total lines to procceed:       '+bold(num(total_lines)))
print(inf+'desired email providers:       '+bold(selected_email_providers or 'all'))
print(inf+'safe emails file:              '+bold(safe_filename))
print(inf+'dangerous emails file:         '+bold(dangerous_filename))
input(npt+'press '+bold('[ Enter ]')+' to start...')

threading.Thread(target=every_second, daemon=True).start()
threading.Thread(target=printer, args=(jobs_que, results_que), daemon=True).start()

with open(list_filename, 'r', encoding='utf-8', errors='ignore') as fp:
	while True:
		while not no_jobs_left and jobs_que.qsize()<min_threads*2:
			line = fp.readline()
			if not line:
				no_jobs_left = True
				break
			if extract_email(line):
				jobs_que.put(line.strip())
			else:
				progress += 1
		if threads_counter == 0 and no_jobs_left:
			break
		time.sleep(0.08)
	print('\r\n'+okk+green('well done. bye.'))
