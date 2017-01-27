from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import ssid
from django import forms
from django.views.decorators.csrf import csrf_exempt
from netmiko import ConnectHandler
import copy
import paramiko,time,pexpect,requests,json,logging
from datetime import datetime


class ssidForm(forms.ModelForm):
   class Meta:
       model=ssid
       fields=('name','status')
       widgets = {
           'text': forms.TextInput(
               attrs={'id': 'post-text', 'required': True, 'placeholder': 'Say something...'}
           ),
       }


all_list= []
for i in ssid.objects.all():
    all_list.append(i.name)


@csrf_exempt
def index(request):
    ctx = {}
    ctx['latest'] = ssid.objects.order_by('-vendor')
    ctx['servers']=enumerate(list(ssid.objects.values_list('web', flat=True).distinct().order_by('web')))
    if request.method == 'POST':
        ssid_name = request.POST.get('ssid')
        ssid_status=request.POST.get('status')
        response_data = {}
        a = ssid.objects.get(name=ssid_name)
        #print('View received POST from Ajax',ssid_name)
        if ssid_status=='up':
            a.status=1
            a.save()
            change(a.name,a.ip,a.vendor,a.status)
        if ssid_status=="down":
            a.status = 0
            a.save()
            change(a.name,a.ip, a.vendor,a.status)
        response_data['result'] = 'Backend: SSID switched successfully!'
        response_data['pk'] = a.pk
        response_data['name'] = ssid_name
        response_data['status'] = a.status

        return JsonResponse(response_data)
    else:
        return render(request, 'index.html', ctx)

def change(ssid,device_ip,vendor,state):
    #username = 'mgmt'
    #password = 'Ve7petrU'
    #remote_conn_pre = paramiko.SSHClient()
    #remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #remote_conn_pre.connect(device_ip, username=username, password=password, look_for_keys=False, allow_agent=False)
    if vendor == 'cisco':
        #remote_conn = remote_conn_pre.invoke_shell()
        remote_conn=sshp_shell(device_ip)
        print(ssid,remote_conn)
        remote_conn.send("mgmt\n")
        time.sleep(1)
        remote_conn.send("Ve7petrU\n")
        time.sleep(2)
        remote_conn.send("show wlan summary\n")
        time.sleep(1)
        output = remote_conn.recv(5000)
        wlanlist = output.decode("utf-8").split('\n')[5:]
        for i in wlanlist:
            if ssid in i:
                wlan_id = i.split()[0]
                break
        if state:
            remote_conn.send('config wlan enable {}\n'.format(int(wlan_id)))
        else:
            remote_conn.send('config wlan disable {}\n'.format(int(wlan_id)))
        time.sleep(2)
        remote_conn.close()
    elif vendor=='aruba':
        remote_conn = sshp_shell(device_ip)
        print(ssid,remote_conn)
        time.sleep(1)
        remote_conn.send("conf t\n")
        time.sleep(1)
        remote_conn.send("wlan ssid-profile {}\n".format(ssid))
        time.sleep(1)
        print('Wlan-config Aruba {}'.format(ssid))
        if state:
            remote_conn.send("enable\n")
            print('Wlan-enable Aruba {}'.format(ssid))
            time.sleep(1)
        else:
            remote_conn.send("disable\n")
            print('Wlan-disable Aruba {}'.format(ssid))
            time.sleep(1)
        remote_conn.send("end\n")
        time.sleep(1)
        print('End config Aruba {}'.format(ssid))
        remote_conn.send("commit apply\n")
        time.sleep(1)
        print('Commit config Aruba {}'.format(ssid))
        remote_conn.send("logout\n")
        time.sleep(1)
        print('Logout Aruba {}, {}'.format(ssid,remote_conn))
        remote_conn.close()
    elif vendor=="mikrotik":
        remote_conn_pre = sshp_rcmd(device_ip)
        if state == 0:
            remote_conn_pre.exec_command("/interface wireless disable {}".format(ssid))
            time.sleep(1)
        else:
            remote_conn_pre.exec_command("/interface wireless enable {}".format(ssid))
            time.sleep(1)
        remote_conn_pre.close()
    elif vendor=="ruckus":
        #child = pexpect.spawn('telnet ' +device_ip)
        #child.expect('Please login: ')
        #child.sendline(username)
        #child.expect("Password: ")
        #child.sendline(password)
        #child.expect("ruckus> ")
        #child.sendline('enable force')
        #child.expect("ruckus# ")
        #child.sendline('conf')
        #child.expect(".*config.*")
        #child.sendline("wlan {}".format(ssid))
        #child.expect(".*config-wlan.*")
        #if state == 0:
        #    child.sendline("hide-ssid")
        #    child.expect(".*config-wlan.*")
        #else:
        #    child.sendline("no hide-ssid")
        #    child.expect(".*config-wlan.*")
        #child.sendline("end\n")
        remote_conn = remote_conn_pre.invoke_shell()
        remote_conn.send("\n")
        time.sleep(1)
        remote_conn.send("{}\n".format(username))
        remote_conn.send("{}\n".format(password))
        time.sleep(1)
        remote_conn.send("enable force\n")
        remote_conn.send("conf\n")
        time.sleep(1)
        remote_conn.send("wlan {}\n".format(ssid))
        time.sleep(1)
        if state == 0:
            remote_conn.send("hide-ssid\n")
            time.sleep(1)
        else:
            remote_conn.send("no hide-ssid\n")
            time.sleep(1)
        remote_conn.send("end\n")
        time.sleep(1)
        remote_conn.close()
    elif vendor=="openwrt":
        remote_conn = remote_conn_pre.invoke_shell()
        remote_conn.send("sudo -s\n")
        time.sleep(1)
        remote_conn.send('{}\n'.format(password))
        time.sleep(1)
        if state == 0:
            remote_conn.send('uci set wireless.@wifi-device[0].disabled=1; uci commit wireless; wifi\n')
            time.sleep(1)
        else:
            remote_conn.send('uci set wireless.@wifi-device[0].disabled=0; uci commit wireless; wifi\n')
            time.sleep(1)
        remote_conn.close()
    elif vendor=="meraki":
        murl='https://n150.meraki.com/api/v0/organizations/616518/networks/N_647392446434529213/ssids/0'
        headers = {
            'X-Cisco-Meraki-API-Key': 'b21b5c3bfa37f5d920831f11775a321c077e71d1',
            'Content-Type': 'application/json'
        }
        if state==0:
            putdata = {'enabled': False}
        else:
            putdata = {'enabled': True}
        dashboard = requests.put(murl, data=json.dumps(putdata), headers=headers)
        print(dashboard.text)
    #elif vendor=="bred":


def sshp_shell(device_ip):
    username = 'mgmt'
    password = 'Ve7petrU'
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_conn_pre.connect(device_ip, username=username, password=password, look_for_keys=False, allow_agent=False)
    remote_conn = remote_conn_pre.invoke_shell()
    remote_conn.keep_this = remote_conn_pre
    return remote_conn

def sshp_rcmd(device_ip):
    username = 'mgmt'
    password = 'Ve7petrU'
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_conn_pre.connect(device_ip, username=username, password=password, look_for_keys=False, allow_agent=False)
    remote_conn_pre.keep_this = remote_conn_pre
    return remote_conn_pre