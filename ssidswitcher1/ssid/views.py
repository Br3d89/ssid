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
pexp_timeout=10


@csrf_exempt
def ssid_update(request):
    all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
    global ssid_status
    ssid_status = []
    errors = []
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
            i.join()
        all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
        return JsonResponse({'all_up_ssids': all_up_ssids, 'errors': errors})
    else:
        index(request)


def cisco(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        child.expect(':',timeout=pexp_timeout)
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
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def aruba(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} {} -o StrictHostKeyChecking=no'.format(ssh_username, i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline("{}\r".format(ssh_password))
        child.expect("#")
        child.sendline('conf\r')
        for m in ssid_objects:
            child.expect('#')
            child.sendline('wlan ssid-profile {}\r'.format(m.wlan_id))
            child.expect('#')
            if (m.name in up_new) and t == 0:
                child.sendline('enable\r')
                m.status = 1
            else:
                child.sendline('disable\r')
                m.status = 0
            m.save()
            child.sendline('exit\r')
            ssid_status.append(m.name)
        child.sendline('end\r')
        child.expect('#')
        child.sendline('commit apply\r')
        child.expect('#')
        child.sendline('logout')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def unifi(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
        child.expect(':', timeout=pexp_timeout)
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
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def mikrotik(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        print('Running mikrotik')
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
        child.expect(':', timeout=pexp_timeout)
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
        print('Mikrotik done')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def ruckus(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        child.expect(':', timeout=pexp_timeout)
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
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def openwrt(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format('root', i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline('AQ!SW@de3?')
        for m in ssid_objects:
            child.expect('#')
            if (m.name in up_new) and t == 0:
                child.sendline('uci set wireless.@wifi-device[0].disabled=0; uci commit wireless; wifi\n')
                m.status = 1
            else:
                child.sendline('uci set wireless.@wifi-device[0].disabled=1; uci commit wireless; wifi\n')
                m.status = 0
            m.save()
            ssid_status.append(m.name)
        child.expect('#')
        child.sendline('exit')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


def huawei(up_new, down_new, ssid_objects, i, ssid_status, errors, t=0):
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline(ssh_password)
        child.expect('>')
        child.sendline('system-view')
        child.expect(']')
        child.sendline('wlan')
        for m in ssid_objects:
            child.expect(']')
            child.sendline('vap-profile name {}'.format(m.wlan_id))
            child.expect(']')
            if (m.name in up_new) and t == 0:
                child.sendline('undo service-mode disable')
                m.status = 1
            else:
                child.sendline('service-mode disable')
                m.status = 0
            m.save()
            ssid_status.append(m.name)
        child.expect(']')
        child.sendline('\x1A')   #CTRL+Z command
        child.expect('>')
        child.sendline('save')
        child.expect(':')
        child.sendline('y')
        child.expect('>')
        child.sendline('quit')
    except pexpect.exceptions.TIMEOUT as err:
        errors.append(list(ssid_objects.values_list('name', flat=True)))


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