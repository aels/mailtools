#!/usr/local/bin/python3

import os, sys, threading, time, queue, random, re, signal, smtplib, ssl, socket

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

if sys.version_info[0] < 3:
	raise Exception("Python 3 or a more recent version is required.")
try:
	from alive_progress import alive_bar
except ImportError:
	from pip._internal import main as pip
	pip(['install', '--user', 'alive_progress'])
	from alive_progresss import alive_bar

#~~~~~~~~~~~~~~~~~~ replace this with your values ~~~~~~~~~~~~~~~~~~~

smtp_list_file          = 'smtp_list.txt'
mail_list_file          = 'mail_list.txt'
mail_body_file          = 'mail_body.txt'
attachment_files        = 'masterclass_invoice.html'
redirects_file 			= ''
mail_to_verify          = 'omgmovebx@outlook.com'
verify_every			= 1000
threads_count 			= 30
connection_timeout 		= 5

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

mail_list = []
smtp_list = []
threads_statuses = {}

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

def quit(signum, frame):
	print('\b'*10+f"{c.WARN}Exiting...{c.END}\n")
	sys.exit(0)

def worker_item(mail_que, smtp_que, worker_results):
	global threads_counter
	self = threading.current_thread()
	mails_sent = 0
	error_regexp = 'could not deliver|per session|timed out|rate-limited|too much|too many|run connect|mailbox unavailable|local error|451'
	while True:
		if smtp_que.empty():
			break
		else:
			smtp = smtp_que.get()
			worker_results.put((self.name,f'{c.WARN}{c.BOLD}switching to{c.END} {smtp}',mails_sent))
			smtp_server, port, smtp_user, password = smtp.split('|')
			try:
				server_obj = smtp_connect(smtp_server, port, smtp_user, password)
				while True:
					if mail_que.empty():
						worker_results.put((self.name,f'done with {c.GREEN}{c.BOLD}{mails_sent}{c.END} mails',mails_sent))
						break
					mail_str = mail_que.get()
					try:
						smtp_sendmail(server_obj,smtp_user,mail_str)
						worker_results.put((self.name,f'{smtp_user} sent to {c.GREEN}{c.BOLD}{mail_str}{c.END}',mails_sent))
						mails_sent += 1
						mail_que.task_done()
					except Exception as e:
						mail_que.put(mail_str)
						e = str(e).strip()
						if re.match(error_regexp, e):
							smtp_que.put(smtp)
							# worker_results.put((self.name,f'{c.WARN}{c.BOLD}{e}{c.END}',mails_sent))
							worker_results.put((self.name,f'rate-limit error, {smtp_server} {c.WARN}{c.BOLD}added back to queue{c.END}',mails_sent))
						else:
							worker_results.put((self.name,f'{c.FAIL}{c.BOLD}{e}{c.END}',mails_sent))
						time.sleep(1)
						break
				server_obj.quit()
			except Exception as e:
				e = str(e).strip()
				if re.match(error_regexp, e):
					smtp_que.put(smtp)
					worker_results.put((self.name,f'timeout error, {smtp_server} {c.WARN}{c.BOLD}added back to queue{c.END}',mails_sent))
				else:
					worker_results.put((self.name,f'connection error: {c.FAIL}{c.BOLD}{e}{c.END}',mails_sent))
				time.sleep(1)
				continue
			if mail_que.empty():
				break
	threads_counter -= 1

def is_binary(data):
	if not str(data).find("b'"):
		return True
	else:
		return False

def is_valid_email(email):
	return re.match('^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email.lower())

def tuple_to_binary(tup):
	return '|'.join(tup).encode().split(b'|')

def expand_macros(bytes_data, subs):
	placeholders = '{{1}}|{{2}}|{{mail}}|{{username}}|{{redirect_url}}|{{random_name}}'.split('|')
	subs_length = len(subs)
	if is_binary(bytes_data):
		for i in range(subs_length):
			bytes_data = bytes_data.replace(tuple_to_binary(placeholders)[i], tuple_to_binary(subs)[i])
	else:
		for i in range(subs_length):
			bytes_data = bytes_data.replace(placeholders[i], subs[i])
		macros = re.findall('(\{\{.*?\}\})', bytes_data)
		for macro in macros:
			bytes_data = bytes_data.replace(macro,random.choice(macro[2:-2].split('|')))
	return bytes_data

def cut_str(string, length):
	return (string, string[0:length-3]+f'...{c.END}')[len(string)>length]

def dbytes_statuses():
	global smtp_left, threads_statuses, threads_counter
	rows = len(threads_statuses)
	sys.stdout.write('\033[F'*rows+'\033[F')
	print((f'[ cpu load: {c.BOLD}{round(os.getloadavg()[0]/os.cpu_count(),2)}{c.END} ]'+
		   f'[ threads: {c.BOLD}{threads_counter}{c.END} ]'+
		   f'[ {c.BOLD}{smtp_left}{c.END} SMTPs left ]').rjust(144))
	for i in range(rows):
		print(threads_statuses['thread'+str(i)])	

def smtp_connect(smtp_server, port, user, password):
	global connection_timeout
	try:
		if port == '587':
			tls_context = ssl.create_default_context()
			tls_context.check_hostname = False
			tls_context.verify_mode = ssl.CERT_NONE
			server_obj = smtplib.SMTP(smtp_server, port, timeout=float(connection_timeout))
			server_obj.ehlo()
			server_obj.starttls(context=tls_context) 
		elif port == '465':
			server_obj = smtplib.SMTP_SSL(smtp_server, port, timeout=float(connection_timeout))
		else:
			server_obj = smtplib.SMTP(smtp_server, port, timeout=float(connection_timeout))
	except Exception as e:
		server_obj = smtplib.SMTP(smtp_server, port, timeout=float(connection_timeout))
	server_obj.ehlo()
	server_obj.login(user, password)

	return server_obj

def smtp_sendmail(server_obj,mail_from,mail_str):
	global mail_body_file, attachment_files, redirects_file
	mail_str = mail_str.replace('|',';').replace(':',';')
	mail_str += ';'*(2-mail_str.count(';'))
	mail_to, one, two = mail_str.split(';')
	mail_subject_and_body = open(mail_body_file,'r').read().split('\n\n')
	subject = mail_subject_and_body.pop(0)
	body = '\n\n'.join(mail_subject_and_body)
	redirect_url = random.choice(open(redirects_file, 'r').read().splitlines()) if os.path.isfile(redirects_file) else ''
	random_name = get_random_name()
	subs = (one,two,mail_to,mail_to.split('@')[0].capitalize(),redirect_url,random_name)

	if not is_valid_email(mail_to):
		return False

	subject = expand_macros(subject,subs)
	body = expand_macros(body,subs)

	message = MIMEMultipart()
	message['From'] = f'{random_name} <{mail_from}>'
	message['To'] = mail_to
	message['Subject'] = subject
	message.attach(MIMEText(body, 'html', 'utf-8'))
	for attachment_file in attachment_files.split(','):
		attachment_display_name = attachment_file.split('/')[-1]
		if os.path.isfile(attachment_file):
			attachment_body = open(attachment_file, 'rb').read()
			attachment_body = expand_macros(attachment_body,subs)
			attachment = MIMEApplication(attachment_body)
			attachment.add_header('content-disposition', 'attachment', filename=attachment_display_name)
			message.attach(attachment)
	headers = 'Return-Path: '+mail_from+'\n'
	headers+= 'Reply-To: '+mail_from+'\n'
	headers+= 'X-Priority: 1\n'
	headers+= 'X-MSmail-Priority: High\n'
	headers+= 'X-Source-IP: 127.0.0.1\n'
	headers+= 'X-Sender-IP: 127.0.0.1\n'
	headers+= 'X-Mailer: Microsoft Office Outlook, Build 10.0.5610\n'
	headers+= 'X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441\n'
	headers+= 'Received: '+random_name+'\n'
	message_raw = headers + message.as_string()

	server_obj.sendmail(mail_from, mail_to, message_raw)

def get_random_name():
	fnames = 'Dan|Visakan|Molly|Nicole|Nick|Michael|Joanna|Ed|Maxim|Nancy|Mika|Margaret|Melody|Jerry|Lindsey|Jared|Lindsay|Veronica|Marianne|Mohammed|Alex|Lisa|Laurie|Thomas|Mike|Lydia|Melissa|Ccsa|Monique|Morgan|Drew|Milan|Nemashanker|Benjamin|Mel|Norine|Deirdre|Millie|Tom|Maria|Mighty|Terri|Marsha|Mark|Stephen|Holly|Megan|Fonda|Melanie|Nada|Barry|Marilyn|Letitia|Mary|Larry|Mindi|Alexander|Mirela|Lhieren|Wilson|Nandan|Matthew|Nicolas|Michelle|Lauri|John|Amy|Danielle|Laly|Lance|Nance|Debangshu|Emily|Graham|Aditya|Edward|Jimmy|Anne|William|Michele|Laura|George|Marcus|Martin|Bhanu|Miles|Marla|Luis|Christa|Lina|Lynn|Alban|Tim|Chris|Fakrul|Angad|Nolan|Christine|Anil|Marigem|Matan|Louisa|Timothy|Mirza|Donna|Steve|Chandan|Bethany|Oscar|Marcie|Joanne|Jitendra|Lorri|Manish|Brad|Swati|Alan|Larissa|Lori|Lana|Amanda|Anthony|Luana|Javaun|Max|Luke|Malvika|Lee|Nic|Lynne|Nathalie|Natalie|Brooke|Masafumi|Marty|Meredith|Miranda|Liza|Tanner|Jeff|Ghazzalle|Anna|Odetta|Toni|Marc|Meghan|Matt|Fai|Martha|Marjorie|Christina|Martina|Askhat|Leo|Leslie|As|Mandy|Jenene|Marian|Tia|Murali|Heidi|Jody|Mamatha|Sudhir|Yan|Frank|Lauren|Steven|Jessica|Monica|Aneta|Leanne|David|Mallory|Ianne|Melaine|Leeann|Arvid|Marge|Greg|Melinda|Alison|Deborah|Nikhol|Charles|Doug|Nicholas|Alexandre|Nels|James|Yvette|Muruganathan|Mangesh|Cfre|Claudia|Austin|Mara|Linda|Dana|Stewart|Oleg|Nikhil|Emilio|Lenn|Emiliano|Lennart|Cortney|Cullen|Lena|Garima|Levent|Nelson|Xun|Jenn|Noah|Marshall|Nozlee|Lois|Lars|Alissa|Casimir|Fiona|Mehul|Brian|Marvin|Hiedi|Ashley|Luise|Vinay|Mithun|Denise|Orlando|Madison|Colin|Mina|Nichole|Norman|M|Jason|Nereida|Damon|Mohamed|Tomas|Len|Liliana|Marybeth|Dave|Cole|Jennifer|Lucas|Milton|Makhija|Marlon|Miki|Joan|Barbara|Nevins|Marta|Angelique|Muriel|Cornelia|Monty|Mouthu|Jayson|Louis|Janet|Moore|Nathan|Luanne|Dheeraj|Chelley|Vishal|Laree|Ado|Mona|Lorena|Marco|Jeremy|Joe|Andrew|Lloyd|Mahalaxmi|Niamh|Daniel|Mitzi|Les|Laurence|Levonte|Nuno|Mj|Derek|Susan|Deandre|Nizar|Tanya|Maritza|Gabe|Imtiaz|Nira|Ervin|Maureen|Lalit|Lynwood|Li|Christopher|Min|Liz|Diane|Michaeline|Craig|Marianna|Becky|Leonard|Aj|Jeffrey|Edison|Csm|Clay|Marie|Jae|Bruce|Marcello|Lucille|Megha|Todd|Elizabeth|Angelica|Minette|Lynda|Liton|Carrie|Dennis|Amit|May|B|Laurel|Istiaq|Valerio|Sujesh|Vincent|Charley|Benj|Jeanine|Marcin|Ali|Arnaud|Mirna|Dianne|Namita|Melvin|Geroge|Omar|Wesley|Dominic|Adrian|Tina|Eric|Graciano|Leon|Mario|Brandon|Isabel|Antonio|Liang|Lara|Nadezhda|Navjot|Vicki|Danette|Nikia|Sunil|Leighann|Dustin|Adekunle|Natalia|Taylor|Darryl|Danny|Lorenza|Manny|Dorothy|Maryanne|Tarun|Lou|Oliver|Jay|Carla|Atle|Geoff|Mathew|Brit|Casey|Martijn|Laquita|Aaron|Mahesh|Althea|Lorra|Nina|Tammy|Ellie|Calvin|Marcia|Tamir|Meital|Cheryl|Gordon|Mujie|Marylou|Nicki|Manoj|Mitch|Tania|Hector|Dallan|Carol|Adenton|Nadira|Chengxiang|Naomi|Nirav|Frances|Lorelei|Methila|Ilias|Madhusudan|Jim|Noel|Harsha|Mayra|Masano|Nellie|Mengli|Lalita|Margo|Olga|Chase|Vineet|Mae|Akash|Vandhana|Naren|Ian|Niall|Alicia|Nate|Ben|Bill|Meagan|Madelene|Neha|Louise|Marti|Maarten|Asim|Earlyn|Nobumasa|Maaike|Sylvain|Mack|Maggie|Lester|April|Trent|Leland|Maged|Loren|Lycia|Leandrew|Learcell|Terra|Clara|Lasse|Nadine|Lew|Marquita|Marina|Leah|Miche|Brett|Hao|Lex|Maurice|Natasha|Moni|Melodie|Libby|Elliott|Aprajit|Ning|Lanette|Ivy|Liautaud|Merla|Mihaela|Heather|Nicola|Adger|Alyssa|Marusca|Donald|Mashay|Ashlee|Destine|Victor|Narin|Mathias|Branden|Geoffrey|Manjunath|Alexis|Dahlia|Mayer|Taras|Monte|Igor|Harry|Yonas|Obed|Albert|Darrell|Maxime|Zoe|Leigh|Tal|Thoai|Curtis|Cindy|Evan|Gomathy|Tessa|Elaheh|Marinca|Abby|Veronika|Onetta|Nikki|Mohsen|Edwin|Margie|Mick|Bonnie|Trina|Marilia|Nora|Leonor|Eddie|Gail|Arjan|Lorna|Mengwei|Aray|Ann|Wolfgang|Barb|Mahir|Swapna|Lijuan|Dinesh|Mayur|Marit|Beat|Maricela|Erika|Muhammad|Avi|Nestor|Anchal|Avni|Amber|Jessy|Luz|Midhat|Anita|Nandini|Lola|Nathaniel|Cleo|Jean|Lynette|Mitchell|Lawrence|Liviu|Madelyn|Nabil|Mila|Carson|Marcy|Mohammad|Bobby|Theresa|Lei|Nazim|Laurens|Chetan|Magdalena|Charlotte|Ana|Nissanka|Neil|Glenn|Mari|Miguel|Devin|Courtney|Mora|Jocelyn'.split('|')
	lnames = 'Scearcy|Sachchi|Ohalloran|Smith|Karahalios|Puglisi|Cordero|Pinero|Turcan|Poor|Tanaka|Henderson|Baltzer|Ivy|Jones|Mertens|Oyer|Polin|Lee|Greene|Sanchez|St|Kazi|Glowik|Mccann|Hogberg|Hutchinson|Morse|Hardy|Luke|Kincaid|Ceh|Guerrero|Roe|Vanderwert|Area|Singh|Ho|Koehler|Ask|Oakes|Vega|Sternfeldt|Huddleston|Massa|Interactive|Ruzsbatzky|Miller|Neeley|Posnock|Marando|Bright|Moyers|Walsh|Cataldi|Herbst|Lange|Shepherd|Nelson|Doherty|Willms|Lane|Romashkov|Trudeau|Bancu|Fraga|Wei|Kulkarni|Linkewich|Rouquette|Messer|Naypaue|Giafaglione|Bunting|Ahlersmeyer|Deschene|Viggers|Vadassery|Alves|Wilson|Trueworthy|Mukherjee|Sharp|Thomas|Prabhakar|Moore|Horikawa|Horne|Brostek|Richardson|Lewis|Alberti|Kelso|Mashita|Forsling|Dong|Diaz|Gibbs|Chitturi|Trackwell|Jeanne|Napoleon|Mclau|Craigie|Dacosta|Johnson|Farr|Martinez|Rauscher|Barclay|Webber|Delortlaval|Lin|Rinenbach|Weyand|Syed|Brady|Pathak|Fairchild|Ta|Higgins|Zhang|Kensey|Puthin|Malundas|Marom|Labed|Smagala|Zelenak|Capecelatro|Hambley|Causevic|Simmet|Schneider|Poovaiah|Enge|Maddatu|Wheeler|Henken|Fett|Goldston|Solanki|Arnce|Tamayo|Visa|Labruyere|French|Bennett|Shah|Osborne|Curley|Vaidya|Valachovic|Witters|Terrill|Thompson|Fryer|Price|Fulgieri|Queen|Moradi|Bell|Kort|Gillfoyle|Wosje|Aswal|Chelap|Wie|M.;4831600947|Niziolek|Whitley|Huntington|Drew|Santana|Basch|Simond|Bakke|Massi|Usuda|Mcquade|Rodgers|Kerpovich|Williams|Marciano|Ludeman|Strange|Spano|Hahn|Elgin|Mirkooshesh|Angottiportell|Deet|Pumphrey|Sandler|Vogel|Flynn|De|Wagner|Cheung|Dalberth|Skoog|Benavides|Ginsberg|Woodworth|Roachell|Monfeli|Sadow|Mejean|Song|Smurzynski|Mckee|Hunter|Gabdulov|Arnaboldi|Saxton|Worthy|Asd|Kee|Thigpen|Ormand|Schwartz|Sandberg|Pitner|Achutharaman|Seyot|Mientka|Hougom|Speer|Pearce|Hernandez|Long|Earley|Fulton|Chiavetta|Mcbrayer|Chamarthi|Barag|Kumar|Yang|Casari|Slicer|Lang|Bourgeois|Perry|Spivack|Taylor|Hughes|Seric|Barth|Hayter|Westerdale|Cook|Rico|Fasthoff|Trainor|Kleinman|Harverstick|Greenwell|Grady|Kirkpatrick|Saxon|Ujvari|Glander|Robinson|Goddard|Chen|Kramer|Caracache|Ramer|Baudet|Casner|Jenson|Butz|Hooper|Ramanathan|Marks|Dhawale|Ferguson|Huapaya|Mcdowell|Haehn|Piccolo|Carns|Jeffrey|Gibitz|Hsu|Jindra|Isaev|Gaikwad|Manganaro|Gerbelli|Sisson|Santiago|Izzo|Mills|Wiseen|Cooney|Libby|Miles|Mcgough|Fox|Koch|Rochelle|Mehta|Riffee|Erkok|Gibby|Freitas|Remund|Arones|Penn|Liu|Farkas|Kelkenberg|Samadzadeh|Castillo|Garrett|Cooper|Djuvik|Fishbane|Niedzielski|Kan|Hammond|Kruse|Rees|Leone|Vanbemmel|Ramani|Macdonald|Hall|Kiragu|Folkert|Tremaine|Zachry|Sherpard|Gearo|Richard|Voy|Weinem|Bhatia|Marder|Whittam|Garcia|Brannen|Mcindoe|Nandi|Mcgowen|Orr|Tamsitt|Kingsford|Lillie|Sheehan|Mylexsup|Davis|Yanez|Neal|Spinks|Massimo|Taulbee|Yunus|Maxian|Giuliano|Jorgenson|Sullivan|Obrien|Garcis|Allen|Kowalske|Wirtzberger|Kaiser|Millen|Mclaughlin|Sinclair|Messina|Lins|Robertson|Kindle|Velez|Vin|Argueta|Seltzer|Hayes|Clark|Slocum|Laski|Jim|Fey|Weston|Licata|Hanson|Mohlenkamp|Kos|Bilotti|Popke|Sloss|Campbell|Pham|Eby|Tipps|Walker|Hertzman|Harrell|Jansen|Kumarasamy|Lopez|Lindsley|Silver|Seremeth|Gorelick|Snider|Cauley|Ann|Garmatz|Ashcraft|Pawar|Kain|Coronel|Wilkes|Hinkle|Lloyd|Hassan|Ghangale|Kurtz|Trakic|Gibson|Shaheen|Calkins|Kuhlmann|Nishihara|Skrbin|Vanora|Fitzgerald|Trifler|Arriola|Krishnamurthy|Leleux|Weum|Dunne|Bairstow|Choi|Boyce|Joe|Ploshay|Tibbits|Minkley|Coshurt|Santos|Odonnell|Rios|Burkart|Turner|Parker|Racki|Paliferro|Wcislo|Donchatz|Ford|Ladak|Emmick|Mobed|Quiles|Gagne|Medrano|Hussain|Tejada|Alterson|Anastasia|Eddie|Adams|Motto|Brooks|Sharma|Byrum|Cheng|Kagan|Helman|Kim|Roller|Bordelon|Dozal|Mitchell|Barnes|Hummel|Fenton|Anderson|Reinbold|Dillard|Mattingly|Shcherbina|Mintz|Tullos|Siuda|Maggi|Lucas|Bouchard|Cortes|Dunning|Howard|Gower|Cotter|Kisner|Kennedy|Palacios|Levy|Uppal|Oholendt|Jew|Schultz|Dabrock|Peel|Cls|Deady|Park|Corradini|Sisneros|Hartnett|Nazaredth|Gentile|Hester|Richcreek|Giermak|Kay|Shadle|Pott|Kubey|Chacana|Rangel|York|Cooke|Squire|Roush|Tillman|Kandel|Roy|Sun|Herrmann|Chong|Knudsen|Coomer|Sarkar|Woodward|Banks|Allan|Schiller|Nicholls|Mahmud|Fiala|Horvath|Dangelo|Vickery|Somanathan|Sellier|Alejos|Ellis|Roska|Thibeault|Fuller|Brown|Roach|Bulgajewski|Oztekin|Sabol|Nomellini|Magnier|Berglund|Schau|Gramling|Francisco|Korman|Shubhy|Gossmeyer|Murray|Foster|Blevins|Arias|Soda|Litwin|Solak|Casey|Schmidt|Hartshorn|Deck|Leodoro|Swenson|Luc|Zamudio|Lacoe|Simko|Metz|Pace|Benjamin|Tolwinska|Little|Mcdonough|Lynch|Worley|Funk|Bachtle|Estes|Hennessey|Wurtzel|Jimenez|Pilogallo|Donaldson|Eng|Weiss|Coy|Bockstahler|Nekrasova|Rand|Gagen|Masters|Root|Eldert|Bleiler|Huang|Ryan|Janca|Cozart|Bhatara|Todd|Haylett|Mckinney|Adeniran|Oneill|Zamparini|Lafauce|Hetzel|Boers|Elder|Glaser|Kienzler|Reverendo|Cruse|Salafia|Bossard|Muir|Khanna|Orsatti|Mantheiy|Moorehead|Trevino|Delorme|Gregory|Gratwick|Mooney|Reitan|L|Flachaire|Simpson|Edwards|Humes|Probst|Wood|La|Hardesty|Rogers|Batten|Peifer|Devolt|Tesnovets|Hitchcock|Scarlata|Khot|Bush|Navale|Volper|Schnell|Emmons|Newton|Adkins|Roberts|Romaine|Barker|Louie|Richmond|Stear|Derr|Hallinger|See|Heller|Raveenthran|Bridges|Robison|Caney|Thaves|Darab|Corridore|Haas|Medved|Hain|Chiu|Chalmer|Sirotnak|Lavecchia|Buoniconti|Karpe|Poell|Massicot|Bauer|Augusty|Cfp|Guzman|Zuleta|Dijohnson|Whatley|Zickur|Denton|Mety|Dhani|Ren|Rivas|Chartier|Botuck|Mistry|Rigney|Hough|Rahman|Panagiotou|Bookbinder|Mcnabb|Reddy|Desma|Giampicclo|Granata|Shekleton|Shivaram|Marzan|Abramson|Mack|Hribar|Wolman|Machado|Weispfenning|Adcock|Sugiyama|Manning|Mcclure|Salinas|Yuan|Langer|Metcalf|Cherian|Baamonde|Lolam|Bealhen|Trout|Titkova|Gariti|Lamb|Myhrvold|Peltekian|Londergan|Zdroik|Filkins|Nichols|Dieter|Chaturvedi|Kotsikopoulos|Saqcena|Naranjo|Atkinson|Woodley|Kushner|Thorson|Ropple|Phoenix|Jaganathan|Gomar|Denham|Drelich|Livermore|Burns|Cartwright|Wickum|Kluger|Hockenhull|Heindl|Zak|Shipman|Saple|Besmond|Malone|Caldwell|King|Balfe|Tilton|Van|Iqbal|Shuffler|Berry|Panetta|Mori|Meijer|Mckeever|Grande|Stinson|Swanson|Wong|Gavilondo|Jaffe|Innes|Junker|Strickler|Fouad|Phillips|Stevens|Lemmon|Reinholz|Rogan|Krongold|Gremillon|Phipps|Loyd|Atkins|Downing|Parsons|Stanovich|Folger|Savio|Holmes|Osgood|Harris|Soloski|Galvin|Low|Jamt|Baldwin|Doohen|Dustman|Clopton|Zamora|Austin|Delery|Hansen|Samson|Buddin|Hollander|Xiong|Maultsby|Madore|Fortuna|Heckman|Cooey|Heise|Matsuda|Bent|Kar|Gahan|Wang|Yip|Butts|Lincoln|Dorminy|Golojuch|Florestal|Escarment|Aye|Sheldon|Petrova|Haines|Beaudoin|Watkins|Knuth|Balena|Shay|Bogush|Thomann|Blackwell|Carr|Pochiraju|Rauch|Waldeisen|Harding|Lacroix|Kolber|Horenstein|Hoegerman|Ilfeld|Wnorowski|Jacobs|Burnette|Gatto|Wandell|Anerella|Melara|Deisner|Merchant|Mount|Borchardt|Tschupp|Ciotola|Leung|Frailey|Lemons|Clement|Wattanavirun|Schmidheiny|Harness|Schechter|Gebert|Peralta|Stanley|Sandoval|Rangaswamy|Ranallo|Chrostowski|Wallach|Graham|Goltermann|Crosby|Boschman|Pelta|Szmagala|Fry|Konforti|Garduno|Dolan|Rockwell|Mcgah|Damm|Gebrewold|Benito|Chang|Yeboah|Coleman|Steib|London|Ashby|Schulman|Ferrara|Griffith|Sadrieh|Anetakis|Serrano|Konidaris|Kastenson|Barel|Le|Molina|Peterson|Leddy|Espinal|Cohn|Swamy|Chermiset|Link|Hobson|Pentzke|Shirneshan|Veno|Peters|Warren|Stanfield|Magnus|Grantham|Szabo|Hou|Juncherbenzon|Lara|Marlatt|Millbrooke|Sofastaii|Downer|Matheis|Galati|Olson|Wiederrecht|Quintana|Drozd|Weaver|Russell|Fisher|Dorrian|Morris|Ortiz|Newnam|Piper|Modic|Pfister|Butler|Tschetter|Tibbetts|Mattox|Frank|Curry|Zayas|Alvarez|Arrington|Hanlon|Freedman|Lineberry|Robyn|Morakinyo|Stokkel|Rinear|Zheng|Cutting|Driggers|Adil|Nikumbhe|Farver|George|Gyurko|Riley|Greve|Dreyer|Petschl|Hodzic|Rawe|Vijayakumar|Kang|Drees|Calderone|Alvarado|Watson|Belcher|Chaudhari|Panchal|Carnevale|Ayers|Studinger|D|Latib|Haksar|Oles|Dowland|Borreli|Serravalle|Vincent|Sachdeva|Wallace|Jain|Segal|Aguirre|Salihovic|Antonio|Viau|Marek|Murphy|Barratt|Fischer|Lennon|Mike|Ramaswamy|Defruscio|Hamby|Pallant|Clifton|Chenevert|Stuebe|Bloss|Rowe|Speak|Cupido|Debartolomeis|Katz|Brophy|Myster|Frazier|Olaru|Rojas|Straub|Keenan|Phan|Agresta|Mansour|Fiore|Pucci|Levin|Abrams|Cox|Lockwood|Vangilder|Olshan|Tyus|Murry|Crites|Leonard'.split('|')

	return random.choice(fnames)+' '+random.choice(lnames)

def show_banner():
	global mail_to_verify
	banner = f"""{c.HEAD}
	   __ __              .____________         __   
	  /  V  \\ _____     __| _/\\_  ____ \\_____ _/  |_
	 /  \\ /  \\\\__  \\   / __ |  /  \\   \\/\\__  \\\\   __\\
	/    Y    \\/ A_ \\_/ /_/ |  \\   \\_____/ A_ \\|  |
	\\____A____(______/\\_____|   \\_______(______/__|

		{c.BOLD}MadCat Mailer v2.2{c.END}
		Verification email: {c.BOLD}{mail_to_verify}{c.END}
		If you face any problems or have questions feel free to ask me.
		Telegram: {c.GREEN}{c.BOLD}@freebug{c.END}\n"""
	time.sleep(1)
	for line in banner.split('\n'):
		print(line)
		time.sleep(0.05)
	time.sleep(3)

def read_files():
	global mail_list,smtp_list,mail_list_file,smtp_list_file,mail_body_file,attachment_file
	try:
		mail_list = open(mail_list_file,'r').read().splitlines()
	except:
		exit("Mail list file does not exist")
	try:
		smtp_list = open(smtp_list_file,'r').read().splitlines()
	except:
		exit('Accepted format is "smtp_list.txt" containing host|port|username|password')
	if not os.path.isfile(mail_body_file):
		exit('Please set "mail_body_file"')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

signal.signal(signal.SIGINT, quit)

show_banner()
read_files()
sys.stdout.write('\n'*threads_count)

for i in range(threads_count):
	threads_statuses['thread'+str(i)] = 'no data'

threads_counter = 0
j = 0
mail_que = queue.Queue()
for i in mail_list:
	if j % verify_every == 0:
		mail_que.put(mail_to_verify+';Mark Mayflower;12345678')
	mail_que.put(i)
	j += 1
smtp_que = queue.Queue()
for i in smtp_list:
	smtp_que.put(i)
worker_results = queue.Queue()

time_start = time.time()
total_mails_to_sent = mail_que.qsize()

if not mail_que.qsize() or not smtp_que.qsize():
	exit(f'{c.FAIL}Not enough emails or SMTPs. Empty file?{c.END}')
if threads_count > smtp_que.qsize():
	threads_count = smtp_que.qsize()

for i in range(threads_count):
	worker_thread = threading.Thread(name='thread'+str(i),target=worker_item,args=(mail_que,smtp_que,worker_results,),daemon=True)
	worker_thread.start()
	threads_counter += 1

with alive_bar(total_mails_to_sent,title='Progress:') as bar:
	while True:
		time_takes = round(time.time()-time_start, 1)+0.09
		smtp_left = smtp_que.qsize()
		if not worker_results.empty():
			thread_name, thread_status, mails_sent = worker_results.get()
			if 'sent to' in thread_status:
				bar()
			mails_per_second = round(mails_sent/time_takes, 1)
			threads_statuses[thread_name] = '\b'*10+f'{thread_name}'.rjust(9)+cut_str(f': {thread_status}',100).ljust(105)+f' speed: {mails_per_second} mails/s'
			dbytes_statuses()
		if threads_counter == 0:
			if mail_que.empty():
				mails_per_second = round(total_mails_to_sent/time_takes, 1)
				print('\b'*10+f'{c.GREEN}All done in {time_takes} sec. Speed: {mails_per_second} mails/sec.{c.END}')
				break
			if smtp_que.empty():
				print('\b'*10+f'{c.FAIL}SMTP list exhausted. All tasks terminated.{c.END}')
				break

