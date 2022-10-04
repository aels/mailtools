<?php

// ~~~~ mail validation script ~~~~~~~~~~~~~~~
// ~~~~ VALIDOL v1.1 ~~~~~~~~~~~~~~~~~~~~~~~~~
// ~~~~ https://github.com/aels/mailtools ~~~~
// ~~~~ contact: https://t.me/freebug ~~~~~~~~

if( empty($argv[1]) ) {
	die("Usage:\nphp {$argv[0]} file1,file2,file3");
}

include('vendor/autoload.php');
$db = new \IP2Location\Database('ip2location.bin', \IP2Location\Database::MEMORY_CACHE);

$bad_users = "/customer|scanner|apps|service|info|sales|admin|director|^hr$|finance|contact|support|security|mail|manager|abuse|job|billing|home|account|report|office|about|help|webmaster|confirm|reply|tech|marketing|feedback|newsletter|orders|verification|calendar|regist|survey|excel|submission|contracts|invite|hello|staff|community|fax|twitter|postmaster|found|catch|test/i";
$bad_zones = "/(\.us|\.gov|\.mil|\.edu)$/i";
$bad_isps = "/localhost|invalid|proofpoint|perimeterwatch|securence|techtarget|cisco|spiceworks|gartner|fortinet|retarus|checkpoint|fireeye|mimecast|forcepoint|trendmicro|acronis|sophos|sonicwall|cloudflare|trellix|barracuda|security|clearswift|trustwave|broadcom|helpsystems|zyxel|mdaemon|mailchannels|cyren|opswat|duocircle|uni-muenster|proxmox|censornet|guard|indevis|n-able|plesk|spamtitan|avanan|ironscales|mimecast|trustifi|shield|barracuda|essentials|libraesva/i";
$bad_isps2 = "/virus|bot|trap|pot|lab|virtual|vm|research|abus|security|filter|junk|rbl|ubl|spam|black|list|bad|free|brukalai|metunet|excello/i";
$bad_title = "/<title>[^<]*(security|spam|filter|antivirus)[^<]*</i";

function red($str) {
	return "\033[91m".$str."\033[0m";
}

function orange($str) {
	return "\033[93m".$str."\033[0m";
}

function green($str) {
	return "\033[92m".$str."\033[0m";
}

function get_top_host($str) {
	$str_arr = explode('.', $str);
	return implode('.', array_slice($str_arr, strlen(array_slice($str_arr, -2, 1)[0])<4?-3:-2));
}

$filenames = explode(',', $argv[1]);

foreach ($filenames as $filename) {

	$filename_ext = @end(explode('.', $filename));
	$filename_valid = str_replace('.'.$filename_ext, '_validated.'.$filename_ext, $filename);
	$filename_bad = str_replace('.'.$filename_ext, '_bad.'.$filename_ext, $filename);

	$lines = file($filename);
	$goods = array();
	$i = 0;

	foreach ($lines as $line) {

		echo $i++.": ";

		$line = trim($line);
		preg_match("/([\w._-]+@[\w.-]+\.[\w]{2,5})/i", $line, $matches);

		if( empty($matches[1]) ) {
			continue;
		}
		$email = $matches[1];
		$user = explode('@', $email)[0];
		$host = explode('@', $email)[1];

		if( preg_match($bad_users, $user) ) {
			echo str_replace($user, red($user), $line)."\n";
			file_put_contents($filename_bad, $line.": bad username\n", FILE_APPEND);
			continue;
		}
		if( preg_match($bad_zones, $host) ) {
			echo str_replace($host, red($host), $line)."\n";
			file_put_contents($filename_bad, $line.": bad zone\n", FILE_APPEND);
			continue;
		}
		if( !getmxrr($host, $mx_hosts) || $mx_hosts[0]=='' ) {
			echo $line.": ".red('no mx')."\n";
			file_put_contents($filename_bad, $line.": no mx records\n", FILE_APPEND);
			continue;
		}
		if( !in_array(get_top_host($mx_hosts[0]), $goods) ) {
			foreach ($mx_hosts as $mx_host) {
				if( preg_match($bad_isps, $mx_host) || preg_match($bad_isps2, $mx_host) ) {
					echo $line.": ".red($mx_host)."\n";
					file_put_contents($filename_bad, $line.": $mx_host\n", FILE_APPEND);
					break;
				}
				$mx_ip = gethostbyname($mx_host);
				$records = $db->lookup($mx_ip, \IP2Location\Database::ALL);
				$mx_isp = $records['isp']??'';
				if( preg_match($bad_isps, $mx_isp) || preg_match($bad_isps2, $mx_isp) ) {
					echo $line.": ".red($mx_isp)."\n";
					file_put_contents($filename_bad, $line.": $mx_isp\n", FILE_APPEND);
					break;
				}
			}
			if( preg_match($bad_isps, $mx_host) || preg_match($bad_isps2, $mx_host) || preg_match($bad_isps, $mx_isp) || preg_match($bad_isps2, $mx_isp) ) {
				continue;
			}
			@$host_reverse = gethostbyaddr(gethostbyname($host));
			if( preg_match($bad_isps2, $host_reverse) ) {
				echo $line.": ".red($host_reverse)."\n";
				file_put_contents($filename_bad, $line.": $host_reverse\n", FILE_APPEND);
				continue;
			}
			$mx_top_host = get_top_host($mx_host);
			$ctx = stream_context_create(array('http'=>array('timeout'=>1)));
			if( $mx_top_host != $mx_host &&
				preg_match($bad_title, @file_get_contents("https://".$mx_top_host, false, $ctx))
			) {
				echo $line.": ".red($mx_top_host." - security company")."\n";
				file_put_contents($filename_bad, $line.": $mx_top_host - security company\n", FILE_APPEND);
				continue;
			}
			$goods[] = get_top_host($mx_host);
		}
		echo $line.": ".green($mx_hosts[0])."\n";
		file_put_contents($filename_valid, $line."\n", FILE_APPEND);
	}
}
