from django.shortcuts import render,redirect
from django.http import JsonResponse, HttpResponse
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
down_status=[]


@csrf_exempt
def ssid_update(request):
    #all_list = list(ssid.objects.values_list('name', flat=True))
    all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
    global ssid_status
    ssid_status = []
    errors = []
    #ctx = {}
    #ctx['all_up_ssids'] = all_up_ssids
    #ctx['latest'] = ssid.objects.order_by('-vendor')
    #ctx['servers'] = enumerate(list(ssid.objects.values_list('web', flat=True).distinct().order_by('web')))
    #ctx['ok'] = 'Run'
    if request.method == 'POST':
        up_new = json.loads(request.POST.get('up'))
        down_new = json.loads(request.POST.get('down'))
        timeout_value = json.loads(request.POST.get('timer'))
        print(timeout_value)
        rcv_ssids = up_new + down_new
        ip_list = set(ssid.objects.values_list('ip', flat=True).filter(name__in=rcv_ssids))
        process_list = []
        for i in ip_list:
            vendor = list(set(ssid.objects.values_list('vendor', flat=True).filter(ip=i)))[0]
            ssid_objects = ssid.objects.filter(ip=i, name__in=rcv_ssids)  # all ssids within device
            p = (threading.Thread(target=globals()['{}'.format(vendor)],
                                  args=(up_new, down_new, ssid_objects, i, ssid_status, errors)))
            # p = Process(target=globals()['{}'.format(vendor)], args=(up_new, down_new, ssid_objects, i, ssid_status))
            p.start()
            if (len(down_new) == 0):
                threading.Timer(timeout_value, globals()['{}'.format(vendor)],
                                args=(up_new, down_new, ssid_objects, i, ssid_status, errors, 1)).start()
            process_list.append(p)
        for i in process_list:
            print('Starting ', i)
            # i.start()
            i.join()
            # if vendor == 'cisco':
            #    cisco(up_new,down_new,ssid_objects,i,ssid_status)
            # elif vendor == 'aruba':
            #    aruba(up_new, down_new, ssid_objects, i, ssid_status)
            # elif vendor == 'ruckus':pass
        all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
        return JsonResponse({'all_up_ssids': all_up_ssids, 'errors': errors})
    else:
        index(request)
        #return render(request, 'index.html', ctx)


def cisco(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    print('Executing SSH command cisco t=', t)
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        child.expect('User:')
        child.sendline(ssh_username)
        child.expect('Password:')
        child.sendline(ssh_password)
        for m in ssid_objects:
            child.expect(">")
            if (m.name in up_new) and t == 0:
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
        print('Backend success')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(err)
        # print('Error Br3d',err)
        print('Br3d pexpect time error')


def aruba(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    print('Eceuting ssh command aruba')
    child = pexpect.spawn('ssh -l {} {} -o StrictHostKeyChecking=no'.format(ssh_username, i))
    child.expect(":")
    child.sendline("{}\r".format(ssh_password))
    child.expect("#")
    child.sendline('conf\r')
    child.expect('#')
    for m in ssid_objects:
        child.sendline('wlan ssid-profile {}\r'.format(m.wlan_id))
        child.expect('#')
        if (m.name in up_new) and t == 0:
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


def unifi(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
    child.expect('password')
    child.sendline(ssh_password)
    for m in ssid_objects:
        child.expect('#')
        if ((m.name in up_new) and t == 0):
            child.sendline('ifconfig wifi0 up')
            child.expect('#')
            child.sendline('reboot')
            m.status = 1
        else:
            child.sendline('ifconfig wifi0 down')
            child.expect('#')
            child.sendline('exit')
            m.status = 0
        m.save()
        ssid_status.append(m.name)

def mikrotik(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
    child.expect('password')
    child.sendline('{}\n\r'.format(ssh_password))
    for m in ssid_objects:
        child.expect('>')
        if (m.name in up_new) and t == 0:
            child.sendline("/interface wireless enable {}\n\r".format(m.wlan_id))
            m.status = 1
        else:
            child.sendline("/interface wireless disable {}\n\r".format(m.wlan_id))
            m.status = 0
        m.save()
        ssid_status.append(m.name)
    child.expect('>')
    child.sendline('/quit\n\r')

def ruckus(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
    child.expect('login:')
    child.sendline(ssh_username)
    child.expect('Password:')
    child.sendline(ssh_password)
    child.expect('>')
    child.sendline('enable')
    child.expect('#')
    child.sendline('config')
    for m in ssid_objects:
        child.expect('#')
        if (m.name in up_new) and t == 0:
            child.sendline('wlan {}'.format(m.wlan_id))
            child.expect('#')
            child.sendline('type hotspot {}'.format(m.wlan_id))
            m.status = 1
        else:
            child.sendline('no wlan {}'.format(m.wlan_id))
            m.status = 0
        child.expect('#')
        child.sendline('end')
        child.expect('#')
        m.save()
        ssid_status.append(m.name)
    child.sendline('end')
    child.expect('#')
    child.sendline('exit')

def openwrt(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format('root', i))
    child.expect('password:')
    child.sendline('AQ!SW@de3?')
    for m in ssid_objects:
        child.expect('#')
        if (m.name in up_new) and t == 0:
            child.sendline('uci set wireless.@wifi-device[0].disabled=0; uci commit wireless; wifi\n')
            m.status = 1
        else:
            child.sendline('uci set wireless.@wifi-device[0].disabled=1; uci commit wireless; wifi\n')
            m.status = 0
        child.expect('#')
        m.save()
        ssid_status.append(m.name)
    child.expect('#')
    child.sendline('exit')


def meraki(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    murl = 'https://n150.meraki.com/api/v0/organizations/616518/networks/N_647392446434529213/ssids/'
    headers = {'X-Cisco-Meraki-API-Key': 'b21b5c3bfa37f5d920831f11775a321c077e71d1','Content-Type': 'application/json'}
    for m in ssid_objects:
        url = murl + m.wlan_id
        if (m.name in up_new) and t == 0:
            putdata = {'enabled': True}
            m.status = 1
        else:
            putdata = {'enabled': False}
            m.status = 0
        dashboard = requests.put(url, data=json.dumps(putdata), headers=headers)
        m.save()
        ssid_status.append(m.name)





@csrf_exempt
def index(request):
    all_list = list(ssid.objects.values_list('name', flat=True))
    all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
    #global ssid_status
    #ssid_status=[]
    errors=[]
    ctx = {}
    ctx['all_up_ssids']=all_up_ssids
    ctx['latest'] = ssid.objects.order_by('-vendor')
    ctx['servers']=enumerate(list(ssid.objects.values_list('web', flat=True).distinct().order_by('web')))
    ctx['ok']='Run'
    if request.method == 'POST':
        return HttpResponse('Index not for POSTs')
    else:
        return render(request, 'index.html', ctx)

def detail(request,name):
    a = ssid.objects.get(name=name)
    return render(request, 'ssid/detail.html', {'instance': a})


def status(request):
    print('Status request')
    print('Backend ssid status ',ssid_status)
    return JsonResponse({'ssid_status': ssid_status})