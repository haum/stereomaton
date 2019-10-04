<?php

define ('CONFIG_FILE', 'config.conf');

/// Interface for Camera Connection
$CAMERA_IFACE = '';

/// Interface for Access Point
$AP_IFACE = '';

/// Interface for Local Network
$LOCAL_IFACE = '';


/// Run Camera Connection
function Camera_run($iface, $ssid, $pass) {
	Camera_stop();

	echo "Starting Camera Connection on $iface\n";

	shell_exec("sudo ifconfig $iface up");

	shell_exec("sudo iwconfig $iface power off");

	/// if OSMO pass is empty - use default
	if ($pass == "") {
		echo "OSMO pass is empty, using default pass\n";
		$pass = "12341234";
	}

	/// if OSMO SSID is empty - search any Osmo
	if ($ssid == "") {
		echo "OSMO SSID is empty. Searching any Osmo...\n";

		$all_ssid_text = shell_exec("iwlist $iface scan");
		$all_ssid_array = explode("\n", $all_ssid_text);

		$new_ssid = "";

		for ($i = 0; $i < sizeof($all_ssid_array); $i++) {
			if (strpos($all_ssid_array[$i], 'ESSID:"OSMO')) {
				$new_ssid = $all_ssid_array[$i];

				/// Replace multiple spaces to one
				$new_ssid = preg_replace('!\s+!', ' ', $new_ssid);

				/// Remove "ESSID:", spaces, quotes
				$new_ssid = trim($new_ssid);
				$new_ssid = str_replace('ESSID:', '', $new_ssid);
				$new_ssid = str_replace('"', '', $new_ssid);
				echo 'Found OSMO: ' . $new_ssid . "\n";

				break;
			}
		}

		$ssid = $new_ssid;
	}

	/// If still no ssid - exit
	if ($ssid == "") {
		echo "Osmo not found\n";
		return;
	} else {
		echo "Using Osmo ssid $ssid pass $pass\n";
	}

	/// Save Camera ssid
	shell_exec("echo $ssid > /run/camera.ssid");

	/// Save Camera iface name
	shell_exec("echo $iface > /run/camera.iface");

	KillProcess('wpa_supplicant', $iface);
	@unlink('/var/run/' . $iface);

	/// Save config for network to temp file
	@unlink("/run/$iface.conf");
	file_put_contents("/run/$iface.conf", "country=00\n");
	shell_exec('wpa_passphrase "' . $ssid . '" "' . $pass . '" >> /run/' . $iface . '.conf');

	/// Start Wlan connection
	shell_exec('sudo wpa_supplicant -B -i ' . $iface . ' -D nl80211,wext -c /run/' . $iface . '.conf');

	/// Start DHCP client
	KillProcess('dhclient', $iface);
	shell_exec('sudo dhclient ' . $iface . ' -sf /etc/dhcp/noroute -nw');
}

/// Stop Camera Connection
function Camera_stop() {
	$iface = trim(@file_get_contents('/run/camera.iface'));
	@unlink('/run/camera.iface');
	if ($iface == "") return;
	echo "Stopping Camera Connection on $iface\n";

	@unlink('/run/camera.ssid');

	KillProcess('wpa_supplicant', $iface);
	@unlink('/var/run/' . $iface);
}

function Camera_getCurrentSsid () {
	return trim(@file_get_contents('/run/camera.ssid'));
}

function Camera_clearCurrentSsid () {
	@unlink('/run/camera.ssid');
}


/// Run Access Point
function AP_run ($iface, $mode, $channel, $ssid, $pass, $country_code) {
	$HOSTAPD_CONFIG = '/run/hostapd.conf';

	AP_stop();

	echo "Starting Access point on $iface ssid=$ssid pass=$pass mode=$mode channel=$channel country_code=$country_code\n";

	/// Save AP iface name
	shell_exec("echo $iface > /run/ap.iface");

	/// Copy sample config file to /run
	shell_exec('cp /etc/hostapd/hostapd.conf ' . $HOSTAPD_CONFIG);

	/// Set params
	SetParams($HOSTAPD_CONFIG, [ ['interface', $iface], ['hw_mode', $mode], ['channel', $channel], ['ssid', $ssid], ['wpa_passphrase', $pass], ['country_code', $country_code] ] );

	/// Configure interface
	shell_exec("sudo ifconfig $iface 192.168.50.1/24 up");
	shell_exec("sudo iwconfig $iface power off");
	/// Kill old hostapd
	shell_exec('sudo killall -q hostapd');
	/// Start new hostapd
	shell_exec('sudo /usr/sbin/hostapd -B -P /run/hostapd.pid ' . $HOSTAPD_CONFIG);

	//shell_exec('sudo iw dev ' . $iface . ' set power_save off > /dev/null 2>&1');
}

/// Stop Access Point
function AP_stop () {
	echo "Stopping Access Point\n";

	/// Kill hostapd
	shell_exec('sudo killall -q hostapd');
}


/// Run Local Network Connection
function LAN_run($iface, $ssid, $pass) {
	LAN_stop();

	# check interface
	$retval = -1;
	exec("ifconfig $iface", $retarr, $retval);
	if ($retval != 0) {
	    echo "Interface $iface not found\n";
	    return false;
	}

	echo "Starting Local Network Connection on $iface\n";

	shell_exec("sudo ifconfig $iface up");
	shell_exec("sudo iwconfig $iface power off");

	/// Save Local iface name
	shell_exec("echo $iface > /run/local.iface");

	KillProcess('wpa_supplicant', $iface);
	@unlink('/var/run/' . $iface);

	/// Save config for network to temp file
	@unlink("/run/$iface.conf");
	file_put_contents("/run/$iface.conf", "country=00\n");
	shell_exec('wpa_passphrase "' . $ssid . '" "' . $pass . '" >> /run/' . $iface . '.conf');
	shell_exec('cat /etc/wpa_networks >> /run/' . $iface . '.conf');
	
	/// Start Wlan connection
	shell_exec('sudo wpa_supplicant -B -i ' . $iface . ' -D nl80211,wext -c /run/' . $iface . '.conf');

	/// Start DHCP client
	KillProcess('dhclient', $iface);
	shell_exec('sudo dhclient ' . $iface . ' -nw');

	//shell_exec('sudo iw ' . $iface . ' set power_save off');
	return true;
}

/// Run Local Network Connection
function LAN_stop() {
	$iface = trim(@file_get_contents('/run/local.iface'));
	@unlink('/run/local.iface');
	if ($iface == "") return;
	echo "Stopping Local Network Connection on $iface\n";

	KillProcess('wpa_supplicant', $iface);
	@unlink('/var/run/' . $iface);
}



/// Change params in any text config file
function SetParams($file, $params) {
	/// load file content
	$content = file($file);

	/// search params
	for ($i = 0; $i < sizeof($content); $i++) {
		foreach ($params as $k => $v) if (strpos($content[$i], $v[0].'=') === 0) $content[$i] = $v[0].'=' . $v[1] . "\n";
	}

	/// save changes
	file_put_contents($file, $content);
}

function GetConfig () {
	return @file(CONFIG_FILE);
}

/// Get param from any text config file
function GetParam($content, $param) {
	/// search param
	for ($i = 0; $i < sizeof($content); $i++) {
		if (strpos($content[$i], $param.'=') === 0) {
			$tmp = explode('=', $content[$i]);
			$result = trim($tmp[1]);
			$result = str_replace('"', '', $result);
			return $result;
		}
	}
}


/// Kill all processes where some string presents in cmdline
function KillProcess ($name, $param) {
	$procs = shell_exec('ps -ax');
	$array = explode("\n", $procs);

	/// Search processes
	for ($i = 0; $i < sizeof($array); $i++) {

		/// if process found
		if (strpos($array[$i], $name) !== FALSE) {

			/// if param found in cmdline
			if (strpos($array[$i], $param) !== FALSE) {

				/// add leading space
				$string = " " . $array[$i];

				/// Replace multiple spaces to one
				$string = preg_replace('!\s+!', ' ', $string);

				/// Now get proc ID from string
				$tmp = explode(' ', $string);
				$PID = $tmp[1];

				/// Kill this process
				shell_exec('sudo kill ' . $PID);
			}
		}
	}
}

?>
