from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import ssid
from django import forms
from django.views.decorators.csrf import csrf_exempt
import copy
import paramiko,time,pexpect,requests,json,logging,threading
from datetime import datetime
from multiprocessing import Process


class ssidForm(forms.ModelForm):
   class Meta:
       model=ssid
       fields=('name','status')
       widgets = {
           'text': forms.TextInput(
               attrs={'id': 'post-text', 'required': True, 'placeholder': 'Say something...'}
           ),
       }


ssh_username = 'mgmt'
ssh_password = 'Ve7petrU'
ssid_status=[]





@csrf_exempt
def index(request):
    all_list = list(ssid.objects.values_list('name', flat=True))
    all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
    global ssid_status
    ssid_status=[]
    errors=[]
    ctx = {}
    ctx['all_up_ssids']=all_up_ssids
    ctx['latest'] = ssid.objects.order_by('-vendor')
    ctx['servers']=enumerate(list(ssid.objects.values_list('web', flat=True).distinct().order_by('web')))
    ctx['ok']='Run'
    if request.method == 'POST':
        up_new=json.loads(request.POST.get('up'))
        down_new=json.loads(request.POST.get('down'))
        rcv_ssids=up_new+down_new
        ip_list=set(ssid.objects.values_list('ip', flat=True).filter(name__in=rcv_ssids))
        process_list=[]
        for i in ip_list:
            vendor = list(set(ssid.objects.values_list('vendor', flat=True).filter(ip=i)))[0]
            ssid_objects=ssid.objects.filter(ip=i, name__in=rcv_ssids) #all ssids within device
            p=(threading.Thread(target=globals()['{}'.format(vendor)],args=(up_new, down_new, ssid_objects, i, ssid_status,errors)))
            #p = Process(target=globals()['{}'.format(vendor)], args=(up_new, down_new, ssid_objects, i, ssid_status))
            p.start()
            process_list.append(p)
        for i in process_list:
            print('Starting ', i)
            #i.start()
            i.join()
            #if vendor == 'cisco':
            #    cisco(up_new,down_new,ssid_objects,i,ssid_status)
            #elif vendor == 'aruba':
            #    aruba(up_new, down_new, ssid_objects, i, ssid_status)
            #elif vendor == 'ruckus':pass
        all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
        return JsonResponse({'all_up_ssids':all_up_ssids,'errors':errors})
    else:
        return render(request, 'index.html', ctx)


def cisco(up_new, down_new, ssid_objects, i, ssid_status,errors):
    print('Executing SSH command cisco')
    try:
        child = pexpect.spawn('ssh -l {} -oStrictHostKeyChecking=no {}'.format(ssh_username, i))
    #except pexpect.exceptions.TIMEOUT as err:
    #    errors.append(err)
    #    print(err)
    #child = pexpect.spawn('telnet {}'.format(i))
        print('Waiting for Username:','Before:', child.before,'After:', child.after)
        child.expect('User:')
        child.sendline(ssh_username)
        print('Waiting for Password:', 'Before:', child.before, 'After:', child.after)
        child.expect('Password:')
        child.sendline(ssh_password)
        print('Starting for loop and waiting for >', 'Before:', child.before, 'After:', child.after)
        for m in ssid_objects:
            print('Started for loop, waiting for WLC symbols', 'Before:', child.before, 'After:', child.after)
            child.expect("WLC")
            print('Received expected >')
            if m.name in up_new:
                child.sendline('config wlan enable {}'.format(m.wlan_id))
                m.status = 1
            else:
                child.sendline('config wlan disable {}'.format(m.wlan_id))
                m.status = 0
            m.save()
            ssid_status.append(m.name)
        child.expect('>',timeout=60)
        child.sendline('logout')
        child.expect('(y/N)')
        child.sendline('y')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(err)
        print('Error Br3d',err)


def aruba(up_new, down_new, ssid_objects, i, ssid_status,errors):
    print('Eceuting ssh command aruba')
    child = pexpect.spawn('ssh -l {} {}'.format(ssh_username,i))
    child.expect(":")
    child.sendline("{}\r".format(ssh_password))
    child.expect("#")
    child.sendline('conf\r')
    child.expect('#')
    for m in ssid_objects:
        child.sendline('wlan ssid-profile {}\r'.format(m.wlan_id))
        child.expect('#')
        if m.name in up_new:
            child.sendline('enable\r')
            child.expect('#')
            m.status = 1
        else:
            child.sendline('disable\r')
            child.expect('#')
            m.status = 0
        m.save()
        ssid_status.append(m.name)
    child.sendline('end\r')
    child.expect('#')
    child.sendline('commit apply\r')
    child.expect('#')
    child.sendline('logout')
'''
def cisco(up_new,down_new,ssid_objects,i,ssid_status):
    #child = pexpect.spawn('ssh -l {} {}'.format(ssh_username, i))
    child = pexpect.spawn('telnet {}'.format(i))
    child.expect(':')
    child.sendline(ssh_username)
    child.expect(':')
    child.sendline(ssh_password)
    for m in ssid_objects:
        child.expect(">")
        if m.name in up_new:
            child.sendline('config wlan enable {}'.format(m.wlan_id))
            m.status = 1
        else:
            child.sendline('config wlan disable {}'.format(m.wlan_id))
            m.status = 0
        m.save()
        ssid_status.append(m.name)
    child.expect('>')
    child.sendline('logout')
    child.expect('(y/N)')
    child.sendline('y')


def aruba(up_new,down_new,ssid_objects,i,ssid_status):
    child = pexpect.spawn('telnet {}'.format(i))
    child.expect(":")
    child.sendline("{} + \r".format(ssh_username))
    child.expect(":")
    child.sendline("{} + \r".format(ssh_password))
    child.expect("#")
    child.sendline('conf' + '\r')
    child.expect('#')
    for m in ssid_objects:
        child.sendline('wlan ssid-profile {} \r'.format(m.wlan_id))
        child.expect('#')
        if m.name in up_new:
            child.sendline('enable \r')
            child.expect('#')
            m.status = 1
        else:
            child.sendline('disable \r')
            child.expect('#')
            m.status = 0
        m.save()
        ssid_status.append(m.name)
    child.sendline('end' + '\r')
    child.expect('#')
    child.sendline('commit apply' + '\r')
    child.expect('#')
    child.sendline('logout')



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
'''


def detail(request,name):
    a = ssid.objects.get(name=name)
    return render(request, 'ssid/detail.html', {'instance': a})


def status(request):
    print('Status request')
    print(ssid_status)
    return JsonResponse({'ssid_status': ssid_status})