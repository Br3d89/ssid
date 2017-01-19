from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import ssid
from django import forms
from django.views.decorators.csrf import csrf_exempt
from netmiko import ConnectHandler
import copy
import paramiko,time


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
    remote_conn = remote_conn_pre.invoke_shell()
    if vendor == 'cisco':
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
    elif vendor=='aruba':
        time.sleep(1)
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


