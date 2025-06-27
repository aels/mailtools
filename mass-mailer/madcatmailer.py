#!/usr/local/bin/python3

import os, sys, threading, time, queue, random, re, signal, smtplib, ssl, socket, configparser, base64, string, datetime, uuid, colorama

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
from email.header import Header
from email import charset

try:
	import psutil, requests, dns.resolver
except ImportError:
	print('\033[1;33minstalling missing packages...\033[0m')
	os.system('apt -y install python3-pip; pip3 install psutil dnspython requests pyopenssl colorama')
	import psutil, requests, dns.resolver

if not sys.version_info[0] > 2 and not sys.version_info[1] > 8:
	exit('\033[0;31mpython 3.9 is required. try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

mailing_services = r'amazon|elastic|sendinblue|twilio|sendgrid|mailgun|netcore|pepipost|mailjet|mailchimp|mandrill|salesforce|constant|postmark|sharpspring|zepto|litmus|sparkpost|smtp2go|socketlabs|aritic|kingmailer|netcore|flowmailer|jangosmtp'
no_read_receipt_for = r'@(web\.de|gmx\.[a-z]{2,3}|gazeta\.pl|wp\.pl|op\.pl|interia\.pl|onet\.pl|spamtest\.glockdb\.com)$'
dummy_config_path = 'https://raw.githubusercontent.com/aels/mailtools/main/mass-mailer/dummy.config'
text_extensions = 'txt|html|htm|mhtml|mht|xhtml|svg'.split('|')
slow_send_mail_servers = 'gmail,googlemail,google,biglobe'

requests.packages.urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')
colorama.init(autoreset=True)
charset.add_charset('utf-8', charset.SHORTEST, charset.QP)

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
          ╙     {b}MadCat Mailer v25.06.27{z}
                Made by {b}Aels{z} for community: {b}https://xss.is{z} - forum of security professionals
                https://github.com/aels/mailtools
                https://t.me/IamLavander
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

def shuffle_arr(array):
	random.shuffle(array)
	return array

def tune_network():
	if os.name != 'nt':
		try:
			import resource
			resource.setrlimit(8, (2**20, 2**20))
			print(okk+'tuning rlimit_nofile:          '+', '.join([bold(num(i)) for i in resource.getrlimit(8)]))
			# if os.geteuid() == 0:
			# 	print('tuning network settings...')
			# 	os.system("echo 'net.core.rmem_default=65536\nnet.core.wmem_default=65536\nnet.core.rmem_max=8388608\nnet.core.wmem_max=8388608\nnet.ipv4.tcp_max_orphans=4096\nnet.ipv4.tcp_slow_start_after_idle=0\nnet.ipv4.tcp_synack_retries=3\nnet.ipv4.tcp_syn_retries =3\nnet.ipv4.tcp_window_scaling=1\nnet.ipv4.tcp_timestamp=1\nnet.ipv4.tcp_sack=0\nnet.ipv4.tcp_reordering=3\nnet.ipv4.tcp_fastopen=1\ntcp_max_syn_backlog=1500\ntcp_keepalive_probes=5\ntcp_keepalive_time=500\nnet.ipv4.tcp_tw_reuse=1\nnet.ipv4.tcp_tw_recycle=1\nnet.ipv4.ip_local_port_range=32768 65535\ntcp_fin_timeout=60' >> /etc/sysctl.conf")
			# else:
			# 	print('Better to run this script as root to allow better network performance')
		except Exception as e:
			print(wrn+'failed to set rlimit_nofile:   '+str(e))

def quit(signum, frame):
	print('\r\n'+wl+okk+'exiting... see ya later. bye.')
	time.sleep(1)
	sys.exit(0)

def now():
	return datetime.datetime.now().strftime('[ %Y-%m-%d %H:%M:%S ]')

def url_escape_str(string):
	return ''.join(['%'+format(ord(i), 'x') for i in string])

def html_encode_str(string):
	return ''.join(['&#'+format(ord(i), 'd') for i in string])

def get_rand_num(len):
	return ''.join(random.choice(string.digits) for i in range(len))

def get_rand_str(len):
	return ''.join(random.choice(string.ascii_lowercase+string.digits) for i in range(len))

def get_rand_ip():
	return '.'.join(str(random.randint(1, 255)) for i in range(4))

def any_of(string):
	return random.choice(string.split('|'))

def get_rand_color():
	return '#'+os.urandom(random.choice([3,4])).hex()

def rand_case(string):
	return string.upper() if random.choice([0,1]) and not re.findall(r'linear-gradient\(|rgb\(', string) else string.lower()

def get_zerofont_css():
	zf_css = f"display:inline-block;width:0{any_of('px|')};overflow:hidden;height:16px;white-space:nowrap".split(';')
	dummy_css = f"""color: {get_rand_color()}
		background: {get_rand_color()}
		text-align: {any_of('initial|revert|revert-layer|unset|inherit')}
		text-decoration: {any_of('none|inherit')}
		text-shadow: {any_of('none|inherit')}
		box-align: {any_of('unset|inherit')}
		box-shadow: {any_of('inset |')}{any_of('0px|0')} {any_of('0px|0')}{any_of('| '+get_rand_color())}
		font-weight: {any_of('normal|inherit')}
		font-display: {any_of('auto|block|swap|fallback|optional|inherit')}
		font: {any_of('caption|icon|menu|message-box|small-caption|status-bar')}
		font-smooth: {any_of('unset|inherit')}
		align-self: {any_of('start|inherit')}
		align-content: {any_of('start|inherit')}
		background-origin: {any_of('padding-box|inherit')}""".replace('\t', '').split('\n')
	return ';'.join([rand_case(style) for style in shuffle_arr(zf_css+shuffle_arr(dummy_css)[-4:])])

def get_zerofont_html(string):
	tag = any_of('span|div|sup')
	tag = rand_case(tag)
	return f'<{tag} style="{get_zerofont_css()}">{string}</{tag}>'

def shuffle_html_attributes(html):
	for html_attr_value in re.findall(r'<[A-Za-z]+ ([^>]+)>', html):
		attributes = re.findall(r'([A-Za-z]+="[^"]+")', html_attr_value)
		html = html.replace(html_attr_value, ' '.join(shuffle_arr(attributes)))
	return html

def shuffle_css_styles(html):
	for tag_style_value in re.findall(r'style="([^"]+)"', html):
		styles = tag_style_value.replace('&quot;', '"').split(';')
		styles = [rand_case(style).strip() for style in shuffle_arr(styles) if style!='']
		html = html.replace(tag_style_value, any_of(';|; ').join(styles).replace('"', '&quot;'))
	return html

def obfuscate_phone_number(number):
	allowed_chars = ['']*5 + list('     &---()./!	$_')
	if number[0]=='+':
		have_plus = True
		number = number[1:]
	else:
		have_plus = False
	number = re.sub(r'( )', lambda x: random.choice(allowed_chars), ' '.join(re.findall(r'\d', number)))
	number = ''.join([s if random.choice(range(4)) else url_escape_str(s) for s in number])
	return have_plus and '+'+number or number

def check_ipv4():
	try:
		socket.has_ipv4 = read('https://api.ipify.org')
	except:
		socket.has_ipv4 = red('error getting ip')

def check_ipv4_blacklists():
	print(inf+'checking ipv4 address in blacklists...'+up)
	try:
		mxtoolbox_url = f'https://mxtoolbox.com/api/v1/Lookup?command=blacklist&argument={socket.has_ipv4}&resultIndex=5&disableRhsbl=true&format=2'
		socket.ipv4_blacklist = requests.get(mxtoolbox_url, headers={'tempauthorization':'27eea1cd-e644-4b7b-bebe-38010f55dab3'}, timeout=15).text
		socket.ipv4_blacklist = re.findall(r'LISTED</td><td class=[^>]+><span class=[^>]+>([^<]+)</span>', socket.ipv4_blacklist)
		socket.ipv4_blacklist = red(', '.join(socket.ipv4_blacklist)) if socket.ipv4_blacklist else False
	except:
		socket.ipv4_blacklist = red('blacklist check error')

def check_ipv6():
	try:
		socket.has_ipv6 = read('https://api6.ipify.org')
	except:
		socket.has_ipv6 = False

def first(a):
	return (a or [''])[0]

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def sec_to_min(i):
	return '%02d:%02d'%(int(i/60), i%60)

def normalize_delimiters(s):
	return re.sub(r'[:,\t|]+', ';', re.sub(r'"+', '', s))

def read(path):
	return os.path.isfile(path) and open(path, 'r', encoding='utf-8-sig', errors='ignore').read() or re.search(r'^https?://', path) and requests.get(path, timeout=5).text or ''

def read_lines(path):
	return read(path).splitlines()

def read_bytes(path):
	return os.path.isfile(path) and open(path, 'rb').read() or ''

def rand_file_from_dir(path):
	path = re.sub(r'//', '/', path+'/')
	filenames = [file for file in os.listdir(path) if is_file_or_url(path+file)]
	return path+random.choice(filenames) if len(filenames) else ''

def is_file_or_url(path):
	return os.path.isfile(path) or re.search(r'^https?://', path)

def base64_encode(string):
	return base64.b64encode(str(string).encode('ascii')).decode('ascii')

def get_rand_ip_of_host(host):
	global resolver_obj
	try:
		ip_array = resolver_obj.resolve(host, socket.has_ipv6 and 'aaaa' or 'a')
	except:
		try:
			ip_array = resolver_obj.resolve(host, 'a')
		except:
			raise Exception('no a record found for '+host)
	return str(random.choice(ip_array))

def is_valid_email(mail):
	return re.match(r'^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$', mail)

def is_mail_of(mail, services):
	global resolver_obj
	try:
		mx_domain = str(resolver_obj.resolve(mail.split('@')[-1], 'mx')[0].exchange)[0:-1]
	except:
		return False
	for service in services.split(','):
		if service in mx_domain:
			return True
	return False

def extract_mail(line):
	return first(re.findall(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', line))

def expand_macros_once(text, subs):
	mail_str, smtp_user, mail_redirect_url, rand_Fname, rand_Lname = subs
	mail_to = extract_mail(mail_str)
	placeholders = 'email|email_b64|email_user|email_host|email_l2_domain|smtp_user|smtp_host|url|rand_Fname|rand_Lname|rand_fname|rand_lname'.split('|')
	replacements = [
		mail_to,
		base64_encode(mail_to),
		mail_to.split('@')[0].capitalize(),
		mail_to.split('@')[-1],
		mail_to.split('@')[-1].split('.')[0],
		smtp_user,
		smtp_user.split('@')[-1],
		mail_redirect_url,
		rand_Fname,
		rand_Lname,
		rand_Fname.lower(),
		rand_Lname.lower()
	]
	if not '\x00' in text:
		for i, column in enumerate(mail_str.split(';')):
			text = text.replace('{'+str(i+1)+'}', column)
		for i, placeholder in enumerate(placeholders):
			text = text.replace('{'+placeholder+'}', replacements[i])
		for file_path in [file_path for file_path in re.findall(r'(\{[^{}]+\})', text) if is_file_or_url(file_path[1:-1])]:
			text = text.replace(file_path, random.choice(read_lines(file_path[1:-1])).strip())
		text = re.sub(r'(\{d\})', lambda x: str(random.choice(range(0,9))), text)
		text = re.sub(r'(\{rand_str\})', lambda x: get_rand_str(16), text)
		text = re.sub(r'(\{rand_ip\})', lambda x: get_rand_ip(), text)
		text = re.sub(r'(\{zf_css\})', lambda x: get_zerofont_css(), text)
		for phone_num in re.findall(r'(\{tel:[^{}]+\})', text):
			text = text.replace(phone_num, 'tel:'+obfuscate_phone_number(phone_num[5:-1]))
		for b64_text in re.findall(r'(\{b64:[^{}]+\})', text):
			text = text.replace(b64_text, base64_encode(b64_text[5:-1]))
		for zf_splitter in re.findall(r'(\{zf:[^{}]+\})', text):
			text = text.replace(zf_splitter, get_zerofont_html(zf_splitter[4:-1]))
		for macro in re.findall(r'(\{[^{}]*\|[^{}]*\})', text):
			text = text.replace(macro, any_of(macro[1:-1]))
	return text

def expand_macros(text, subs):
	text = expand_macros_once(text, subs)
	text = expand_macros_once(text, subs)
	text = expand_macros_once(text, subs)
	return text

def get_read_receipt_headers(mail_from):
	receipt_headers = f'Disposition-Notification-To: {mail_from}\n'
	receipt_headers+= f'Generate-Delivery-Report: {mail_from}\n'
	receipt_headers+= f'Read-Receipt-To: {mail_from}\n'
	receipt_headers+= f'Return-Receipt-Requested: {mail_from}\n'
	receipt_headers+= f'Return-Receipt-To: {mail_from}\n'
	receipt_headers+= f'X-Confirm-reading-to: {mail_from}\n'
	return receipt_headers

def create_attachment(file_path, subs):
	global text_extensions
	if os.path.isdir(file_path):
		file_path = rand_file_from_dir(file_path)
	if is_file_or_url(file_path):
		attachment_filename = expand_macros(re.sub(r'=', '/', file_path).split('/')[-1], subs)
		attachment_ext = file_path.split('.')[-1]
		attachment_body = expand_macros(read(file_path), subs) if attachment_ext in text_extensions else read_bytes(file_path)
		attachment = MIMEApplication(attachment_body)
		attachment.add_header('content-disposition', 'attachment', filename=attachment_filename)
		return attachment
	else:
		return ''

def str_ljust(string, length):
	is_inside_tag = False
	shift = 0
	for i, s in enumerate(string):
		if i<length+shift:
			is_inside_tag |= s == '\033'
			shift += int(is_inside_tag)
			is_inside_tag &= s != 'm'
	if len(string)>length+shift:
		return re.sub(r'\033[^m]*$', '', string[0:length+shift-3])+'...'+z
	else:
		return string+' '*(length-len(re.sub(r'\033[^m]+m', '', string)))

def smtp_connect(smtp_server, port, user, password):
	global connection_timeout
	smtp_class = smtplib.SMTP_SSL if str(port) == '465' else smtplib.SMTP
	smtp_server_ip = get_rand_ip_of_host(smtp_server)
	ctx = ssl._create_unverified_context()
	server_obj = smtp_class(smtp_server_ip, port, local_hostname=smtp_server, timeout=connection_timeout)
	server_obj.ehlo()
	if server_obj.has_extn('starttls') and port != '465':
		server_obj.starttls(context=ctx)
		server_obj.ehlo()
	server_obj.login(user, password)
	return server_obj

def smtp_sendmail(server_obj, smtp_server, smtp_user, mail_str):
	global config, no_read_receipt_for, total_sent
	mail_redirect_url = random.choice(config['redirects_list'])
	subs = [mail_str, smtp_user, mail_redirect_url] + get_random_name()
	mail_to = extract_mail(mail_str)
	mail_from = expand_macros(config['mail_from'], subs)
	mail_reply_to = expand_macros(config['mail_reply_to'], subs)
	mail_subject = expand_macros(config['mail_subject'], subs)
	mail_body = expand_macros(read(config['mail_body']) or os.path.isdir(config['mail_body']) and read(rand_file_from_dir(config['mail_body'])) or config['mail_body'], subs)
	mail_body = shuffle_html_attributes(mail_body)
	mail_body = shuffle_css_styles(mail_body)
	smtp_from = extract_mail(smtp_user) or extract_mail(mail_from) or 'no-reply@localhost'
	smtp_host = smtp_from.split('@')[1]
	if is_mail_of(mail_to, 'outlook.com'):
		boundary = '==============='+get_rand_num(19)+'=='
	else:
		boundary = 'Apple-Mail=_'+str(uuid.uuid4()).upper()
	message = MIMEMultipart(boundary=boundary)
	message['To'] = mail_to
	message['From'] = smtp_from if is_valid_email(mail_from) else str(Header(mail_from.split(' <')[0],'utf-8'))+f' <{smtp_from}>'
	message['Subject'] = Header(mail_subject,'utf-8')
	message_html = MIMEText(mail_body, 'html', 'utf-8')	
	headers = ''
	headers+= 'Reply-To: '+mail_reply_to+'\n'
	headers+= 'Message-ID: <'+str(uuid.uuid4()).upper()+'@'+smtp_host+'>\n'
	headers+= 'Date: '+formatdate(localtime=True)+'\n'
	if is_mail_of(mail_to, 'outlook.com'):
		headers+= 'X-Priority: 1\n'
		headers+= 'X-MSmail-Priority: High\n'
		headers+= 'X-Mailer: Microsoft Office Outlook, Build 10.0.5610\n'
		headers+= 'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441\n'
	else:
		message_html.replace_header('MIME-Version', '1.0 (Mac OS X Mail 16.0 \\(3774.'+any_of('1|2|3|4|5|6')+'00.171.1.1\\))')
		headers+= 'X-Mailer: Apple Mail (2.3774.'+any_of('1|2|3|4|5|6')+'00.171.1.1)\n'
	# headers+= 'X-Source-IP: 127.0.0.1\n'
	# headers+= 'X-Sender-IP: 127.0.0.1\n'
	# headers+= 'List-Unsubscribe: <mailto:unsubscribe@'+smtp_host+'>\n'
	headers+= 'Precedence: first-class\n' # https://stackoverflow.com/a/6240126/1906976
	headers+= 'X-Anti-Abuse: Please report abuse to abuse@'+smtp_host+'\n'
	if config['add_read_receipts'] and not re.findall(no_read_receipt_for, mail_to.lower()):
		headers += get_read_receipt_headers(smtp_from)
	message.attach(message_html)
	for attachment_file_path in config['attachment_files']:
		attachment = create_attachment(attachment_file_path, subs)
		message.attach(attachment)
	message_raw = (headers + message.as_string()).replace('\r\n', '\n')
	server_obj.sendmail(smtp_from, mail_to, message_raw)

def get_testmail_str(smtp_str):
	global smtp_pool_tested, test_mail_str, config
	mails_to_verify = config['mails_to_verify'].split(',')
	mail_str = False
	if smtp_pool_tested[smtp_str]<len(mails_to_verify):
		mail_str = test_mail_str.replace(extract_mail(test_mail_str), mails_to_verify[smtp_pool_tested[smtp_str]])
		smtp_pool_tested[smtp_str] += 1
	return mail_str

def smtp_send_testmails():
	global smtp_pool_array, test_mail_str, smtp_errors_que, config
	test_mails_sent = False
	while not test_mails_sent:
		try:
			smtp_str = random.choice(smtp_pool_array)
		except:
			exit(wl+err+'sorry, no valid smtp servers left. bye.')
		smtp_server, port, smtp_user, password = smtp_str.split('|')
		try:
			server_obj = smtp_connect(smtp_server, port, smtp_user, password)
			while True:
				mail_str = get_testmail_str(smtp_str)
				if not mail_str:
					break
				smtp_sendmail(server_obj, smtp_server, smtp_user, mail_str)
				print(wl+okk+f'sent to: '+bold(mail_str)+', sleeping...')
				time.sleep(12)
			test_mails_sent = True
		except Exception as e:
			msg = '~\b[X] '+str(e).split('b\'')[-1].strip()
			smtp_errors_que.put((smtp_str, msg, 0))
			smtp_str in smtp_pool_array and smtp_pool_array.remove(smtp_str)
			print(wl+err+smtp_server+' ('+smtp_user+'): '+red(msg))
	return True

def test_inbox():
	print(wl+inf+f'sending test mails to '+bold(config['mails_to_verify'])+'...')
	smtp_send_testmails()
	print(wl+okk+f'test mails to '+bold(config['mails_to_verify'])+' sent.')

def worker_item(mail_que, results_que):
	global threads_counter, smtp_pool_array, loop_times, smtp_errors_que, slow_send_mail_servers_delay
	self = threading.current_thread()
	mail_str = False
	mails_sent = 0
	while True:
		if not len(smtp_pool_array) or mail_que.empty() and not mail_str:
			results_que.put((self.name, f'~\bdone with {green(mails_sent,0)} mails', mails_sent))
			break
		else:
			smtp_str = random.choice(smtp_pool_array)
			smtp_server, port, smtp_user, password = smtp_str.split('|')
			smtp_sent = 0
			current_server = f'{smtp_server} ({smtp_user}): '
			results_que.put((self.name, current_server+blue('~\b->- ',0)+smtp_str, mails_sent))
			try:
				server_obj = smtp_connect(smtp_server, port, smtp_user, password)
				server_born_time = time.perf_counter()
				last_slow_mail_time = time.perf_counter()
				while True:
					if mail_que.empty() and not mail_str:
						break
					try:
						time_start = time.perf_counter()
						mail_str = get_testmail_str(smtp_str) or mail_str or mail_que.get()
						mail_to = extract_mail(mail_str)
						if time.perf_counter() - server_born_time < 60*5:
							chill_time = 35
							msg = cyan('+\b'+'>'*(mails_sent%3)+b+'>',0)+cyan('>> '[mails_sent%3:],0)+'warming-up, slowly... sleeping '+bold('30s')
						elif time.perf_counter() - last_slow_mail_time < slow_send_mail_servers_delay:
							chill_time = slow_send_mail_servers_delay - time.perf_counter() + last_slow_mail_time
							msg = cyan('+\b'+'>'*(mails_sent%3)+b+'>',0)+cyan('>> '[mails_sent%3:],0)+'chilling for '+bold(chill_time)+'s between emails'
						else:
							chill_time = 0.3
							msg = cyan('+\b'+'>'*(mails_sent%3)+b+'>',0)+cyan('>> '[mails_sent%3:],0)+'chilling for 0.3s between emails'
						results_que.put((self.name, current_server+msg, mails_sent))
						time.sleep(chill_time)
						smtp_sendmail(server_obj, smtp_server, smtp_user, mail_str)
						smtp_sent += 1
						mails_sent += 1
						msg = green('+\b'+'>'*(mails_sent%3)+b+'>',0)+green('>> '[mails_sent%3:],0)+mail_str
						results_que.put((self.name, current_server+msg, mails_sent))
						mail_str = False
						last_slow_mail_time = time.perf_counter() if is_mail_of(mail_to, slow_send_mail_servers) else last_slow_mail_time
						loop_times += [time.perf_counter() - time_start]
						len(loop_times)>100 and loop_times.pop(0)
					except Exception as e:
						if re.search(r'suspicio|suspended|too many|limit|spam|blocked|unexpectedly closed|mailbox unavailable', str(e).lower()):
							raise Exception(e)
						msg = '~\b{!} '+str(e).split(' b\'')[-1].strip()
						results_que.put((self.name, current_server+orange(msg), mails_sent))
						smtp_errors_que.put((smtp_str, msg, smtp_sent))
						time.sleep(1)
						break
			except Exception as e:
				msg = '~\b[X] '+str(e).split(' b\'')[-1].strip()
				results_que.put((self.name, current_server+red(msg), mails_sent))
				smtp_errors_que.put((smtp_str, msg, smtp_sent))
				smtp_str in smtp_pool_array and smtp_pool_array.remove(smtp_str)
				time.sleep(1)
			time.sleep(0.04)
	threads_counter -= 1

def get_random_name():
	fnames = 'Dan|Visakan|Molly|Nicole|Nick|Michael|Joanna|Ed|Maxim|Nancy|Mika|Margaret|Melody|Jerry|Lindsey|Jared|Lindsay|Veronica|Marianne|Mohammed|Alex|Lisa|Laurie|Thomas|Mike|Lydia|Melissa|Ccsa|Monique|Morgan|Drew|Milan|Nemashanker|Benjamin|Mel|Norine|Deirdre|Millie|Tom|Maria|Mighty|Terri|Marsha|Mark|Stephen|Holly|Megan|Fonda|Melanie|Nada|Barry|Marilyn|Letitia|Mary|Larry|Mindi|Alexander|Mirela|Lhieren|Wilson|Nandan|Matthew|Nicolas|Michelle|Lauri|John|Amy|Danielle|Laly|Lance|Nance|Debangshu|Emily|Graham|Aditya|Edward|Jimmy|Anne|William|Michele|Laura|George|Marcus|Martin|Bhanu|Miles|Marla|Luis|Christa|Lina|Lynn|Alban|Tim|Chris|Fakrul|Angad|Nolan|Christine|Anil|Marigem|Matan|Louisa|Timothy|Mirza|Donna|Steve|Chandan|Bethany|Oscar|Marcie|Joanne|Jitendra|Lorri|Manish|Brad|Swati|Alan|Larissa|Lori|Lana|Amanda|Anthony|Luana|Javaun|Max|Luke|Malvika|Lee|Nic|Lynne|Nathalie|Natalie|Brooke|Masafumi|Marty|Meredith|Miranda|Liza|Tanner|Jeff|Ghazzalle|Anna|Odetta|Toni|Marc|Meghan|Matt|Fai|Martha|Marjorie|Christina|Martina|Askhat|Leo|Leslie|As|Mandy|Jenene|Marian|Tia|Murali|Heidi|Jody|Mamatha|Sudhir|Yan|Frank|Lauren|Steven|Jessica|Monica|Aneta|Leanne|David|Mallory|Ianne|Melaine|Leeann|Arvid|Marge|Greg|Melinda|Alison|Deborah|Nikhol|Charles|Doug|Nicholas|Alexandre|Nels|James|Yvette|Muruganathan|Mangesh|Cfre|Claudia|Austin|Mara|Linda|Dana|Stewart|Oleg|Nikhil|Emilio|Lenn|Emiliano|Lennart|Cortney|Cullen|Lena|Garima|Levent|Nelson|Xun|Jenn|Noah|Marshall|Nozlee|Lois|Lars|Alissa|Casimir|Fiona|Mehul|Brian|Marvin|Hiedi|Ashley|Luise|Vinay|Mithun|Denise|Orlando|Madison|Colin|Mina|Nichole|Norman|M|Jason|Nereida|Damon|Mohamed|Tomas|Len|Liliana|Marybeth|Dave|Cole|Jennifer|Lucas|Milton|Makhija|Marlon|Miki|Joan|Barbara|Nevins|Marta|Angelique|Muriel|Cornelia|Monty|Mouthu|Jayson|Louis|Janet|Moore|Nathan|Luanne|Dheeraj|Chelley|Vishal|Laree|Ado|Mona|Lorena|Marco|Jeremy|Joe|Andrew|Lloyd|Mahalaxmi|Niamh|Daniel|Mitzi|Les|Laurence|Levonte|Nuno|Mj|Derek|Susan|Deandre|Nizar|Tanya|Maritza|Gabe|Imtiaz|Nira|Ervin|Maureen|Lalit|Lynwood|Li|Christopher|Min|Liz|Diane|Michaeline|Craig|Marianna|Becky|Leonard|Aj|Jeffrey|Edison|Csm|Clay|Marie|Jae|Bruce|Marcello|Lucille|Megha|Todd|Elizabeth|Angelica|Minette|Lynda|Liton|Carrie|Dennis|Amit|May|B|Laurel|Istiaq|Valerio|Sujesh|Vincent|Charley|Benj|Jeanine|Marcin|Ali|Arnaud|Mirna|Dianne|Namita|Melvin|Geroge|Omar|Wesley|Dominic|Adrian|Tina|Eric|Graciano|Leon|Mario|Brandon|Isabel|Antonio|Liang|Lara|Nadezhda|Navjot|Vicki|Danette|Nikia|Sunil|Leighann|Dustin|Adekunle|Natalia|Taylor|Darryl|Danny|Lorenza|Manny|Dorothy|Maryanne|Tarun|Lou|Oliver|Jay|Carla|Atle|Geoff|Mathew|Brit|Casey|Martijn|Laquita|Aaron|Mahesh|Althea|Lorra|Nina|Tammy|Ellie|Calvin|Marcia|Tamir|Meital|Cheryl|Gordon|Mujie|Marylou|Nicki|Manoj|Mitch|Tania|Hector|Dallan|Carol|Adenton|Nadira|Chengxiang|Naomi|Nirav|Frances|Lorelei|Methila|Ilias|Madhusudan|Jim|Noel|Harsha|Mayra|Masano|Nellie|Mengli|Lalita|Margo|Olga|Chase|Vineet|Mae|Akash|Vandhana|Naren|Ian|Niall|Alicia|Nate|Ben|Bill|Meagan|Madelene|Neha|Louise|Marti|Maarten|Asim|Earlyn|Nobumasa|Maaike|Sylvain|Mack|Maggie|Lester|April|Trent|Leland|Maged|Loren|Lycia|Leandrew|Learcell|Terra|Clara|Lasse|Nadine|Lew|Marquita|Marina|Leah|Miche|Brett|Hao|Lex|Maurice|Natasha|Moni|Melodie|Libby|Elliott|Aprajit|Ning|Lanette|Ivy|Liautaud|Merla|Mihaela|Heather|Nicola|Adger|Alyssa|Marusca|Donald|Mashay|Ashlee|Destine|Victor|Narin|Mathias|Branden|Geoffrey|Manjunath|Alexis|Dahlia|Mayer|Taras|Monte|Igor|Harry|Yonas|Obed|Albert|Darrell|Maxime|Zoe|Leigh|Tal|Thoai|Curtis|Cindy|Evan|Gomathy|Tessa|Elaheh|Marinca|Abby|Veronika|Onetta|Nikki|Mohsen|Edwin|Margie|Mick|Bonnie|Trina|Marilia|Nora|Leonor|Eddie|Gail|Arjan|Lorna|Mengwei|Aray|Ann|Wolfgang|Barb|Mahir|Swapna|Lijuan|Dinesh|Mayur|Marit|Beat|Maricela|Erika|Muhammad|Avi|Nestor|Anchal|Avni|Amber|Jessy|Luz|Midhat|Anita|Nandini|Lola|Nathaniel|Cleo|Jean|Lynette|Mitchell|Lawrence|Liviu|Madelyn|Nabil|Mila|Carson|Marcy|Mohammad|Bobby|Theresa|Lei|Nazim|Laurens|Chetan|Magdalena|Charlotte|Ana|Nissanka|Neil|Glenn|Mari|Miguel|Devin|Courtney|Mora|Jocelyn'.split('|')
	lnames = 'Scearcy|Sachchi|Ohalloran|Smith|Karahalios|Puglisi|Cordero|Pinero|Turcan|Poor|Tanaka|Henderson|Baltzer|Ivy|Jones|Mertens|Oyer|Polin|Lee|Greene|Sanchez|St|Kazi|Glowik|Mccann|Hogberg|Hutchinson|Morse|Hardy|Luke|Kincaid|Ceh|Guerrero|Roe|Vanderwert|Area|Singh|Ho|Koehler|Ask|Oakes|Vega|Sternfeldt|Huddleston|Massa|Interactive|Ruzsbatzky|Miller|Neeley|Posnock|Marando|Bright|Moyers|Walsh|Cataldi|Herbst|Lange|Shepherd|Nelson|Doherty|Willms|Lane|Romashkov|Trudeau|Bancu|Fraga|Wei|Kulkarni|Linkewich|Rouquette|Messer|Naypaue|Giafaglione|Bunting|Ahlersmeyer|Deschene|Viggers|Vadassery|Alves|Wilson|Trueworthy|Mukherjee|Sharp|Thomas|Prabhakar|Moore|Horikawa|Horne|Brostek|Richardson|Lewis|Alberti|Kelso|Mashita|Forsling|Dong|Diaz|Gibbs|Chitturi|Trackwell|Jeanne|Napoleon|Mclau|Craigie|Dacosta|Johnson|Farr|Martinez|Rauscher|Barclay|Webber|Delortlaval|Lin|Rinenbach|Weyand|Syed|Brady|Pathak|Fairchild|Ta|Higgins|Zhang|Kensey|Puthin|Malundas|Marom|Labed|Smagala|Zelenak|Capecelatro|Hambley|Causevic|Simmet|Schneider|Poovaiah|Enge|Maddatu|Wheeler|Henken|Fett|Goldston|Solanki|Arnce|Tamayo|Visa|Labruyere|French|Bennett|Shah|Osborne|Curley|Vaidya|Valachovic|Witters|Terrill|Thompson|Fryer|Price|Fulgieri|Queen|Moradi|Bell|Kort|Gillfoyle|Wosje|Aswal|Chelap|Wie|M.;4831600947|Niziolek|Whitley|Huntington|Drew|Santana|Basch|Simond|Bakke|Massi|Usuda|Mcquade|Rodgers|Kerpovich|Williams|Marciano|Ludeman|Strange|Spano|Hahn|Elgin|Mirkooshesh|Angottiportell|Deet|Pumphrey|Sandler|Vogel|Flynn|De|Wagner|Cheung|Dalberth|Skoog|Benavides|Ginsberg|Woodworth|Roachell|Monfeli|Sadow|Mejean|Song|Smurzynski|Mckee|Hunter|Gabdulov|Arnaboldi|Saxton|Worthy|Asd|Kee|Thigpen|Ormand|Schwartz|Sandberg|Pitner|Achutharaman|Seyot|Mientka|Hougom|Speer|Pearce|Hernandez|Long|Earley|Fulton|Chiavetta|Mcbrayer|Chamarthi|Barag|Kumar|Yang|Casari|Slicer|Lang|Bourgeois|Perry|Spivack|Taylor|Hughes|Seric|Barth|Hayter|Westerdale|Cook|Rico|Fasthoff|Trainor|Kleinman|Harverstick|Greenwell|Grady|Kirkpatrick|Saxon|Ujvari|Glander|Robinson|Goddard|Chen|Kramer|Caracache|Ramer|Baudet|Casner|Jenson|Butz|Hooper|Ramanathan|Marks|Dhawale|Ferguson|Huapaya|Mcdowell|Haehn|Piccolo|Carns|Jeffrey|Gibitz|Hsu|Jindra|Isaev|Gaikwad|Manganaro|Gerbelli|Sisson|Santiago|Izzo|Mills|Wiseen|Cooney|Libby|Miles|Mcgough|Fox|Koch|Rochelle|Mehta|Riffee|Erkok|Gibby|Freitas|Remund|Arones|Penn|Liu|Farkas|Kelkenberg|Samadzadeh|Castillo|Garrett|Cooper|Djuvik|Fishbane|Niedzielski|Kan|Hammond|Kruse|Rees|Leone|Vanbemmel|Ramani|Macdonald|Hall|Kiragu|Folkert|Tremaine|Zachry|Sherpard|Gearo|Richard|Voy|Weinem|Bhatia|Marder|Whittam|Garcia|Brannen|Mcindoe|Nandi|Mcgowen|Orr|Tamsitt|Kingsford|Lillie|Sheehan|Mylexsup|Davis|Yanez|Neal|Spinks|Massimo|Taulbee|Yunus|Maxian|Giuliano|Jorgenson|Sullivan|Obrien|Garcis|Allen|Kowalske|Wirtzberger|Kaiser|Millen|Mclaughlin|Sinclair|Messina|Lins|Robertson|Kindle|Velez|Vin|Argueta|Seltzer|Hayes|Clark|Slocum|Laski|Jim|Fey|Weston|Licata|Hanson|Mohlenkamp|Kos|Bilotti|Popke|Sloss|Campbell|Pham|Eby|Tipps|Walker|Hertzman|Harrell|Jansen|Kumarasamy|Lopez|Lindsley|Silver|Seremeth|Gorelick|Snider|Cauley|Ann|Garmatz|Ashcraft|Pawar|Kain|Coronel|Wilkes|Hinkle|Lloyd|Hassan|Ghangale|Kurtz|Trakic|Gibson|Shaheen|Calkins|Kuhlmann|Nishihara|Skrbin|Vanora|Fitzgerald|Trifler|Arriola|Krishnamurthy|Leleux|Weum|Dunne|Bairstow|Choi|Boyce|Joe|Ploshay|Tibbits|Minkley|Coshurt|Santos|Odonnell|Rios|Burkart|Turner|Parker|Racki|Paliferro|Wcislo|Donchatz|Ford|Ladak|Emmick|Mobed|Quiles|Gagne|Medrano|Hussain|Tejada|Alterson|Anastasia|Eddie|Adams|Motto|Brooks|Sharma|Byrum|Cheng|Kagan|Helman|Kim|Roller|Bordelon|Dozal|Mitchell|Barnes|Hummel|Fenton|Anderson|Reinbold|Dillard|Mattingly|Shcherbina|Mintz|Tullos|Siuda|Maggi|Lucas|Bouchard|Cortes|Dunning|Howard|Gower|Cotter|Kisner|Kennedy|Palacios|Levy|Uppal|Oholendt|Jew|Schultz|Dabrock|Peel|Cls|Deady|Park|Corradini|Sisneros|Hartnett|Nazaredth|Gentile|Hester|Richcreek|Giermak|Kay|Shadle|Pott|Kubey|Chacana|Rangel|York|Cooke|Squire|Roush|Tillman|Kandel|Roy|Sun|Herrmann|Chong|Knudsen|Coomer|Sarkar|Woodward|Banks|Allan|Schiller|Nicholls|Mahmud|Fiala|Horvath|Dangelo|Vickery|Somanathan|Sellier|Alejos|Ellis|Roska|Thibeault|Fuller|Brown|Roach|Bulgajewski|Oztekin|Sabol|Nomellini|Magnier|Berglund|Schau|Gramling|Francisco|Korman|Shubhy|Gossmeyer|Murray|Foster|Blevins|Arias|Soda|Litwin|Solak|Casey|Schmidt|Hartshorn|Deck|Leodoro|Swenson|Luc|Zamudio|Lacoe|Simko|Metz|Pace|Benjamin|Tolwinska|Little|Mcdonough|Lynch|Worley|Funk|Bachtle|Estes|Hennessey|Wurtzel|Jimenez|Pilogallo|Donaldson|Eng|Weiss|Coy|Bockstahler|Nekrasova|Rand|Gagen|Masters|Root|Eldert|Bleiler|Huang|Ryan|Janca|Cozart|Bhatara|Todd|Haylett|Mckinney|Adeniran|Oneill|Zamparini|Lafauce|Hetzel|Boers|Elder|Glaser|Kienzler|Reverendo|Cruse|Salafia|Bossard|Muir|Khanna|Orsatti|Mantheiy|Moorehead|Trevino|Delorme|Gregory|Gratwick|Mooney|Reitan|L|Flachaire|Simpson|Edwards|Humes|Probst|Wood|La|Hardesty|Rogers|Batten|Peifer|Devolt|Tesnovets|Hitchcock|Scarlata|Khot|Bush|Navale|Volper|Schnell|Emmons|Newton|Adkins|Roberts|Romaine|Barker|Louie|Richmond|Stear|Derr|Hallinger|See|Heller|Raveenthran|Bridges|Robison|Caney|Thaves|Darab|Corridore|Haas|Medved|Hain|Chiu|Chalmer|Sirotnak|Lavecchia|Buoniconti|Karpe|Poell|Massicot|Bauer|Augusty|Cfp|Guzman|Zuleta|Dijohnson|Whatley|Zickur|Denton|Mety|Dhani|Ren|Rivas|Chartier|Botuck|Mistry|Rigney|Hough|Rahman|Panagiotou|Bookbinder|Mcnabb|Reddy|Desma|Giampicclo|Granata|Shekleton|Shivaram|Marzan|Abramson|Mack|Hribar|Wolman|Machado|Weispfenning|Adcock|Sugiyama|Manning|Mcclure|Salinas|Yuan|Langer|Metcalf|Cherian|Baamonde|Lolam|Bealhen|Trout|Titkova|Gariti|Lamb|Myhrvold|Peltekian|Londergan|Zdroik|Filkins|Nichols|Dieter|Chaturvedi|Kotsikopoulos|Saqcena|Naranjo|Atkinson|Woodley|Kushner|Thorson|Ropple|Phoenix|Jaganathan|Gomar|Denham|Drelich|Livermore|Burns|Cartwright|Wickum|Kluger|Hockenhull|Heindl|Zak|Shipman|Saple|Besmond|Malone|Caldwell|King|Balfe|Tilton|Van|Iqbal|Shuffler|Berry|Panetta|Mori|Meijer|Mckeever|Grande|Stinson|Swanson|Wong|Gavilondo|Jaffe|Innes|Junker|Strickler|Fouad|Phillips|Stevens|Lemmon|Reinholz|Rogan|Krongold|Gremillon|Phipps|Loyd|Atkins|Downing|Parsons|Stanovich|Folger|Savio|Holmes|Osgood|Harris|Soloski|Galvin|Low|Jamt|Baldwin|Doohen|Dustman|Clopton|Zamora|Austin|Delery|Hansen|Samson|Buddin|Hollander|Xiong|Maultsby|Madore|Fortuna|Heckman|Cooey|Heise|Matsuda|Bent|Kar|Gahan|Wang|Yip|Butts|Lincoln|Dorminy|Golojuch|Florestal|Escarment|Aye|Sheldon|Petrova|Haines|Beaudoin|Watkins|Knuth|Balena|Shay|Bogush|Thomann|Blackwell|Carr|Pochiraju|Rauch|Waldeisen|Harding|Lacroix|Kolber|Horenstein|Hoegerman|Ilfeld|Wnorowski|Jacobs|Burnette|Gatto|Wandell|Anerella|Melara|Deisner|Merchant|Mount|Borchardt|Tschupp|Ciotola|Leung|Frailey|Lemons|Clement|Wattanavirun|Schmidheiny|Harness|Schechter|Gebert|Peralta|Stanley|Sandoval|Rangaswamy|Ranallo|Chrostowski|Wallach|Graham|Goltermann|Crosby|Boschman|Pelta|Szmagala|Fry|Konforti|Garduno|Dolan|Rockwell|Mcgah|Damm|Gebrewold|Benito|Chang|Yeboah|Coleman|Steib|London|Ashby|Schulman|Ferrara|Griffith|Sadrieh|Anetakis|Serrano|Konidaris|Kastenson|Barel|Le|Molina|Peterson|Leddy|Espinal|Cohn|Swamy|Chermiset|Link|Hobson|Pentzke|Shirneshan|Veno|Peters|Warren|Stanfield|Magnus|Grantham|Szabo|Hou|Juncherbenzon|Lara|Marlatt|Millbrooke|Sofastaii|Downer|Matheis|Galati|Olson|Wiederrecht|Quintana|Drozd|Weaver|Russell|Fisher|Dorrian|Morris|Ortiz|Newnam|Piper|Modic|Pfister|Butler|Tschetter|Tibbetts|Mattox|Frank|Curry|Zayas|Alvarez|Arrington|Hanlon|Freedman|Lineberry|Robyn|Morakinyo|Stokkel|Rinear|Zheng|Cutting|Driggers|Adil|Nikumbhe|Farver|George|Gyurko|Riley|Greve|Dreyer|Petschl|Hodzic|Rawe|Vijayakumar|Kang|Drees|Calderone|Alvarado|Watson|Belcher|Chaudhari|Panchal|Carnevale|Ayers|Studinger|D|Latib|Haksar|Oles|Dowland|Borreli|Serravalle|Vincent|Sachdeva|Wallace|Jain|Segal|Aguirre|Salihovic|Antonio|Viau|Marek|Murphy|Barratt|Fischer|Lennon|Mike|Ramaswamy|Defruscio|Hamby|Pallant|Clifton|Chenevert|Stuebe|Bloss|Rowe|Speak|Cupido|Debartolomeis|Katz|Brophy|Myster|Frazier|Olaru|Rojas|Straub|Keenan|Phan|Agresta|Mansour|Fiore|Pucci|Levin|Abrams|Cox|Lockwood|Vangilder|Olshan|Tyus|Murry|Crites|Leonard'.split('|')
	return [random.choice(fnames), random.choice(lnames)]

def load_config():
	global config, smtp_pool_array, threads_count
	head_name = 'madcatmailer'
	temp_config = configparser.ConfigParser({
		'smtps_list_file': '',
		'mails_list_file': '',
		'mails_to_verify': '',
		'mail_from': '',
		'mail_reply_to': '',
		'mail_subject': '',
		'mail_body': '',
		'attachment_files': '',
		'redirects_file': '',
		'add_read_receipts': '',
	})
	if len(sys.argv) == 2:
		config['config_file'] = sys.argv[1] if is_file_or_url(sys.argv[1]) else exit(err+'wrong config path or filename: it must be like '+bold('<...>.config'))
	else:
		try:
			config['config_file'] = max([i for i in os.listdir() if re.search(r'.+\.config$', i)], key=os.path.getctime)
		except:
			open('dummy.config','w').write(read(dummy_config_path))
			print(wrn+'nor '+bold('.config')+' files found in current directory, nor provided as a parameter')
			exit( wrn+'sample '+bold('dummy.config')+' file downloaded to the current directory. please check and edit it before next run')
	temp_config.read_file(open(config['config_file'], 'r', encoding='utf-8'))
	if not temp_config.has_section(head_name):
		exit(err+'malformed config file')
	for key, value in temp_config.items(head_name):
		config[key] = value
	if not is_file_or_url(config['smtps_list_file']):
		exit(err+'cannot open smtps list file, provided in '+bold(config['config_file'])+'. does it exist?')
	else:
		config['smtps_errors_file'] = re.sub(r'\.([^.]+)$', r'_error_log.\1', config['smtps_list_file'])
		smtp_pool_array = read_lines(config['smtps_list_file'])
		for smtp_line in smtp_pool_array:
			smtp_pool_tested[smtp_line] = 0
			not re.findall(r'^[\w.+-]+\|\d+\|[@\w.+-]+\|[^|]+$', smtp_line) and exit(err+'"'+smtp_line+'" is not like "host|port|username|password"')
	if len(smtp_pool_array)*5<threads_count:
		threads_count = len(smtp_pool_array)*5
	if not is_file_or_url(config['mails_list_file']):
		exit(err+'cannot open mails list file. does it exist?')
	if len([is_valid_email(mail) for mail in config['mails_to_verify'].split(',')])<config['mails_to_verify'].count(',')+1:
		exit(err+'not all test emails looks valid. check them, please')
	config['mail_from'] or exit(err+'please fulfill '+bold('mail_from')+' parameter with desired name and email')
	config['mail_reply_to'] = config['mail_reply_to'] or config['mail_from']
	config['mail_subject'] or exit(err+'please fulfill '+bold('mail_subject')+' parameter with desired email subject')
	config['mail_body'] or exit(err+'please put the path to email body file(s) or mail body itself as a string into '+bold('mail_body')+' parameter')
	config['attachment_files'] = config['attachment_files'].split(',') if config['attachment_files'] else []
	for file_path in config['attachment_files']:
		if not is_file_or_url(file_path) and not (os.path.isdir(file_path) and rand_file_from_dir(file_path)):
			exit(err+file_path+' file not found or directory is empty')
	if config['redirects_file'] and not is_file_or_url(config['redirects_file']):
		exit(err+'please put the path to the file with redirects into '+bold('redirects_file')+' parameter')
	else:
		config['redirects_list'] = read_lines(config['redirects_file']) if config['redirects_file'] else ['']

def fill_mail_queue():
	global mail_que, total_mails_to_sent, config
	for i in read_lines(config['mails_list_file']):
		i = normalize_delimiters(i)
		if extract_mail(i):
			mail_que.put(i)
	if not mail_que.qsize():
		exit(err+'not enough emails. empty file?')
	total_mails_to_sent = mail_que.qsize()

def setup_logs_writer():
	threading.Thread(target=logs_writer, daemon=True).start()

def setup_threads():
	global threads_count, threads_counter, threads_statuses, mail_que, results_que
	sys.stdout.write('\n'*threads_count)
	threading.Thread(target=every_second, daemon=True).start()
	threading.Thread(target=printer, daemon=True).start()
	for i in range(threads_count):
		threading.Thread(name='th'+str(i), target=worker_item, args=(mail_que, results_que), daemon=True).start()
		threads_counter += 1
		threads_statuses['th'+str(i)] = 'no data'

def every_second():
	global total_sent, speed, mem_usage, cpu_usage, net_usage, loop_times, loop_time, no_jobs_left
	total_sent_old = total_sent
	net_usage_old = 0
	time.sleep(1)
	while True:
		try:
			speed.append(total_sent - total_sent_old)
			speed.pop(0) if len(speed)>10 else 0
			total_sent_old = total_sent
			mem_usage = round(psutil.virtual_memory()[2])
			cpu_usage = round(sum(psutil.cpu_percent(percpu=True))/os.cpu_count())
			net_usage = psutil.net_io_counters().bytes_sent - net_usage_old
			net_usage_old += net_usage
			loop_time = round(sum(loop_times)/len(loop_times), 2) if len(loop_times) else 0
		except:
			pass
		time.sleep(0.1)

def logs_writer():
	global config, smtp_errors_que
	with open(config['smtps_errors_file'], 'a') as smtps_errors_file_handle:
		while True:
			while not smtp_errors_que.empty():
				smtp_str, msg, smtp_sent = smtp_errors_que.get()
				smtps_errors_file_handle.write(now()+' '+smtp_str+' ('+str(smtp_sent)+' emails): '+msg.split('\b')[-1]+'\n')
				smtps_errors_file_handle.flush()
			time.sleep(0.05)

def printer():
	global total_sent, skipped, total_mails_to_sent, speed, loop_time, cpu_usage, mem_usage, net_usage, threads_count, threads_statuses, smtp_pool_array, time_start, got_updates
	while True:
		clock = sec_to_min(time.time()-time_start).replace(':', (' ', z+':'+b)[int(time.time()*2)%2])
		status_bar = (
			f'{b}['+green('\u2665',int(time.time()*2)%2)+f'{b}]{z}'+
			f'[ {bold(clock)} \xb7 sent/skipped: {bold(num(total_sent))}/{bold(num(skipped))} of {bold(num(total_mails_to_sent))} ({bold(round((total_sent+skipped)/total_mails_to_sent*100))}%) ]'+
			f'[ {bold(num(sum(speed)))} mail/s ({bold(loop_time)}s/loop) ]'+
			f'[ cpu: {bold(cpu_usage)}% \xb7 mem: {bold(mem_usage)}% \xb7 net: {bold(bytes_to_mbit(net_usage*10))}Mbit/s ]'+
			f'[ {bold(num(len(smtp_pool_array)))} smtps left ]'
		)
		if got_updates:
			sys.stdout.write(up*threads_count)
			for name, status in threads_statuses.items():
				print(wl+status)
			got_updates = False
		print(wl+status_bar+up)
		time.sleep(0.05)

signal.signal(signal.SIGINT, quit)

config = {}
threads_counter = 0
total_mails_to_sent = 0
time_start = time.time()
mail_que = queue.Queue()
results_que = queue.Queue()
smtp_errors_que = queue.Queue()
smtp_pool_array = []
smtp_pool_tested = {}
threads_statuses = {}
test_mail_str = ''
threads_count = 40
connection_timeout = 5
slow_send_mail_servers_delay = 6
total_sent = 0
skipped = 0
speed = []
mem_usage = 0
cpu_usage = 0
net_usage = 0
loop_times = []
loop_time = 0
got_updates = False

window_width = os.get_terminal_size().columns-40
resolver_obj = dns.resolver.Resolver()
resolver_obj.nameservers = ['8.8.8.8', '1.1.1.1']

show_banner()
tune_network()
check_ipv4()
check_ipv4_blacklists()
check_ipv6()
load_config()
fill_mail_queue()
setup_logs_writer()

print(inf+'ipv4 address:                  '+bold(socket.has_ipv4 or '-')+' ('+(socket.ipv4_blacklist or green('clean'))+')')
print(inf+'ipv6 address:                  '+bold(socket.has_ipv6 or '-'))
print(okk+'loading config:                '+bold(config['config_file']))
print(inf+'smtp servers file:             '+bold(config['smtps_list_file']+' ('+num(len(smtp_pool_array))+')'))
print(inf+'smtp errors log:               '+bold(config['smtps_errors_file']))
print(inf+'emails list file:              '+bold(config['mails_list_file']+' ('+num(total_mails_to_sent)+')'))
print(inf+'verification emails:           '+bold(config['mails_to_verify']))
print(inf+'mail body:                     '+bold(config['mail_body']))
print(inf+'attachments:                   '+bold(config['attachment_files'] or '-'))
print(inf+'file with redirects:           '+bold(config['redirects_file'] or '-'))

test_inbox()

input(npt+'press '+bold('[ Enter ]')+' to start...')

setup_threads()

while True:
	time_takes = round(time.time()-time_start, 1)+0.09
	while not results_que.empty():
		thread_name, thread_status, mails_sent = results_que.get()
		total_sent += 1 if '+\b' in thread_status else 0
		skipped += 1 if '-\b' in thread_status else 0
		mails_per_second = round(mails_sent/time_takes, 1)
		threads_statuses[thread_name] = f'{thread_name}: '.rjust(7)+str_ljust(thread_status, window_width)+f'{mails_sent} sent ({mails_per_second} mail/s)'.rjust(23)
		got_updates = True
	if threads_counter == 0:
		if mail_que.empty():
			mails_per_second = round(total_mails_to_sent/time_takes, 1)
			time.sleep(1)
			exit('\n'+wl+okk+f'all done in {bold(sec_to_min(time_takes))} minutes. speed: {bold(mails_per_second)} mail/sec.')
		if not len(smtp_pool_array):
			time.sleep(1)
			exit('\n'+wl+err+f'smtp list exhausted. all tasks terminated.\a')
	time.sleep(0.05)
