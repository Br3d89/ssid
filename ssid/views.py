from django.shortcuts import render,redirect
from django.http import JsonResponse, HttpResponse
from .models import ssid,auth_server,device_ip,vendor,auth_scheme
from django import forms
from django.views.decorators.csrf import csrf_exempt
import paramiko,time,pexpect,requests,json,logging,threading
from datetime import datetime,timedelta
from multiprocessing import Process
from django.contrib import auth
from django.contrib.auth.models import Group
import sys,itertools,inspect,copy

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
ssid_status_list=[]
ssid_error_list=[]
down_status=[]
ssids_busy=[]
pexp_timeout=6


#@csrf_exempt
def ssid_update(request):
    all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
    global ssid_status_list
    global ssid_error_list
    ssid_status_list = []
    ssid_error_list = []
    errors = []
    if request.method == 'POST':
        up_new = json.loads(request.POST.get('up'))
        down_new = json.loads(request.POST.get('down'))
        timeout_value = int(json.loads(request.POST.get('timer')))*60
        rcv_ssids = up_new + down_new
        [ssids_busy.append(i) for i in rcv_ssids]
        ip_list = list(ssid.objects.values_list('ip__name', flat=True).distinct().filter(name__in=rcv_ssids))

        process_list = []
        for i in ip_list:
            vendor = ssid.objects.values_list('vendor__name', flat=True).distinct().filter(ip__name=i)[0]
            ssid_objects = ssid.objects.filter(ip__name=i, name__in=rcv_ssids)  # all ssids within device
            ssid_objects_up=ssid.objects.filter(ip__name=i, name__in=up_new)
            p = (threading.Thread(target=globals()['{}'.format(vendor)],args=(i, up_new, down_new, ssid_objects, ssid_status_list, ssid_error_list, errors,timeout_value)))   #поменял i
            p.start()
            process_list.append(p)
            if ssid_objects_up:     #run disable thread only for ssid_objects_up
                print('Creating disable thread')
                d = threading.Timer(timeout_value, globals()['{}'.format(vendor)],args=(up_new, down_new, ssid_objects_up, i, ssid_status_list, ssid_error_list, errors,timeout_value, 1))  #нужно поменять i
                d.start()
        for i in process_list:
            i.join()
        all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
        return JsonResponse({'all_up_ssids': all_up_ssids, 'errors': errors})
    else:
        index(request)


def cisco(i,up_new=[], down_new=[], ssid_objects=[], ssid_status_list=[],ssid_error_list=[], errors=[],ssid_timeout=[], t=0,action='',ssid_name='',ssid_server=''):
    print('Working on Cisco {}, action = {}'.format(i,action))
    #print('Debug info:',ssid_name,action)
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        fout = open('/home/bred/ssid/test.log', 'wb')
        child.logfile = fout
        child.expect(':',timeout=pexp_timeout)
        child.sendline(ssh_username)
        child.expect(':')
        child.sendline(ssh_password)
        k=child.expect([">",":"])
        if k==1:
            print('Wrong login/password')
            child.sendline(ssh_username)
            child.expect(':')
            child.sendline(ssh_password)
        child.sendline('')
        child.expect_exact(">")
        child.sendline('config paging disable')
        if action=='up/down':
            for m in ssid_objects:
                child.expect(">")
                if (m.name in up_new) and t == 0:
                    child.sendline('config wlan enable {}'.format(m.wlan_id))
                    m.status = 1
                    m.start_date=datetime.now()
                    m.end_date=m.start_date+timedelta(0,ssid_timeout)
                    print(m.name,' enabled')
                else:
                    child.sendline('config wlan disable {}'.format(m.wlan_id))
                    m.status = 0
                    print(m.name,' disabled')
                m.save()
                if t==0:
                    ssids_busy.remove(m.name)
                ssid_status_list.append(m.name)
        elif action=='add':
            child.expect(">")
            #creating ssid
            child.sendline('show wlan summary')
            child.expect(">")
            a=str(child.before)
            #print(a)
            number_of_wlans=int(a.split(r'\r\n')[2].split('.')[-1].split()[0])
            #print(number_of_wlans)
            if number_of_wlans < 16:
                b=a.split(r'\r\n')[6:-2]
                wlan_list=[]
                for i in b:
                    wlan_list.append(i.split()[0])
                free_wlan_id=[]
                for i in range(1,17):
                    if str(i) not in wlan_list:
                        free_wlan_id.append(str(i))
                child.sendline('config wlan create {} {} {}'.format(free_wlan_id[0],ssid_name,ssid_name))
                ssid_object=ssid.objects.get(name=ssid_name)
                ssid_object.wlan_id=free_wlan_id[0]
                ssid_object.save()
                child.expect(">")
                print(ssid_server.name)
                child.sendline('show radius summary')
                child.expect(">")
                r = str(child.before)
                print(r)
                #creating aaa server
                #creating acl
                #creating model
                #new_ssid=ssid()
                #new_ssid.name=ssid_name
                #new_ssid.vendor=inspect.stack()[0][3]
                #new_ssid.ip=i
                #new_ssid.web=
                #print('Cisco finished')
                #print('Cisco finished')


            else:
                print('Maximum number reached')
        #child.expect('>')
        #print('Logout from Cisco')
        child.sendline('logout')
        child.expect('(y/N)')
        child.sendline('y')
        print('Cisco {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        time.sleep(2)
        print(err)



def aruba(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list, errors,ssid_timeout, t=0):
    print('Working on Aruba {} '.format(i))
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        #fout = open('/home/bred/ssid/ssid/test.log', 'wb')
        #child.logfile = fout
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
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('disable\r')
                m.status = 0
                print(m.name,' disabled')
            m.save()
            child.sendline('exit\r')
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.sendline('end\r')
        child.expect('#')
        child.sendline('commit apply\r')
        child.expect('#')
        child.sendline('logout')
        print('Aruba {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def unifi(up_new, down_new, ssid_objects, i, ssid_status_list,ssid_error_list, errors,ssid_timeout, t=0):
    print('Working on Unifi {} '.format(i))
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
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('ifconfig wifi0 down')
                child.expect('#')
                child.sendline('exit')
                m.status = 0
                print(m.name,' disabled')
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
            print('Unifi {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def mikrotik(up_new, down_new, ssid_objects, i, ssid_status_list,ssid_error_list, errors,ssid_timeout, t=0):
    print('Working on Mikrotik {} '.format(i))
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username,i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline('{}\n\r'.format(ssh_password))
        for m in ssid_objects:
            child.expect('>')
            if (m.name in up_new) and t == 0:
                child.sendline("/interface wireless enable {}\n\r".format(m.wlan_id))
                time.sleep(1)
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline("/interface wireless disable {}\n\r".format(m.wlan_id))
                time.sleep(1)
                m.status = 0
                print(m.name,' disabled') 
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.expect('>')
        child.sendline('/quit\n\r')
        print('Mikrotik {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def ruckus(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on Ruckus {} '.format(i))
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format(ssh_username, i))
        fout = open('/home/bred/ssid/ssid/test.log', 'wb')
        child.logfile = fout
        child.expect(':', timeout=pexp_timeout)
        child.sendline(ssh_username)
        child.expect('Password:')
        child.sendline(ssh_password)
        child.expect('>')
        child.sendline('enable')
        child.expect('#')
        child.sendline('config')
        child.expect('#')
        for m in ssid_objects:
            if (m.name in up_new) and t == 0:
                child.sendline('wlan {}'.format(m.wlan_id))
                child.expect('#')
                child.sendline('type hotspot {}'.format(m.wlan_id))
                child.expect('#')
                child.sendline('called-station-id-type ap-mac')
                child.expect('#')
                child.sendline('end')
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('no wlan {}'.format(m.wlan_id))
                m.status = 0
                print(m.name,' disabled')
            child.expect('#')
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.sendline('end')
        child.expect('#')
        child.sendline('exit')
        print('Rukcus {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def ruckusvsz(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on RuckusVSZ {} '.format(i))
    try:
        child = pexpect.spawn('ssh -l admin -o StrictHostKeyChecking=no {}'.format(i))
        #fout = open('/home/bred/ssid/ssid/test.log', 'wb')
        #child.logfile = fout
        child.expect('password:',timeout=pexp_timeout)
        child.sendline('AQ!SW@de3?')
        child.expect('>')
        child.sendline('enable')
        child.expect('Password:')
        child.sendline('AQ!SW@de3?')
        child.expect('#')
        child.sendline('config')
        for m in ssid_objects:
            child.expect('#')
            child.sendline('wlan {}'.format(m.wlan_id))
            child.expect('#')
            if (m.name in up_new) and t == 0:
                child.sendline('enable-type Always-On')
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('enable-type Always-Off')
                m.status = 0
                print(m.name,' disabled')
            child.expect('#')
            child.sendline('exit')
            child.expect(']')
            child.sendline('yes')            
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.sendline('end')
        child.expect('#')
        child.sendline('logout')
        print('RuckusVSZ {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def openwrt(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on OpenWRT {} '.format(i))
    try:
        child = pexpect.spawn('ssh -l {} -o StrictHostKeyChecking=no {}'.format('root', i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline('AQ!SW@de3?')
        for m in ssid_objects:
            child.expect('#')
            if (m.name in up_new) and t == 0:
                child.sendline('uci set wireless.@wifi-device[0].disabled=0; uci commit wireless; wifi\n')
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('uci set wireless.@wifi-device[0].disabled=1; uci commit wireless; wifi\n')
                m.status = 0
                print(m.name,' disabled')
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.expect('#')
        child.sendline('exit')
        print('OpenWRT {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def ddwrt(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on DDWRT {} '.format(i))
    try:
        child = pexpect.spawn('telnet {}'.format(i))
        child.expect(':', timeout=pexp_timeout)
        child.sendline('root')
        child.expect(':')
        child.sendline('AQ!SW@de3?')
        for m in ssid_objects:
            child.expect('#')
            if (m.name in up_new) and t == 0:
                child.sendline('ifconfig ath0 up\n')
                child.expect('#')
                child.sendline('reboot\n')
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('ifconfig ath0 down\n')
                m.status = 0
                print(m.name,' disabled')
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.expect('#')
        child.sendline('exit')
        print('DDWRT {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


def huawei(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on Huawei {} '.format(i))
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
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                child.sendline('service-mode disable')
                m.status = 0
                print(m.name,' disabled')
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        child.expect(']')
        child.sendline('\x1A')   #CTRL+Z command
        child.expect('>')
        child.sendline('save')
        child.expect(':')
        child.sendline('y')
        child.expect('>')
        child.sendline('quit')
        print('Huawei {} done'.format(i))
        time.sleep(1)
    except pexpect.exceptions.TIMEOUT as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)
        time.sleep(1)


def meraki(up_new, down_new, ssid_objects, i, ssid_status_list, ssid_error_list,errors,ssid_timeout, t=0):
    print('Working on Meraki {} '.format(i))
    try:
        murl = 'https://n150.meraki.com/api/v0/organizations/616518/networks/N_647392446434529213/ssids/'
        headers = {'X-Cisco-Meraki-API-Key': 'b21b5c3bfa37f5d920831f11775a321c077e71d1','Content-Type': 'application/json'}
        for m in ssid_objects:
            url = murl + m.wlan_id
            if (m.name in up_new) and t == 0:
                putdata = {'enabled': True}
                m.status = 1
                m.start_date = datetime.now()
                m.end_date = m.start_date + timedelta(0, ssid_timeout)
                print(m.name,' enabled')
            else:
                putdata = {'enabled': False}
                m.status = 0
                print(m.name,' disabled')
            dashboard = requests.put(url, data=json.dumps(putdata), headers=headers)
            m.save()
            if t==0:
                ssids_busy.remove(m.name)
            ssid_status_list.append(m.name)
        print('Meraki {} done'.format(i))
        time.sleep(1)
    except requests.exceptions.ConnectionError as err:
        for i in list(ssid_objects.values_list('name', flat=True)):
            ssid_error_list.append(i)
            ssids_busy.remove(i)
        errors.append(list(ssid_objects.values_list('name', flat=True)))
        print(err)


#@csrf_exempt
def index(request,args={}):
    errors = []
    ctx = {}
    ctx.update(args)
    request_user_group=list(request.user.groups.values_list('name', flat=True))
    all_group_ssids=ssid.objects.filter(group__name__in=request_user_group).order_by('-vendor_id')
    all_up_ssids = list(ssid.objects.filter(group__name__in=request_user_group).filter(status='1').distinct().values_list('name', flat=True))   #Сначала нужно выбрать все сервера относящиеся к пользователю
    request_user_servers =list(auth_server.objects.values_list('name', flat=True).filter(group__name=request_user_group))

    servers_with_up_ssids = list(ssid.objects.filter(status=1).filter(group__name__in=request_user_group).distinct().values_list('web__name', flat=True))
    vendors_with_up_ssids=list(ssid.objects.filter(status=1).filter(group__name__in=request_user_group).distinct().values_list('vendor__name',flat=True))

    servers_with_down_ssids = list(ssid.objects.filter(status=0).filter(group__name__in=request_user_group).distinct().values_list('web__name',flat=True).order_by('web_id'))
    vendors_with_down_ssids=list(ssid.objects.filter(status=0).filter(group__name__in=request_user_group).distinct().values_list('vendor__name',flat=True).order_by('vendor_id'))

    servers_ssids_sorted=[]+servers_with_up_ssids
    vendors_ssids_sorted=[]+vendors_with_up_ssids

    # Index button position logic for servers
    for i in servers_with_down_ssids:
        if i not in servers_with_up_ssids:
            servers_ssids_sorted.append(i)
    div = []
    iter_list = []
    server_list_len=len(servers_ssids_sorted)
    if server_list_len<=3:
       for i in range(server_list_len):
           div.append([])
           iter_list.append(i)
       div_cycle = itertools.cycle(iter_list)
       for i in servers_ssids_sorted:
           div[next(div_cycle)].append(i)
       div_enum = enumerate(div)
    else:
        for i in range(3):
            div.append([])
            iter_list.append(i)
        div_cycle = itertools.cycle(iter_list)
        for i in servers_ssids_sorted:
            div[next(div_cycle)].append(i)
        div_enum = enumerate(div)
    # End of Index button position logic for servers



    # Index button position logic for vendors
    for i in vendors_with_down_ssids:
        if i not in vendors_with_up_ssids:
            vendors_ssids_sorted.append(i)
    div_vendors = []
    iter_list_vendors = []
    vendor_list_len = len(vendors_ssids_sorted)
    if vendor_list_len <= 3:
        for i in range(vendor_list_len):
            div_vendors.append([])
            iter_list_vendors.append(i)
        div_cycle_vendors = itertools.cycle(iter_list_vendors)
        for i in vendors_ssids_sorted:
            div_vendors[next(div_cycle_vendors)].append(i)
        div_enum_vendors = enumerate(div_vendors)
    else:
        for i in range(3):
            div_vendors.append([])
            iter_list_vendors.append(i)
        div_cycle_vendors = itertools.cycle(iter_list_vendors)
        for i in vendors_ssids_sorted:
            div_vendors[next(div_cycle_vendors)].append(i)
        div_enum_vendors = enumerate(div_vendors)
    # End of Index button position logic for vendors


    ctx['ssids_busy']=ssids_busy
    ctx['ssid_status_list']=ssid_status_list
    ctx['all_up_ssids']=all_up_ssids
    ctx['servers_with_up_ssids']=servers_with_up_ssids
    ctx['vendors_with_up_ssids']=vendors_with_up_ssids         #for accordion logic
    ctx['all_group_ssids']=ssid.objects.filter(group__name__in=request_user_group).order_by('-vendor_id')
    ctx['servers']=servers_ssids_sorted
    ctx['servers_enum']=div_enum
    ctx['vendors_enum']=div_enum_vendors             #for accordion logic
    ctx['ok']='Run'
    ctx['username']=auth.get_user(request).username
    ctx['user_object']=auth.get_user(request)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            ctx['login_error'] = 'Login failed'
            return render(request, 'index.html', ctx)
        #return HttpResponse('Index not for POSTs')
    else:
        return render(request, 'index.html', ctx)


def detail(request,name):
    ctx={}
    ctx['user_object'] = auth.get_user(request)
    ctx['username'] = auth.get_user(request).username
    ctx['instance']=ssid.objects.get(name=name)
    return render(request, 'detail.html', ctx)


def ssid_status(request):
    #print('Status request')
    #print('Backend ssid status ',ssid_status_list)
    return JsonResponse({'ssid_status_list': ssid_status_list})


def ssid_busy(request):
    return JsonResponse({'ssid_busy_list': ssids_busy})


def ssid_error(request):
    #print('Error request')
    #print('Backend ssid error ', ssid_error_list)
    return JsonResponse({'ssid_error_list': ssid_error_list})

a=vendor.objects.all()
def ssid_add(request):
    ctx={}
    server_queryset=auth_server.objects.all()
    device_queryset=device_ip.objects.all()
    from ssid.models import vendor
    vendor_queryset=vendor.objects.all()
    ctx['user_object'] = auth.get_user(request)
    ctx['username'] = auth.get_user(request).username
    ctx['server_queryset']=server_queryset
    ctx['device_queryset']=device_queryset
    ctx['vendor_queryset']=vendor_queryset
    if request.POST:
        print('received POST')
        ssid_name = request.POST.get('name')
        ssid_vendor = json.loads(request.POST.get('vendor'))
        ssid_device=json.loads(request.POST.get('device'))
        ssid_server = request.POST.get('server')
        ssid_server_object=auth_server.objects.get(name=ssid_server)
        ssid_device_objects = device_queryset.filter(name__in=ssid_device)
        if ssid_device:
            ssid_vendor=list(device_queryset.filter(name__in=ssid_device).values_list('vendor__name', flat=True))
        process_list = []
        for i in ssid_device_objects:
            vendor = ssid.objects.values_list('vendor__name', flat=True).distinct().filter(ip__name=i.name)[0]
            action='add'
            ssid_name=ssid_name + '_' + i.vendor.name
            p = (threading.Thread(target=globals()['{}'.format(vendor)], kwargs={'i':i.name,'action':action,'ssid_name':ssid_name,'ssid_server':ssid_server_object}))
            p.start()
            process_list.append(p)
            #creating new ssid object
            new_ssid = ssid()
            new_ssid.name = ssid_name
            new_ssid.vendor = i.vendor
            new_ssid.ip = i
            new_ssid.web = ssid_server_object
            new_ssid.auth_scheme=auth_scheme.objects.get(pk=1)
            new_ssid.save()
            new_ssid.group.add(Group.objects.get(id=1))
            new_ssid.save()
        for i in process_list:
            i.join()
            print('Join test')


        #return JsonResponse({'all_up_ssids': all_up_ssids, 'errors': errors})
        print('Finished')
        #print(ssid_name,ssid_vendor,ssid_device,ssid_server)
    return render(request, 'add.html', ctx)


def login(request):
    print('Login is triggered')
    args={}
    args['servers'] = enumerate(list(ssid.objects.values_list('web', flat=True).distinct().order_by('web')))
    if request.POST:
        #username = json.loads(request.POST.get('username'))
        #password = json.loads(request.POST.get('password'))
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            args['login_error']='Login failed'
            #return render(request,'index.html', args)
            return index(request,args)
    else:
        return render(request, 'index.html', args)


def logout(request):
    print('Logout is triggered')
    auth.logout(request)
    return redirect('/')


def profile(request):
    args = {}
    args['username'] = auth.get_user(request).username
    args['user_object']=auth.get_user(request)
    return render(request, 'profile.html', args)

