from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import ssid
from django import forms
from django.views.decorators.csrf import csrf_exempt
from netmiko import ConnectHandler
import copy
import paramiko,time,pexpect


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
    if request.method == 'POST':
        ssid_name = request.POST.get('ssid')
        ssid_status=request.POST.get('status')
        response_data = {}
        a = ssid.objects.get(name=ssid_name)
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
    username = 'mgmt'
    password = 'Ve7petrU'
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_conn_pre.connect(device_ip, username=username, password=password, look_for_keys=False, allow_agent=False)
    if vendor == 'cisco':
        remote_conn = remote_conn_pre.invoke_shell()
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
        if state==0:
            remote_conn.send('config wlan disable {}\n'.format(int(wlan_id)))
        if state==1:
            remote_conn.send('config wlan enable {}\n'.format(int(wlan_id)))
        time.sleep(2)
        remote_conn.close()
    elif vendor=='aruba':
        time.sleep(1)
        remote_conn = remote_conn_pre.invoke_shell()
        remote_conn.send("conf t\n")
        time.sleep(1)
        remote_conn.send("wlan ssid-profile wcm_prod_aruba\n")
        time.sleep(1)
        if state == 0:
            remote_conn.send("disable\n")
            time.sleep(1)
        else:
            remote_conn.send("enable\n")
            time.sleep(1)
        remote_conn.send("end\n")
        time.sleep(1)
        remote_conn.send("commit apply\n")
        time.sleep(1)
        remote_conn.send("logout\n")
        time.sleep(1)
        remote_conn.close()
    elif vendor=="mikrotik":
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


