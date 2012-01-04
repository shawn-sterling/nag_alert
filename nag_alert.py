#!/usr/bin/python -tt
#
# Copyright (C) 2011  Shawn Sterling <shawn@systemtemplar.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# nag_alert: this program will supress nagios alerts in a very simple
# manner, with no databases or ldap servers required.
#
# The latest version of this code will be found on my github page:
# https://github.com/shawn-sterling

import os
import sys
import time
import smtplib
import subprocess
import re
import tempfile

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

# mode (email or sms). Will use email mode if '@' is detected.
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


def send_sms_mail(email_to, email_message):
    """
        sends a email, truncats to 160 chars. (sms)
    """
    headers = "From %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (email_from, \
        email_to, email_subject)
    mail = smtplib.SMTP("127.0.0.1")
    message = headers + email_message
    if len(message) > 160:
        message = message[0:159]
    mail.sendmail(email_from, email_to, message)
    mail.quit()


def send_sms_direct(sms_number, sms_message):
    """
        sends a sms message directly using gnokii
    """
    if len(sms_message) > 160:
        message = message[0:159]

    full_command = []
    tmp = "%s %s" % (sms_command, sms_number)
    full_command.extend(tmp.split())

#    print full_command
    p = subprocess.Popen(full_command, stdout=subprocess.PIPE,
        stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = p.communicate(input=sms_message)

    for line in output:
        if re.search("Send succeeded", line):
            return True

    return False


def check_last_mail(email_to, email_message):
    """
        finds out last time we emailed a email address, sends if it has been
        more than alert_time in seconds.
    """
    file_name_received = os.path.join(tmp_dir, nag_alert_dir,
        email_to) + ".recv"
    file_name_sent = os.path.join(tmp_dir, nag_alert_dir, email_to) + ".sent"
    try:
        f = open(file_name_sent, "r")
        last_sent = f.read()
        f.close()
    except IOError:
        last_sent = 0

    now = int(time.time())
    if now - int(last_sent) > alert_time:
        # good to send message it's been more than alert_time
        try:
            f = open(file_name_received, "r")
            last_received = f.read()
            f.close()
        except IOError:
            last_received = 0

        if now - int(last_received) > alert_time:
            # send message as is
            if mode == "sms":
                send_sms_direct(email_to, email_message)
            else:
                send_sms_mail(email_to, email_message)
        else:
            # send multiple message
            if mode == "sms":
                send_sms_direct(email_to, multi_message)
            else:
                send_sms_mail(email_to, multi_message)

        new_dir = os.path.join(tmp_dir, nag_alert_dir)
        if not os.path.exists(new_dir):
            try:
                os.makedirs(new_dir)
            except Exception as e:
                print "Can't create dir:%s error:%s" % (new_dir, e)

        try:
            f = open(file_name_sent, "w")
            f.write("%s\n" % now)
            f.close()
        except Exception as e:
            print "Can't write to file:%s error:%e" % (file_name_sent, e)

    try:
        f = open(file_name_received, "w")
        f.write("%s\n" % now)
        f.close()
    except Exception as e:
        print "Can't write to file:%s error:%e" % (file_name_received, e)


def usage():
    """
        prints usage
    """
    print """
nag_alert: reduces nagios alerts

Usage:
nag_alert HOST notification_type host_alias host_state host_output email
or
nag_alert SERVICE notification_type host_alias sv_desc sv_state sv_out email
"""
    sys.exit(2)


def main():
    """
        main program. Test with cmd line options:
SERVICE PROBLEM myhost "test service" WARNING "test alert" number@bla.com
HOST PROBLEM myhost WARNING "test alert" number@bla.com
    """
    if len(sys.argv) < 6:
        usage()
    alert_type = sys.argv[1]
    notification_type = sys.argv[2]
    host_alias = sys.argv[3]

    if alert_type == "HOST":
        host_state = sys.argv[4]
        host_output = sys.argv[5]
        if len(host_output) > 16:
            host_output = host_output[0:15]      # 0:15 = 16 chars max
        email = sys.argv[6]
        if re.search("@", email):
            mode = "email"
        message = "%s : %s is %s (%s)" % (notification_type, host_alias, \
            host_state, host_output)

        if alerts[notification_type] == True:
            check_last_mail(email, message)
    else:
        # alert_type must be SERVICE
        service_desc = sys.argv[4]
        service_state = sys.argv[5]
        service_output = sys.argv[6]
        if len(service_output) > 16:
            service_output = service_output[0:15]

        email = sys.argv[7]
        if re.search("@", email):
            mode = "email"
        message = "%s : %s/%s is %s (%s)" % (notification_type, host_alias, \
            service_desc, service_state, service_output)

        if alerts[notification_type] == True:
            check_last_mail(email, message)


if __name__ == '__main__':
    main()
