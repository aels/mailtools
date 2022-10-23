#!/usr/local/bin/python3

import os, sys, threading, time, queue, random, re, signal, smtplib, ssl, socket, configparser, resource

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

try:
	import psutil, requests, dns.resolver
except ImportError:
	print('\033[1;33minstalling missing packages...\033[0m')
	os.system(sys.executable+' -m pip install psutil dnspython requests pyopenssl')
	import psutil, requests, dns.resolver

if sys.version_info[0] < 3:
	exit('\033[0;31mpython 3 is required. try to run this script with \033[1mpython3\033[0;31m instead of \033[1mpython\033[0m')

if sys.stdout.encoding is None:
	exit('\033[0;31mplease set python env PYTHONIOENCODING=UTF-8, example: \033[1mexport PYTHONIOENCODING=UTF-8\033[0m')

# needed for faster and stable dns resolutions
custom_dns_nameservers = ['8.8.8.8', '8.8.4.4', '9.9.9.9', '149.112.112.112', '1.1.1.1', '1.0.0.1', '76.76.19.19', '2001:4860:4860::8888', '2001:4860:4860::8844']
# dangerous mx domains, skipping them all
dangerous_domains = r'localhost|invalid|mx37\.m..p\.com|mailinator|mxcomet|mxstorm|proofpoint|perimeterwatch|securence|techtarget|cisco|spiceworks|gartner|fortinet|retarus|checkpoint|fireeye|mimecast|forcepoint|trendmicro|acronis|sophos|sonicwall|cloudflare|trellix|barracuda|security|clearswift|trustwave|broadcom|helpsystems|zyxel|mdaemon|mailchannels|cyren|opswat|duocircle|uni-muenster|proxmox|censornet|guard|indevis|n-able|plesk|spamtitan|avanan|ironscales|mimecast|trustifi|shield|barracuda|essentials|libraesva|fucking-shit|please|kill-me-please|virus|bot|trap|honey|lab|virtual|vm\d|research|abus|security|filter|junk|rbl|ubl|spam|black|list|bad|brukalai|metunet|excello'

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
          ╙     {b}MadCat Mailer v22.10.23{z}
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
	global error_log, config
	print('\r\n'+wl+okk+'exiting... see ya later. bye.')
	if config['debug']:
		print(inf+'last 200 errors:')
		print('\n'.join(error_log))
	sys.exit(0)

def first(a):
	return (a or [''])[0]

def bytes_to_mbit(b):
	return round(b/1024./1024.*8, 2)

def sec_to_min(i):
	return '%02d:%02d'%(int(i/60), i%60)

def normalize_delimiters(s):
	return re.sub(r'[:,\t| \']+', ';', re.sub(r'"+', '', s))

def read(path):
	return os.path.isfile(path) and open(path, 'r', encoding='utf-8', errors='ignore').read() or re.search(r'^https?://', path) and requests.get(path, timeout=5).text or ''

def read_lines(path):
	return read(path).splitlines()

def is_file_or_url(path):
	return os.path.isfile(path) or re.search(r'^https?://', path)

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

def is_valid_email(email):
	return re.match(r'^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$', email)

def is_dangerous_email(email):
	global resolver_obj, dangerous_domains
	try:
		mx_domain = str(resolver_obj.resolve(email.split('@')[1], 'mx')[0].exchange)[0:-1]
		return mx_domain if re.search(dangerous_domains, mx_domain) and not re.search(r'\.outlook\.com$', mx_domain) else False
	except:
		return 'no mx records found'

def extract_email(line):
	return first(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', line))

def expand_macros(text, subs):
	mail_str, smtp_user, mail_redirect_url = subs
	mail_to = extract_email(mail_str)
	placeholders = 'email|email_user|email_host|email_l2_domain|smtp_user|smtp_host|url|random_name'.split('|')
	replacements = [
		mail_to,
		mail_to.split('@')[0].capitalize(),
		mail_to.split('@')[-1],
		mail_to.split('@')[-1].split('.')[0],
		smtp_user,
		smtp_user.split('@')[-1],
		mail_redirect_url,
		get_random_name()
	]
	for i, column in enumerate(mail_str.split(';')):
		text = text.replace('{{'+str(i+1)+'}}', column)
	for i, placeholder in enumerate(placeholders):
		text = text.replace('{{'+placeholder+'}}', replacements[i])
	macros = re.findall(r'(\{\{.*?\}\})', text)
	for macro in macros:
		text = text.replace(macro, random.choice(macro[2:-2].split('|')))
	return text

def get_read_receipt_headers(to):
	receipt_headers =f'Disposition-Notification-To: {to}\n'
	receipt_headers+=f'Generate-Delivery-Report: {to}\n'
	receipt_headers+=f'Read-Receipt-To: {to}\n'
	receipt_headers+=f'Return-Receipt-Requested: {to}\n'
	receipt_headers+=f'Return-Receipt-To: {to}\n'
	receipt_headers+=f'X-Confirm-reading-to: {to}\n'
	return receipt_headers

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

def smtp_sendmail(server_obj, smtp_user, mail_str):
	global config
	mail_redirect_url = random.choice(config['redirects_list'])
	subs = [mail_str, smtp_user, mail_redirect_url]
	mail_to = extract_email(mail_str)
	mail_from = expand_macros(config['mail_from'], subs)
	mail_subject = expand_macros(config['mail_subject'], subs)
	mail_body = expand_macros(read(config['mail_body']) if is_file_or_url(config['mail_body']) else config['mail_body'], subs)
	message = MIMEMultipart()
	message['To'] = mail_to
	message['From'] = mail_from
	message['Subject'] = mail_subject
	message.attach(MIMEText(mail_body, 'html', 'utf-8'))
	for attachment_filename, attachment_body in config['attachment_files_data'].items():
		attachment_body = expand_macros(attachment_body, subs)
		attachment = MIMEApplication(attachment_body)
		attachment.add_header('content-disposition', 'attachment', filename=attachment_filename)
		message.attach(attachment)
	headers = 'Return-Path: '+mail_from+'\n'
	headers+= 'Reply-To: '+mail_from+'\n'
	headers+= 'X-Priority: 1\n'
	headers+= 'X-MSmail-Priority: High\n'
	headers+= 'X-Source-IP: 127.0.0.1\n'
	headers+= 'X-Sender-IP: 127.0.0.1\n'
	headers+= 'X-Mailer: Microsoft Office Outlook, Build 10.0.5610\n'
	headers+= 'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441\n'
	headers+= 'Received: '+get_random_name()+'\n'
	headers+= get_read_receipt_headers(mail_from)
	message_raw = headers + message.as_string()
	server_obj.sendmail(smtp_user, mail_to, message_raw)

def worker_item(mail_que, results_que):
	global threads_counter, smtp_pool_array, loop_times
	self = threading.current_thread()
	mail_str = False
	mails_sent = 0
	while True:
		if not len(smtp_pool_array) or mail_que.empty() and not mail_str:
			results_que.put((self.name, f'~\bdone with {green(mails_sent,0)} mails', mails_sent))
			break
		else:
			time_start = time.perf_counter()
			smtp_str = random.choice(smtp_pool_array)
			smtp_server, port, smtp_user, password = smtp_str.split('|')
			current_server = f'{smtp_server} ({smtp_user}): '
			results_que.put((self.name, current_server+blue('~\b->- ',0)+smtp_str, mails_sent))
			try:
				server_obj = smtp_connect(smtp_server, port, smtp_user, password)
				while True:
					if mail_que.empty() and not mail_str:
						break
					mail_str = mail_str or mail_que.get()
					try:
						mail_to = extract_email(mail_str)
						is_dangerous = is_dangerous_email(mail_to)
						if not mail_to or is_dangerous:
							msg = current_server+red('-\b'+'>'*(mails_sent%3)+b+'>',2)+red('>> '[mails_sent%3:],2)+(mail_to and 'skipping' or 'no')+' email - '+(mail_to and mail_to+' ('+is_dangerous+')' or mail_str)
							results_que.put((self.name, msg, mails_sent))
							mail_str = False
							time.sleep(0.5)
							continue
						smtp_sendmail(server_obj, smtp_user, mail_str)
						msg = current_server+green('+\b'+'>'*(mails_sent%3)+b+'>',0)+green('>> '[mails_sent%3:],0)+mail_str
						results_que.put((self.name, msg, mails_sent))
						mails_sent += 1
						mail_str = False
					except Exception as e:
						if re.search(r'suspicio|suspended|too many|limit|spam|blocked|unexpectedly closed|mailbox unavailable', str(e).lower()):
							raise Exception(e)
						msg = current_server+orange('~\b{!} '+str(e).split(' b\'')[-1].strip(),0)
						results_que.put((self.name, msg, mails_sent))
						time.sleep(1)
						break
			except Exception as e:
				msg = current_server+red('~\b[X] '+str(e).split(' b\'')[-1].strip(),0)
				results_que.put((self.name, msg, mails_sent))
				smtp_str in smtp_pool_array and smtp_pool_array.remove(smtp_str)
				time.sleep(1)
			time.sleep(0.04)
			loop_times.append(time.perf_counter() - time_start)
			len(loop_times)>100 and loop_times.pop(0)
	threads_counter -= 1

def get_random_name():
	fnames = 'Dan|Visakan|Molly|Nicole|Nick|Michael|Joanna|Ed|Maxim|Nancy|Mika|Margaret|Melody|Jerry|Lindsey|Jared|Lindsay|Veronica|Marianne|Mohammed|Alex|Lisa|Laurie|Thomas|Mike|Lydia|Melissa|Ccsa|Monique|Morgan|Drew|Milan|Nemashanker|Benjamin|Mel|Norine|Deirdre|Millie|Tom|Maria|Mighty|Terri|Marsha|Mark|Stephen|Holly|Megan|Fonda|Melanie|Nada|Barry|Marilyn|Letitia|Mary|Larry|Mindi|Alexander|Mirela|Lhieren|Wilson|Nandan|Matthew|Nicolas|Michelle|Lauri|John|Amy|Danielle|Laly|Lance|Nance|Debangshu|Emily|Graham|Aditya|Edward|Jimmy|Anne|William|Michele|Laura|George|Marcus|Martin|Bhanu|Miles|Marla|Luis|Christa|Lina|Lynn|Alban|Tim|Chris|Fakrul|Angad|Nolan|Christine|Anil|Marigem|Matan|Louisa|Timothy|Mirza|Donna|Steve|Chandan|Bethany|Oscar|Marcie|Joanne|Jitendra|Lorri|Manish|Brad|Swati|Alan|Larissa|Lori|Lana|Amanda|Anthony|Luana|Javaun|Max|Luke|Malvika|Lee|Nic|Lynne|Nathalie|Natalie|Brooke|Masafumi|Marty|Meredith|Miranda|Liza|Tanner|Jeff|Ghazzalle|Anna|Odetta|Toni|Marc|Meghan|Matt|Fai|Martha|Marjorie|Christina|Martina|Askhat|Leo|Leslie|As|Mandy|Jenene|Marian|Tia|Murali|Heidi|Jody|Mamatha|Sudhir|Yan|Frank|Lauren|Steven|Jessica|Monica|Aneta|Leanne|David|Mallory|Ianne|Melaine|Leeann|Arvid|Marge|Greg|Melinda|Alison|Deborah|Nikhol|Charles|Doug|Nicholas|Alexandre|Nels|James|Yvette|Muruganathan|Mangesh|Cfre|Claudia|Austin|Mara|Linda|Dana|Stewart|Oleg|Nikhil|Emilio|Lenn|Emiliano|Lennart|Cortney|Cullen|Lena|Garima|Levent|Nelson|Xun|Jenn|Noah|Marshall|Nozlee|Lois|Lars|Alissa|Casimir|Fiona|Mehul|Brian|Marvin|Hiedi|Ashley|Luise|Vinay|Mithun|Denise|Orlando|Madison|Colin|Mina|Nichole|Norman|M|Jason|Nereida|Damon|Mohamed|Tomas|Len|Liliana|Marybeth|Dave|Cole|Jennifer|Lucas|Milton|Makhija|Marlon|Miki|Joan|Barbara|Nevins|Marta|Angelique|Muriel|Cornelia|Monty|Mouthu|Jayson|Louis|Janet|Moore|Nathan|Luanne|Dheeraj|Chelley|Vishal|Laree|Ado|Mona|Lorena|Marco|Jeremy|Joe|Andrew|Lloyd|Mahalaxmi|Niamh|Daniel|Mitzi|Les|Laurence|Levonte|Nuno|Mj|Derek|Susan|Deandre|Nizar|Tanya|Maritza|Gabe|Imtiaz|Nira|Ervin|Maureen|Lalit|Lynwood|Li|Christopher|Min|Liz|Diane|Michaeline|Craig|Marianna|Becky|Leonard|Aj|Jeffrey|Edison|Csm|Clay|Marie|Jae|Bruce|Marcello|Lucille|Megha|Todd|Elizabeth|Angelica|Minette|Lynda|Liton|Carrie|Dennis|Amit|May|B|Laurel|Istiaq|Valerio|Sujesh|Vincent|Charley|Benj|Jeanine|Marcin|Ali|Arnaud|Mirna|Dianne|Namita|Melvin|Geroge|Omar|Wesley|Dominic|Adrian|Tina|Eric|Graciano|Leon|Mario|Brandon|Isabel|Antonio|Liang|Lara|Nadezhda|Navjot|Vicki|Danette|Nikia|Sunil|Leighann|Dustin|Adekunle|Natalia|Taylor|Darryl|Danny|Lorenza|Manny|Dorothy|Maryanne|Tarun|Lou|Oliver|Jay|Carla|Atle|Geoff|Mathew|Brit|Casey|Martijn|Laquita|Aaron|Mahesh|Althea|Lorra|Nina|Tammy|Ellie|Calvin|Marcia|Tamir|Meital|Cheryl|Gordon|Mujie|Marylou|Nicki|Manoj|Mitch|Tania|Hector|Dallan|Carol|Adenton|Nadira|Chengxiang|Naomi|Nirav|Frances|Lorelei|Methila|Ilias|Madhusudan|Jim|Noel|Harsha|Mayra|Masano|Nellie|Mengli|Lalita|Margo|Olga|Chase|Vineet|Mae|Akash|Vandhana|Naren|Ian|Niall|Alicia|Nate|Ben|Bill|Meagan|Madelene|Neha|Louise|Marti|Maarten|Asim|Earlyn|Nobumasa|Maaike|Sylvain|Mack|Maggie|Lester|April|Trent|Leland|Maged|Loren|Lycia|Leandrew|Learcell|Terra|Clara|Lasse|Nadine|Lew|Marquita|Marina|Leah|Miche|Brett|Hao|Lex|Maurice|Natasha|Moni|Melodie|Libby|Elliott|Aprajit|Ning|Lanette|Ivy|Liautaud|Merla|Mihaela|Heather|Nicola|Adger|Alyssa|Marusca|Donald|Mashay|Ashlee|Destine|Victor|Narin|Mathias|Branden|Geoffrey|Manjunath|Alexis|Dahlia|Mayer|Taras|Monte|Igor|Harry|Yonas|Obed|Albert|Darrell|Maxime|Zoe|Leigh|Tal|Thoai|Curtis|Cindy|Evan|Gomathy|Tessa|Elaheh|Marinca|Abby|Veronika|Onetta|Nikki|Mohsen|Edwin|Margie|Mick|Bonnie|Trina|Marilia|Nora|Leonor|Eddie|Gail|Arjan|Lorna|Mengwei|Aray|Ann|Wolfgang|Barb|Mahir|Swapna|Lijuan|Dinesh|Mayur|Marit|Beat|Maricela|Erika|Muhammad|Avi|Nestor|Anchal|Avni|Amber|Jessy|Luz|Midhat|Anita|Nandini|Lola|Nathaniel|Cleo|Jean|Lynette|Mitchell|Lawrence|Liviu|Madelyn|Nabil|Mila|Carson|Marcy|Mohammad|Bobby|Theresa|Lei|Nazim|Laurens|Chetan|Magdalena|Charlotte|Ana|Nissanka|Neil|Glenn|Mari|Miguel|Devin|Courtney|Mora|Jocelyn'.split('|')
	lnames = 'Scearcy|Sachchi|Ohalloran|Smith|Karahalios|Puglisi|Cordero|Pinero|Turcan|Poor|Tanaka|Henderson|Baltzer|Ivy|Jones|Mertens|Oyer|Polin|Lee|Greene|Sanchez|St|Kazi|Glowik|Mccann|Hogberg|Hutchinson|Morse|Hardy|Luke|Kincaid|Ceh|Guerrero|Roe|Vanderwert|Area|Singh|Ho|Koehler|Ask|Oakes|Vega|Sternfeldt|Huddleston|Massa|Interactive|Ruzsbatzky|Miller|Neeley|Posnock|Marando|Bright|Moyers|Walsh|Cataldi|Herbst|Lange|Shepherd|Nelson|Doherty|Willms|Lane|Romashkov|Trudeau|Bancu|Fraga|Wei|Kulkarni|Linkewich|Rouquette|Messer|Naypaue|Giafaglione|Bunting|Ahlersmeyer|Deschene|Viggers|Vadassery|Alves|Wilson|Trueworthy|Mukherjee|Sharp|Thomas|Prabhakar|Moore|Horikawa|Horne|Brostek|Richardson|Lewis|Alberti|Kelso|Mashita|Forsling|Dong|Diaz|Gibbs|Chitturi|Trackwell|Jeanne|Napoleon|Mclau|Craigie|Dacosta|Johnson|Farr|Martinez|Rauscher|Barclay|Webber|Delortlaval|Lin|Rinenbach|Weyand|Syed|Brady|Pathak|Fairchild|Ta|Higgins|Zhang|Kensey|Puthin|Malundas|Marom|Labed|Smagala|Zelenak|Capecelatro|Hambley|Causevic|Simmet|Schneider|Poovaiah|Enge|Maddatu|Wheeler|Henken|Fett|Goldston|Solanki|Arnce|Tamayo|Visa|Labruyere|French|Bennett|Shah|Osborne|Curley|Vaidya|Valachovic|Witters|Terrill|Thompson|Fryer|Price|Fulgieri|Queen|Moradi|Bell|Kort|Gillfoyle|Wosje|Aswal|Chelap|Wie|M.;4831600947|Niziolek|Whitley|Huntington|Drew|Santana|Basch|Simond|Bakke|Massi|Usuda|Mcquade|Rodgers|Kerpovich|Williams|Marciano|Ludeman|Strange|Spano|Hahn|Elgin|Mirkooshesh|Angottiportell|Deet|Pumphrey|Sandler|Vogel|Flynn|De|Wagner|Cheung|Dalberth|Skoog|Benavides|Ginsberg|Woodworth|Roachell|Monfeli|Sadow|Mejean|Song|Smurzynski|Mckee|Hunter|Gabdulov|Arnaboldi|Saxton|Worthy|Asd|Kee|Thigpen|Ormand|Schwartz|Sandberg|Pitner|Achutharaman|Seyot|Mientka|Hougom|Speer|Pearce|Hernandez|Long|Earley|Fulton|Chiavetta|Mcbrayer|Chamarthi|Barag|Kumar|Yang|Casari|Slicer|Lang|Bourgeois|Perry|Spivack|Taylor|Hughes|Seric|Barth|Hayter|Westerdale|Cook|Rico|Fasthoff|Trainor|Kleinman|Harverstick|Greenwell|Grady|Kirkpatrick|Saxon|Ujvari|Glander|Robinson|Goddard|Chen|Kramer|Caracache|Ramer|Baudet|Casner|Jenson|Butz|Hooper|Ramanathan|Marks|Dhawale|Ferguson|Huapaya|Mcdowell|Haehn|Piccolo|Carns|Jeffrey|Gibitz|Hsu|Jindra|Isaev|Gaikwad|Manganaro|Gerbelli|Sisson|Santiago|Izzo|Mills|Wiseen|Cooney|Libby|Miles|Mcgough|Fox|Koch|Rochelle|Mehta|Riffee|Erkok|Gibby|Freitas|Remund|Arones|Penn|Liu|Farkas|Kelkenberg|Samadzadeh|Castillo|Garrett|Cooper|Djuvik|Fishbane|Niedzielski|Kan|Hammond|Kruse|Rees|Leone|Vanbemmel|Ramani|Macdonald|Hall|Kiragu|Folkert|Tremaine|Zachry|Sherpard|Gearo|Richard|Voy|Weinem|Bhatia|Marder|Whittam|Garcia|Brannen|Mcindoe|Nandi|Mcgowen|Orr|Tamsitt|Kingsford|Lillie|Sheehan|Mylexsup|Davis|Yanez|Neal|Spinks|Massimo|Taulbee|Yunus|Maxian|Giuliano|Jorgenson|Sullivan|Obrien|Garcis|Allen|Kowalske|Wirtzberger|Kaiser|Millen|Mclaughlin|Sinclair|Messina|Lins|Robertson|Kindle|Velez|Vin|Argueta|Seltzer|Hayes|Clark|Slocum|Laski|Jim|Fey|Weston|Licata|Hanson|Mohlenkamp|Kos|Bilotti|Popke|Sloss|Campbell|Pham|Eby|Tipps|Walker|Hertzman|Harrell|Jansen|Kumarasamy|Lopez|Lindsley|Silver|Seremeth|Gorelick|Snider|Cauley|Ann|Garmatz|Ashcraft|Pawar|Kain|Coronel|Wilkes|Hinkle|Lloyd|Hassan|Ghangale|Kurtz|Trakic|Gibson|Shaheen|Calkins|Kuhlmann|Nishihara|Skrbin|Vanora|Fitzgerald|Trifler|Arriola|Krishnamurthy|Leleux|Weum|Dunne|Bairstow|Choi|Boyce|Joe|Ploshay|Tibbits|Minkley|Coshurt|Santos|Odonnell|Rios|Burkart|Turner|Parker|Racki|Paliferro|Wcislo|Donchatz|Ford|Ladak|Emmick|Mobed|Quiles|Gagne|Medrano|Hussain|Tejada|Alterson|Anastasia|Eddie|Adams|Motto|Brooks|Sharma|Byrum|Cheng|Kagan|Helman|Kim|Roller|Bordelon|Dozal|Mitchell|Barnes|Hummel|Fenton|Anderson|Reinbold|Dillard|Mattingly|Shcherbina|Mintz|Tullos|Siuda|Maggi|Lucas|Bouchard|Cortes|Dunning|Howard|Gower|Cotter|Kisner|Kennedy|Palacios|Levy|Uppal|Oholendt|Jew|Schultz|Dabrock|Peel|Cls|Deady|Park|Corradini|Sisneros|Hartnett|Nazaredth|Gentile|Hester|Richcreek|Giermak|Kay|Shadle|Pott|Kubey|Chacana|Rangel|York|Cooke|Squire|Roush|Tillman|Kandel|Roy|Sun|Herrmann|Chong|Knudsen|Coomer|Sarkar|Woodward|Banks|Allan|Schiller|Nicholls|Mahmud|Fiala|Horvath|Dangelo|Vickery|Somanathan|Sellier|Alejos|Ellis|Roska|Thibeault|Fuller|Brown|Roach|Bulgajewski|Oztekin|Sabol|Nomellini|Magnier|Berglund|Schau|Gramling|Francisco|Korman|Shubhy|Gossmeyer|Murray|Foster|Blevins|Arias|Soda|Litwin|Solak|Casey|Schmidt|Hartshorn|Deck|Leodoro|Swenson|Luc|Zamudio|Lacoe|Simko|Metz|Pace|Benjamin|Tolwinska|Little|Mcdonough|Lynch|Worley|Funk|Bachtle|Estes|Hennessey|Wurtzel|Jimenez|Pilogallo|Donaldson|Eng|Weiss|Coy|Bockstahler|Nekrasova|Rand|Gagen|Masters|Root|Eldert|Bleiler|Huang|Ryan|Janca|Cozart|Bhatara|Todd|Haylett|Mckinney|Adeniran|Oneill|Zamparini|Lafauce|Hetzel|Boers|Elder|Glaser|Kienzler|Reverendo|Cruse|Salafia|Bossard|Muir|Khanna|Orsatti|Mantheiy|Moorehead|Trevino|Delorme|Gregory|Gratwick|Mooney|Reitan|L|Flachaire|Simpson|Edwards|Humes|Probst|Wood|La|Hardesty|Rogers|Batten|Peifer|Devolt|Tesnovets|Hitchcock|Scarlata|Khot|Bush|Navale|Volper|Schnell|Emmons|Newton|Adkins|Roberts|Romaine|Barker|Louie|Richmond|Stear|Derr|Hallinger|See|Heller|Raveenthran|Bridges|Robison|Caney|Thaves|Darab|Corridore|Haas|Medved|Hain|Chiu|Chalmer|Sirotnak|Lavecchia|Buoniconti|Karpe|Poell|Massicot|Bauer|Augusty|Cfp|Guzman|Zuleta|Dijohnson|Whatley|Zickur|Denton|Mety|Dhani|Ren|Rivas|Chartier|Botuck|Mistry|Rigney|Hough|Rahman|Panagiotou|Bookbinder|Mcnabb|Reddy|Desma|Giampicclo|Granata|Shekleton|Shivaram|Marzan|Abramson|Mack|Hribar|Wolman|Machado|Weispfenning|Adcock|Sugiyama|Manning|Mcclure|Salinas|Yuan|Langer|Metcalf|Cherian|Baamonde|Lolam|Bealhen|Trout|Titkova|Gariti|Lamb|Myhrvold|Peltekian|Londergan|Zdroik|Filkins|Nichols|Dieter|Chaturvedi|Kotsikopoulos|Saqcena|Naranjo|Atkinson|Woodley|Kushner|Thorson|Ropple|Phoenix|Jaganathan|Gomar|Denham|Drelich|Livermore|Burns|Cartwright|Wickum|Kluger|Hockenhull|Heindl|Zak|Shipman|Saple|Besmond|Malone|Caldwell|King|Balfe|Tilton|Van|Iqbal|Shuffler|Berry|Panetta|Mori|Meijer|Mckeever|Grande|Stinson|Swanson|Wong|Gavilondo|Jaffe|Innes|Junker|Strickler|Fouad|Phillips|Stevens|Lemmon|Reinholz|Rogan|Krongold|Gremillon|Phipps|Loyd|Atkins|Downing|Parsons|Stanovich|Folger|Savio|Holmes|Osgood|Harris|Soloski|Galvin|Low|Jamt|Baldwin|Doohen|Dustman|Clopton|Zamora|Austin|Delery|Hansen|Samson|Buddin|Hollander|Xiong|Maultsby|Madore|Fortuna|Heckman|Cooey|Heise|Matsuda|Bent|Kar|Gahan|Wang|Yip|Butts|Lincoln|Dorminy|Golojuch|Florestal|Escarment|Aye|Sheldon|Petrova|Haines|Beaudoin|Watkins|Knuth|Balena|Shay|Bogush|Thomann|Blackwell|Carr|Pochiraju|Rauch|Waldeisen|Harding|Lacroix|Kolber|Horenstein|Hoegerman|Ilfeld|Wnorowski|Jacobs|Burnette|Gatto|Wandell|Anerella|Melara|Deisner|Merchant|Mount|Borchardt|Tschupp|Ciotola|Leung|Frailey|Lemons|Clement|Wattanavirun|Schmidheiny|Harness|Schechter|Gebert|Peralta|Stanley|Sandoval|Rangaswamy|Ranallo|Chrostowski|Wallach|Graham|Goltermann|Crosby|Boschman|Pelta|Szmagala|Fry|Konforti|Garduno|Dolan|Rockwell|Mcgah|Damm|Gebrewold|Benito|Chang|Yeboah|Coleman|Steib|London|Ashby|Schulman|Ferrara|Griffith|Sadrieh|Anetakis|Serrano|Konidaris|Kastenson|Barel|Le|Molina|Peterson|Leddy|Espinal|Cohn|Swamy|Chermiset|Link|Hobson|Pentzke|Shirneshan|Veno|Peters|Warren|Stanfield|Magnus|Grantham|Szabo|Hou|Juncherbenzon|Lara|Marlatt|Millbrooke|Sofastaii|Downer|Matheis|Galati|Olson|Wiederrecht|Quintana|Drozd|Weaver|Russell|Fisher|Dorrian|Morris|Ortiz|Newnam|Piper|Modic|Pfister|Butler|Tschetter|Tibbetts|Mattox|Frank|Curry|Zayas|Alvarez|Arrington|Hanlon|Freedman|Lineberry|Robyn|Morakinyo|Stokkel|Rinear|Zheng|Cutting|Driggers|Adil|Nikumbhe|Farver|George|Gyurko|Riley|Greve|Dreyer|Petschl|Hodzic|Rawe|Vijayakumar|Kang|Drees|Calderone|Alvarado|Watson|Belcher|Chaudhari|Panchal|Carnevale|Ayers|Studinger|D|Latib|Haksar|Oles|Dowland|Borreli|Serravalle|Vincent|Sachdeva|Wallace|Jain|Segal|Aguirre|Salihovic|Antonio|Viau|Marek|Murphy|Barratt|Fischer|Lennon|Mike|Ramaswamy|Defruscio|Hamby|Pallant|Clifton|Chenevert|Stuebe|Bloss|Rowe|Speak|Cupido|Debartolomeis|Katz|Brophy|Myster|Frazier|Olaru|Rojas|Straub|Keenan|Phan|Agresta|Mansour|Fiore|Pucci|Levin|Abrams|Cox|Lockwood|Vangilder|Olshan|Tyus|Murry|Crites|Leonard'.split('|')
	return random.choice(fnames)+' '+random.choice(lnames)

def load_config():
	global config, smtp_pool_array
	head_name = 'madcatmailer'
	temp_config = configparser.ConfigParser({
		'smtps_list_file': '',
		'mails_list_file': '',
		'mails_to_verify': '',
		'mail_from': '',
		'mail_subject': '',
		'mail_body': '',
		'attachment_files': '',
		'redirects_file': ''
	})
	config['debug'] = True if 'debug' in sys.argv else False
	if len([i for i in sys.argv if i!='debug']) == 2:
		config['config_file'] = sys.argv[1] if is_file_or_url(sys.argv[1]) else exit(err+'wrong config path or filename: it must be like '+bold('<...>.config'))
	else:
		config['config_file'] = max([i for i in os.listdir() if re.search(r'.+\.config$', i)] or [''], key=os.path.getctime)
	if not config['config_file']:
		print(wrn+'nor '+bold('.config')+' files found in current directory, nor provided as a parameter')
	while not is_file_or_url(config['config_file']):
		config['config_file'] = input(npt+'enter desired config filename: ')
	temp_config.read(config['config_file'])
	if not temp_config.has_section(head_name):
		exit(err+'malformed config file')
	for key, value in temp_config.items(head_name):
		config[key] = value
	config['attachment_files_data'] = {}
	if not is_file_or_url(config['smtps_list_file']):
		exit(err+'cannot open smtps list file. does it exist?')
	else:
		smtp_pool_array = read_lines(config['smtps_list_file'])
		if len([smtp_line for smtp_line in smtp_pool_array if re.match(r'[\w.+-]+\|\d+\|[@\w.+-]+\|[^|]+', smtp_line)])<len(smtp_pool_array):
			exit(err+bold(config['smtps_list_file'])+' list is not in format '+bold('host|port|username|password'))
	if not is_file_or_url(config['mails_list_file']):
		exit(err+'cannot open mails list file. does it exist?')
	if len([is_valid_email(mail) for mail in config['mails_to_verify'].split(',')])<config['mails_to_verify'].count(',')+1:
		exit(err+'not all test emails looks valid. check them, please')
	if not config['mail_from']:
		exit(err+'please fulfill '+bold('mail_from')+' parameter with desired name and email')
	if not config['mail_subject']:
		exit(err+'please fulfill '+bold('mail_subject')+' parameter with desired email subject')
	if not config['mail_body']:
		exit(err+'please put the path to email body file or mail body itself as a string into '+bold('mail_body')+' parameter')
	if config['attachment_files'] and len([is_file_or_url(file) for file in config['attachment_files'].split(',')])<config['attachment_files'].count(',')+1:
		exit(err+'one of attachment files seems does not exists')
	for attachment_file_path in config['attachment_files'].split(','):
		if is_file_or_url(attachment_file_path):
			config['attachment_files_data'][attachment_file_path.split('/')[-1]] = read(attachment_file_path)
	if config['redirects_file'] and not is_file_or_url(config['redirects_file']):
		exit(err+'please put the path to the file with redirects into '+bold('redirects_file')+' parameter')
	else:
		config['redirects_list'] = read_lines(config['redirects_file']) if config['redirects_file'] else ['']

def fill_mail_queue(mail_list_file, verify_every, mails_to_verify):
	global mail_que, total_mails_to_sent
	j = 0
	for i in read_lines(mail_list_file):
		i = normalize_delimiters(i)
		if j % verify_every == 0:
			for mail_to_verify in mails_to_verify.split(','):
				mail_que.put(i.replace(extract_email(i), mail_to_verify))
		mail_que.put(i)
		j += 1
	if not mail_que.qsize():
		exit(err+'not enough emails. empty file?')
	total_mails_to_sent = mail_que.qsize()

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

def printer():
	global total_sent, skipped, total_mails_to_sent, speed, loop_time, cpu_usage, mem_usage, net_usage, threads_count, threads_statuses, smtp_pool_array, got_updates, time_start
	while True:
		clock = sec_to_min(time.time()-time_start).replace(':', (' ', z+':'+b)[int(time.time()*2)%2])
		status_bar = (
			f'{b}['+green('\u2665',int(time.time()*2)%2)+f'{b}]{z}'+
			f'[ {bold(clock)} \xb7 sent: {bold(num(total_sent))}/{bold(num(total_mails_to_sent))} ({bold(round(total_sent/total_mails_to_sent*100))}%), skipped: {bold(num(skipped))} ]'+
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
		time.sleep(0.04)

signal.signal(signal.SIGINT, quit)

config = {}
threads_counter = 0
total_mails_to_sent = 0
time_start = time.time()
mail_que = queue.Queue()
results_que = queue.Queue()
smtp_pool_array = []
threads_statuses = {}
error_log = []
verify_every = 1000
threads_count = 40
connection_timeout = 5
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
resolver_obj.nameservers = custom_dns_nameservers
resolver_obj.rotate = True

show_banner()
tune_network()
load_config()
fill_mail_queue(config['mails_list_file'], verify_every, config['mails_to_verify'])

print(okk+'loading config:                '+bold(config['config_file']))
print(inf+'smtp servers loaded:           '+bold(num(len(smtp_pool_array))))
print(inf+'total lines to procceed:       '+bold(num(total_mails_to_sent)))
print(inf+'verification emails:           '+bold(config['mails_to_verify']))
print(inf+'mail body:                     '+bold(config['mail_body']))
print(inf+'attachments:                   '+bold(config['attachment_files'] or '-'))
print(inf+'file with redirects:           '+bold(config['redirects_file'] or '-'))
input(npt+'press '+bold('[ Enter ]')+' to start...')

setup_threads()

while True:
	time_takes = round(time.time()-time_start, 1)+0.09
	while not results_que.empty():
		thread_name, thread_status, mails_sent = results_que.get()
		total_sent += 1 if '+\b' in thread_status else 0
		skipped += 1 if '-\b' in thread_status else 0
		if config['debug']:
			error_log += [thread_status] if '{!}' in thread_status or '[X]' in thread_status or '-\b' in thread_status else []
			len(error_log)>200 and error_log.pop(0)
		mails_per_second = round(mails_sent/time_takes, 1)
		threads_statuses[thread_name] = f'{thread_name}: '.rjust(7)+str_ljust(thread_status, window_width)+f'{mails_sent} sent ({mails_per_second} mail/s)'.rjust(23)
		got_updates = True
	if threads_counter == 0:
		if mail_que.empty():
			mails_per_second = round(total_mails_to_sent/time_takes, 1)
			exit('\n'+wl+okk+f'all done in {bold(sec_to_min(time_takes))} minutes. speed: {bold(mails_per_second)} mail/sec.')
		if not len(smtp_pool_array):
			exit('\n'+wl+err+f'smtp list exhausted. all tasks terminated.\a')
	time.sleep(0.04)

