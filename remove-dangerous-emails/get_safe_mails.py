#!/usr/local/bin/python3

import threading, sys, time, re, os, signal, queue, tempfile
try:
	import psutil, requests, IP2Location, dns.resolver, dns.reversename
except ImportError:
	print('\033[0;33minstalling missing packages...\033[0m')
	os.system('apt -y install python3-pip; '+sys.executable+' -m pip install psutil requests dnspython IP2Location')
	import psutil, requests, IP2Location, dns.resolver, dns.reversename

if sys.version_info[0] < 3:
	exit('\033[0;31mpython 3 is required. try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

ip2location_url = 'https://github.com/aels/mailtools/releases/download/ip2location/ip2location.bin'
domains_whitelist_url = 'https://cdn.jsdelivr.net/gh/aels/mailtools/remove-dangerous-emails/domains_whitelist.txt'
ip2location_path = tempfile.gettempdir()+'/ip2location.bin'
domains_whitelist_path = tempfile.gettempdir()+'/domains_whitelist.txt'
whitelisted_mx  = r'(google\.com|outlook\.com|googlemail\.com|qq\.com|improvmx\.com|registrar-servers\.com|emailsrvr\.com|secureserver\.net|yandex\.net|amazonaws\.com|zoho\.com|messagingengine\.com|mailgun\.org|netease\.com|yandex\.ru|ovh\.net|gandi\.net|zoho\.eu|mxhichina\.com|mail\.ru|sbnation\.com|beget\.com|securemx\.jp|hostedemail\.com|arsmtp\.com|yahoodns\.net|protonmail\.ch|pair\.com|ne\.jp|1and1\.com|ispgateway\.de|dreamhost\.com|amazon\.com|dfn\.de|aliyun\.com|163\.com|mailanyone\.net|suremail\.cn|privateemail\.com|one\.com|espmailservice\.net|nic\.in|kasserver\.com|oxcs\.net|everyone\.net|above\.com|timeweb\.ru|serverdata\.net|forwardemail\.net|bund\.de|mailhostbox\.com|kundenserver\.de|ionos\.com|expedia\.com|icoremail\.net|hostedmxserver\.com|263xmail\.com|infomaniak\.ch|hostinger\.com|automattic\.com|alibaba-inc\.com|feishu\.cn|cnhi\.com|h-email\.net|zohomail\.com|outlook\.cn|easydns\.com|cscdns\.net|zoho\.in|name\.com|migadu\.com|mailbox\.org|untd\.com|stackmail\.com|kagoya\.net|forwardmx\.io|carrierzone\.com|ucoz\.net|renr\.es|redhat\.com|hotmail\.com|hostinger\.in|fusemail\.net|disney\.com|bell\.ca)$'
dangerous_users = r'^hr$|about|abuse|admin|apps|billing|calendar|catch|community|confirm|contact|contracts|customer|daemon|director|excel|fax|feedback|finance|found|hello|help|home|info|invite|job|mail|manager|marketing|newsletter|office|orders|postmaster|regist|reply|report|sales|scanner|security|service|staff|submission|support|survey|tech|test|twitter|verification|webmaster'
dangerous_zones = r'\.(gov|mil|edu)(\.[a-z.]+|$)'
dangerous_isps  = r'acronis|acros|adlice|alinto|appriver|aspav|atomdata|avanan|avast|barracuda|baseq|bitdefender|broadcom|btitalia|censornet|checkpoint|cisco|cistymail|clean-mailbox|clearswift|closedport|cloudflare|comforte|corvid|crsp|cyren|darktrace|data-mail-group|dmarcly|drweb|duocircle|e-purifier|earthlink-vadesecure|ecsc|eicar|elivescanned|eset|essentials|exchangedefender|fireeye|forcepoint|fortinet|gartner|gatefy|gonkar|guard|helpsystems|heluna|hosted-247|iberlayer|indevis|infowatch|intermedia|intra2net|invalid|ioactive|ironscales|isync|itserver|jellyfish|kcsfa.co|keycaptcha|krvtz|libraesva|link11|localhost|logix|mailborder.co|mailchannels|mailcleaner|mailcontrol|mailinator|mailroute|mailsift|mailstrainer|mcafee|mdaemon|mimecast|mx-relay|mx1.ik2|mx37\.m..p\.com|mxcomet|mxgate|mxstorm|n-able|n2net|nano-av|netintelligence|network-box|networkboxusa|newnettechnologies|newtonit.co|odysseycs|openwall|opswat|perfectmail|perimeterwatch|plesk|prodaft|proofpoint|proxmox|redcondor|reflexion|retarus|safedns|safeweb|sec-provider|secureage|securence|security|sendio|shield|sicontact|sonicwall|sophos|spamtitan|spfbl|spiceworks|stopsign|supercleanmail|techtarget|titanhq|trellix|trendmicro|trustifi|trustwave|tryton|uni-muenster|usergate|vadesecure|wessexnetworks|zillya|zyxel'
dangerous_isps2 = r'abus|bad|black|bot|brukalai|excello|filter|honey|junk|lab|list|metunet|rbl|research|security|spam|trap|ubl|virtual|virus|vm\d'
dangerous_title = r'<title>[^<]*(security|spam|filter|antivirus)[^<]*<'

resolver_obj = dns.resolver.Resolver()
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
          ╙     {b}Validol - Email Validator v23.03.08{z}
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
	if os.name != 'nt':
		try:
			import resource
			resource.setrlimit(8, (2**14, 2**14))
			print(okk+'tuning rlimit_nofile:          '+', '.join([num(i) for i in resource.getrlimit(8)]))
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
	print(wl+okk+'ip2location.bin path:          '+ip2location_path)

def check_whitelist_exists():
	global domains_whitelist_url, domains_whitelist_path
	if not os.path.isfile(domains_whitelist_path):
		print(inf+f'downloading {b}domains whitelist{z} file. it will take some time...'+up)
		try:
			domains_whitelist_body = requests.get(domains_whitelist_url, timeout=5).text
			open(domains_whitelist_path, 'w').write(domains_whitelist_body)
		except Exception as e:
			exit(wl+err+'cannot download domains_whitelist.txt: '+red(e))
	print(wl+okk+'domains_whitelist.txt path:    '+domains_whitelist_path)

def fill_domains_whitelist(domains_whitelist_path):
	goods_cache = {}
	if os.path.isfile(domains_whitelist_path):
		for domain in open(domains_whitelist_path, 'r', encoding='utf-8-sig', errors='ignore').read().splitlines():
			goods_cache[domain] = 'precheck whitelist'
	return goods_cache

def first(a):
	return (a or [''])[0]

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def sec_to_min(i):
	return '%02d:%02d'%(int(i/60), i%60)

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
		return 'solution lifetime expired' in str(e) and (time.sleep(0.5) or get_ip_of_host(host))

def get_ptr(ip):
	global resolver_obj
	try:
		reverse_name = dns.reversename.from_address(ip)
		return str(resolver_obj.resolve(reverse_name, 'ptr')[0])[:-1]
	except Exception as e:
		return 'solution lifetime expired' in str(e) and (time.sleep(0.5) or get_ptr(ip))

def get_mx_server(domain):
	global resolver_obj
	try:
		return str(resolver_obj.resolve(domain, 'mx')[0].exchange)[:-1]
	except Exception as e:
		return 'solution lifetime expired' in str(e) and (time.sleep(0.5) or get_mx_server(domain))

def judge_email(email):
	global dangerous_users, dangerous_zones, dangerous_isps, dangerous_isps2, dangerous_title, bads_cache, database, whitelisted_mx, selected_email_providers
	user, host = email.split('@')
	if host in bads_cache:
		raise Exception(bads_cache[host])
	if re.search(dangerous_users, user.lower()):
		raise Exception('bad username: '+user)
	if re.search(dangerous_zones, host.lower()):
		raise Exception('bad zone: '+host)
	if selected_email_providers:
		for domain in selected_email_providers.split(','):
			if domain and domain in host:
				return host
	email_mx = get_mx_server(host)
	if not email_mx:
		raise Exception('no <mx> records found for: '+host)
	if selected_email_providers:
		for domain in selected_email_providers.split(','):
			if domain and domain in email_mx:
				return email_mx
		raise Exception(email_mx)
	if re.search(whitelisted_mx, email_mx):
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
		if re.findall(dangerous_title, page_body.lower()):
			raise Exception('[!] '+email_mx_top_host+': '+first(re.findall(r'<title>([^<]+)<', page_body.lower())))
	return email_mx

def is_safe_email(email):
	global goods_cache, bads_cache
	host = email.split('@')[-1]
	if not host in goods_cache:
		try:
			goods_cache[host] = judge_email(email)
		except Exception as e:
			if not 'bad username' in str(e):
				bads_cache[host] = str(e)
			raise Exception(str(e))
	return goods_cache[host]

def extract_email(line):
	return first(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', line))

def quit(signum, frame):
	print('\r\n'+okk+'exiting... see ya later. bye.')
	sys.exit(0)

def wc_count(filename, lines=0):
	file_handle = open(filename, 'rb')
	while buf:=file_handle.raw.read(1024*1024):
		lines += buf.count(b'\n')
	return lines

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
			clock = sec_to_min(time.time()-time_start).replace(':', (' ', z+':'+b)[int(time.time()*2)%2])
			status_bar = (
				f'{b}['+green('\u2665',int(time.time()*2)%2)+f'{b}]{z}'+
				f'[ {bold(clock)} \xb7 progress: {bold(num(progress))}/{bold(num(total_lines))} ({bold(round(progress/total_lines*100))}%) \xb7 speed: {bold(num(round(sum(speed)/10)))}lines/s ({bold(loop_time)}s/loop) ]'+
				f'[ cpu: {bold(cpu_usage)}% \xb7 mem: {bold(mem_usage)}% \xb7 net: {bold(bytes_to_mbit(net_usage*10))}Mbit/s ]'+
				f'[ threads: {bold(threads_counter)} \xb7 goods/bads: {green(num(goods),1)}/{red(num(bads),1)} ]'
			)
			thread_statuses = []
			while not results_que.empty():
				is_ok, line, msg = results_que.get()
				if is_ok:
					# thread_statuses.append(' '+line+': '+green(msg))
					safe_file_handle.write(line+'\n')
				else:
					thread_statuses.append(' '+line+': '+red(msg))
					dangerous_file_handle.write(line+'; '+msg+'\n')
			if len(thread_statuses):
				print(wl+'\n'.join(thread_statuses))
			print(wl+status_bar+up)
			time.sleep(0.08)

signal.signal(signal.SIGINT, quit)
show_banner()
tune_network()
check_database_exists()
check_whitelist_exists()
try:
	help_message = f'usage:\n    python3 {sys.argv[0]} '+bold('list_with_emails.txt')+' [selected,email,providers]'
	list_filename = sys.argv[1] if len(sys.argv)>1 and os.path.isfile(sys.argv[1]) else ''
	selected_email_providers = sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!='debug' else ''
	debugging = 'debug' in sys.argv
	if not list_filename:
		print(inf+help_message)
		while not os.path.isfile(list_filename):
			list_filename = input(npt+'path to file with emails: ')
		selected_email_providers = input(npt+'domains to left in list, comma separated (leave empty if all): ')
	suffixes = (r'_'+selected_email_providers, r'_not_'+selected_email_providers) if selected_email_providers else (r'_safe', r'_dangerous')
	safe_filename, dangerous_filename = (re.sub(r'\.([^.]+)$', s+r'.\1', list_filename) for s in suffixes)
except:
	print(err+help_message)

jobs_que = queue.Queue()
results_que = queue.Queue()
time_start = time.time()
bads = 0
goods = 0
progress = 0
goods_cache = {} if selected_email_providers else fill_domains_whitelist(domains_whitelist_path)
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
sys.stdout.reconfigure(encoding='utf-8')

print(inf+'source file:                   '+list_filename)
print(inf+'total lines to procceed:       '+num(total_lines))
print(inf+'desired email providers:       '+(selected_email_providers or 'all'))
print(inf+'safe emails file:              '+safe_filename)
print(inf+'dangerous emails file:         '+dangerous_filename)
input(npt+'press [ Enter ] to start...')

threading.Thread(target=every_second, daemon=True).start()
threading.Thread(target=printer, args=(jobs_que, results_que), daemon=True).start()

with open(list_filename, 'r', encoding='utf-8-sig', errors='ignore') as fp:
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
