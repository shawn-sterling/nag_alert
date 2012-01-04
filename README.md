# Introduction

Nag\_Alert is a simple script to reduce the amount nagios alerts (for sms users). It sends via direct sms (via gnokii) or via a email sms address.

# Requirements

* A working nagios / incinga server
* Python 2.4 or later

Optional (if you want to send direct SMS)
* Working gnokii (or gsm-tools, or gammu)

# License

Nag\_Alert is released under the [GPL v2](http://www.gnu.org/licenses/gpl-2.0.html).

# Documentation

How it works
------------

nag\_alert creates/checks two files for every nagios alert received.
* /tmpdir/email@address.com.sent (updated whenever we send a email)
* /tmpdir/email@address.com.recv (updated whenever we receive a alert from nagios)

(tmpdir/smsnumber.sent if it's a sms number)

Inside the files is the unix time stamp from when the alert was recieved.

It only sends the message if it hasn't sent a message in the last alert\_time seconds (15 minutes by default).

If the time in the .recv file is less than alert\_time seconds old when we send the alert out
we send the multiple alert string instead of the nagios message.

Warning
-------

This gives no preference on alerts. First alert every 15 mins gets sent.
This could eat your recovery alerts as well. Which is fine for my organization
because any alert means go check nagios.

Target Audience
---------------

The target audience of nag\_alert is people who us a sms email address (5551212@myprovider.com) or sending sms directly via gnokii.

The goal of nag\_alert is to reduce the amount of alerts 1 person can get every X minutes (15 minutes by default). Ideally this is done with configuring your nagios to have lovely host and service dependencies, but if you don't have them setup just right (or even if you do) you may be in for a flood of alerts to your phone. In my organization any SMS alert means go check nagios. So if there are multiple alerts waiting, rather than try and sort be priority or server type we just change the message to a multiple alert message (which you can set at the top of the script).

In addition there is the option to disable specific types of alerts (which is only useful if you want to disable ACKNOWLEDGEMENT, or if you want FLAPPINGSTART but not FLAPPINGSTOP) as everything else is better to be setup at the nagios host/service config. However if you want to be sure that SMS message are going to disable all of a particular notification\_type this will happily do it.

A note on wanting flappingstart and not flappingstop. When I get paged at 5 am because something is flapping, I fix the problem, and go back to bed at 5:30. I don't want a SMS at 6:00 to tell me that flapping has stopped, nor do I want to disable flapping notification for the service then remember to have to turn it back on later (usually for me due to say a web server being flaky a couple hundred website checks will be flapping).

# Installation


(1) Modify the top of the script
--------------------------------

You will need to change the top of the script to specify your tmp directory, and how long you want to wait between alerts. This is commented in the file but in case you are blind here it is:

<pre>
############################################################
##### You will likely need to change some of the below #####

# directory to write tmp files to
tmp_dir = "/opt/nagios/tmp"

# tmp files will be written to tmp_dir/nag_alert_dir
nag_alert_dir = "nag_alert"

# time in seconds between notifications per email address
alert_time = 900

# message to send when there are multiple alerts
multi_message = "You have multiple alerts in nagios, please check nagios ASAP."

# mode (email or sms), if the email has a '@' we use email mode anyway.
mode = "sms"

# email settings (only used if mode = email)
email_subject = "ALERT"
email_from = "nagios@my.domain.com"

# sms_command (only used if mode = sms, phone number appended to end)
sms_command = "sudo /usr/bin/gnokii --config /etc/gnokiirc --sendsms"

# What nagios alerts we want to receive globally.

alerts = {
    "PROBLEM": True,
    "RECOVERY": True,
    "ACKNOWLEDGEMENT": True,
    "FLAPPINGSTART": True,
    "FLAPPINGSTOP": True,
    "FLAPPINGDISABLED": True,
    "DOWNTIMESTART": True,
    "DOWNTIMESTOP": True,
    "DOWNTIMECANCELLED": True
}

##### You should stop changing things unless you know what you are doing #####
##############################################################################
</pre>

Consult the nagios documentation on what types of notifications you want or don't want.


(2) Test the script
-------------------

To test the script manually use:

<pre>
Email:
./nag_alert.py SERVICE PROBLEM myhost "test service" WARNING "test alert" number@my-sms-gateway.com
./nag_alert.py HOST PROBLEM myhost WARNING "test alert" number@my-sms-gateway.com

sms:
./nag_alert.py SERVICE PROBLEM myhost "test service" WARNING "test alert" 5551212
./nag_alert.py HOST PROBLEM myhost WARNING "test alert" number@bla.com 5551212
</pre>

Make sure the script is working manually before you start messing with nagios.


(3) Modify your nagios configs
------------------------------

You will need to modify your nagios configuration files. Find your notify-host-by-email and notify-service-by-email commands and modify to look like this:

#### NOTE: Your libexec dir may be different, or you may decide to put nag_alert.py somewhere else. Adjust as needed.
<pre>
define command {
   command_name             notify-host-by-email
   command_line             /opt/nagios/libexec/nag_alert.py HOST "$NOTIFICATIONTYPE$" "$HOSTALIAS$" "$HOSTSTATE$" "$HOSTOUTPUT$" "$CONTACTEMAIL$"
}

define command {
   command_name             notify-service-by-email
   command_line             /opt/nagios/libexec/nag_alert.py SERVICE "$NOTIFICATIONTYPE$" "$HOSTALIAS$" "$SERVICEDESC$" "$SERVICESTATE$" "$SERVICEOUTPUT$" "$CONTACTEMAIL$"
}

OR SMS via:

define command {
   command_name             notify-host-by-sms
   command_line             /opt/nagios/libexec/nag_alert.py HOST "$NOTIFICATIONTYPE$" "$HOSTALIAS$" "$HOSTSTATE$" "$HOSTOUTPUT$" "$CONTACTPAGER$"
}

define command {
   command_name             notify-service-by-sms
   command_line             /opt/nagios/libexec/nag_alert.py SERVICE "$NOTIFICATIONTYPE$" "$HOSTALIAS$" "$SERVICEDESC$" "$SERVICESTATE$" "$SERVICEOUTPUT$" "$CONTACTPAGER$"
}

</pre>


# Contributing

I'm open to any feedback / patches / suggestions.

I'm still learning python so any python advice would be much appreciated.

Shawn Sterling shawn@systemtemplar.com
