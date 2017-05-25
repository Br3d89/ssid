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
import sys,itertools,inspect,copy,socket,re

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
            print('Working on {} ip_list_length = {}'.format(i,len(ip_list)))
            vendor = ssid.objects.values_list('vendor__name', flat=True).distinct().filter(ip__name=i)[0]
            ssid_objects = ssid.objects.filter(ip__name=i, name__in=rcv_ssids)  # all ssids within device
            ssid_objects_up=ssid.objects.filter(ip__name=i, name__in=up_new)
            ssid_objects_down=ssid.objects.filter(ip__name=i,name__in=down_new)
            print(ssid_objects_down)
            if ssid_objects_up:
                print('if ssid_object_up = True')
                p = (threading.Thread(target=globals()['{}'.format(vendor)],kwargs={'i': i,'ssid_objects': ssid_objects_up, 'ssid_status_list': ssid_status_list,'ssid_error_list': ssid_error_list, 'errors': errors,'ssid_timeout': timeout_value, 'action': 'enable'}))  # поменял i
                p.start()
                process_list.append(p)
                d = threading.Timer(timeout_value, globals()['{}'.format(vendor)],kwargs={'i': i, 'ssid_objects': ssid_objects_up, 'ssid_status_list': ssid_status_list,'ssid_error_list': ssid_error_list, 'errors': errors,'ssid_timeout': timeout_value, 'action': 'disable'})  # нужно поменять i
                d.start()
            if ssid_objects_down:
                print('if ssid_object_down = True')
                p = (threading.Thread(target=globals()['{}'.format(vendor)],kwargs={'i': i, 'ssid_objects': ssid_objects_down, 'ssid_status_list': ssid_status_list, 'ssid_error_list': ssid_error_list,'errors': errors, 'ssid_timeout': timeout_value,'action': 'disable'}))  # поменял i
                p.start()
                process_list.append(p)
            else:
                print('There are no ssid objects for {}'.format(i))
        for i in process_list:
            print('Working with process_list, starting join process')
            i.join()
        all_up_ssids = list(ssid.objects.values_list('name', flat=True).filter(status='1'))
        return JsonResponse({'all_up_ssids': all_up_ssids, 'errors': errors})
    else:
        index(request)


def cisco(i,ssid_objects=[], ssid_status_list=[],ssid_error_list=[], errors=[],ssid_timeout=[], action=''):
    print('Working on Cisco {}, action = {}'.format(i,action))
    pass
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
        retry_count = 5
        while (k==1 and retry_count):
            print('Wrong login/password')
            child.sendline(ssh_username)
            child.expect(':')
            child.sendline(ssh_password)
            k = child.expect([">", ":"])
            retry_count -= 1
        if k==1:
            print('Cant connect to device {}'.format(i))
            return False
        child.sendline('')
        child.expect_exact(">")
        print('logged in')
        child.sendline('config paging disable')
        child.expect(">")

        #wlan_radius_id_mapping={}
        if action=='enable':
            print('Enabling action')
            #creating ssid
            child.sendline('show wlan summary')
            child.expect(">")
            a=str(child.before)
            #print(a)
            number_of_wlans=int(a.split(r'\r\n')[2].split('.')[-1].split()[0])
            #print(number_of_wlans)
            if number_of_wlans < 16:
                print('Number of wlans < 16')
                #Looking for free wlan id
                b=a.split(r'\r\n')[6:-2]
                wlan_list=[]
                for i in b:
                    wlan_list.append(i.split()[0])
                free_wlan_id=[]
                for i in range(1,17):
                    if str(i) not in wlan_list:
                        free_wlan_id.append(str(i))
                print('free_wlan_id = {}'.format(free_wlan_id))
                # Looking for free radius server id
                child.sendline('show radius summary')
                child.expect(">")
                r = str(child.before)


                # Auth server id
                c = r.split('Accounting Servers')[0].split(r'\r\n')[21:-1]
                radius_auth_list = []
                for i in c:
                    radius_auth_list.append(i.split()[0])
                free_radius_auth_id = []
                for i in range(1, 33):
                    if str(i) not in radius_auth_list:
                        free_radius_auth_id.append(i)
                print('free radius auth id = {}'.format(free_radius_auth_id))
                # Acct server id
                #c = r.split('Accounting Servers')[1].split(r'\r\n')[4:-2]
                #radius_acct_list = []
                #for i in c:
                #    radius_acct_list.append(i.split()[0])
                #free_radius_acct_id = []
                #for i in range(1, 33):
                #    if str(i) not in radius_acct_list:
                #        free_radius_acct_id.append(i)


                for i in ssid_objects:
                    print('Working with {} ssid object'.format(i))
                    child.sendline('config wlan create {} {} {}'.format(free_wlan_id[0],i.name,i.name))
                    child.expect(">")
                    child.sendline('config wlan mac-filtering enable {}'.format(free_wlan_id[0]))
                    child.expect(">")
                    child.sendline('config wlan security wpa disable {}'.format(free_wlan_id[0]))
                    child.expect(">")
                    child.sendline('config wlan aaa-override enable {}'.format(free_wlan_id[0]))
                    child.expect(">")
                    child.sendline('config wlan nac radius enable {}'.format(free_wlan_id[0]))
                    child.expect(">")
                    child.sendline('config wlan exclusionlist {} disabled'.format(free_wlan_id[0]))
                    child.expect(">")
                    child.sendline('config wlan security ft disable {}'.format(free_wlan_id[0]))
                    child.expect(">")
                    #add wlan to ap-group wcm_private
                    child.sendline('config wlan apgroup interface-mapping add wcm_private {} management'.format(free_wlan_id[0]))
                    child.expect(">")

                    print('Radius server creation')
                    if len(free_radius_auth_id):
                        child.sendline('config radius auth add {} {} 1812 ascii dfqAFQhekbn!'.format(free_radius_auth_id[0], i.web.ip))
                        child.expect(">")
                        child.sendline('config radius auth disable {}'.format(free_radius_auth_id[0]))
                        child.expect(">")
                        child.sendline('config radius auth rfc3576 enable {}'.format(free_radius_auth_id[0]))
                        child.expect(">")
                        child.sendline('config radius auth enable {}'.format(free_radius_auth_id[0]))
                        child.expect(">")
                        child.sendline('config radius auth management {} disable'.format(free_radius_auth_id[0]))
                        child.expect(">")

                    #if len(free_radius_acct_id):
                        child.sendline('config radius acct add {} {} 1812 ascii dfqAFQhekbn!'.format(free_radius_auth_id[0],i.web.ip))
                        child.expect(">")
                    else:
                         print('There is no free IDs for radius server')
                    print('Mapping radius to wlan')
                    # mapping radius to wlan
                    child.sendline('config wlan radius_server auth add {} {}'.format(free_wlan_id[0],free_radius_auth_id[0]))
                    child.expect(">")
                    child.sendline('config wlan radius_server acct add {} {}'.format(free_wlan_id[0],free_radius_auth_id[0]))
                    child.expect(">")
                    print('creating acl')
                    #creating acl
                    acl_shortcut=i.web.name.split('.')[0]
                    for k in i.acl.split(','):
                        child.sendline('config acl create {}'.format(k))
                        child.expect(">")
                        child.sendline('config acl url-domain add {} {}'.format(i.web.name, k))
                        child.expect(">")
                        if 'social' in k:
                            child.sendline('config acl url-domain add fbcdn.net {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add facebook.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add facebook.net {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add vk.com {}'.format(k))
                            child.expect(">")
                        if 'apple' in k:
                            child.sendline('config acl url-domain add apple.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add connectivitycheck.android.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add clients3.google.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add www.msftncsi.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add appleiphonecell.com {}'.format(k))
                            child.expect(">")
                            child.sendline('config acl url-domain add akamaitechnologies.com {}'.format(k))
                            child.expect(">")


                    #enable wlan
                    child.sendline('config wlan enable {}'.format(free_wlan_id[0]))

                    i.status = 1
                    i.wlan_id=free_wlan_id[0]
                    #i.acl="{}_limited,{}_social,{}_apple".format(acl_shortcut,acl_shortcut,acl_shortcut)
                    i.start_date = datetime.now()
                    i.end_date = i.start_date + timedelta(0, ssid_timeout)
                    i.save()

                    #delete id fro free list
                    #wlan_radius_id_mapping[free_wlan_id[0]]=free_radius_auth_id
                    free_wlan_id.pop(0)
                    free_radius_auth_id.pop(0)
                    #free_radius_acct_id.pop(0)
                    ssids_busy.remove(i.name)
                    ssid_status_list.append(i.name)
                    print('SSID {} enabled'.format(i.name))

            #number of wlans >= 16
            else:
                print('Maximum number of wlans reached')

        if action=='disable':
            print('Disabling action')
            child.sendline('show radius summary')
            child.expect(">")
            r = str(child.before)
            for i in ssid_objects:
                print('Deleting wlan')
                child.sendline('config wlan delete {}'.format(i.wlan_id))
                child.sendline('y')
                child.expect('>')
                print('Deleting radius auth')
                radius_server_id=r.split(i.web.ip)[0].split(r'\r\n')[-1].split()[0]
                print('radius server id = {}'.format(radius_server_id))
                child.sendline('config radius auth delete {}'.format(radius_server_id))
                child.expect('>')
                print('Deleting radius acct')
                child.sendline('config radius acct delete {}'.format(radius_server_id))
                child.expect('>')
                print('Deleting acl')
                for k in i.acl.split(','):
                    print(k)
                    child.sendline('config acl delete {}'.format(k))
                    child.expect('>')
                ssids_busy.remove(i.name)
                ssid_status_list.append(i.name)
                i.status=0
                i.wlan_id = ''
                i.save()
                print('SSID {} disabled'.format(i.name))


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
    device_queryset=device_ip.objects.all().order_by('vendor')
    auth_scheme_queryset=auth_scheme.objects.all()
    group_queryset=Group.objects.all()
    from ssid.models import vendor
    vendor_queryset=vendor.objects.filter(name__in=['cisco', 'aruba', 'huawei', 'meraki', 'mikrotik', 'ruckus', 'ruckusvsz'])
    ctx['user_object'] = auth.get_user(request)
    ctx['username'] = auth.get_user(request).username
    ctx['server_queryset']=server_queryset
    ctx['device_queryset']=device_queryset
    ctx['vendor_queryset']=vendor_queryset
    ctx['auth_scheme_queryset'] = auth_scheme_queryset
    ctx['group_queryset'] = group_queryset
    if request.POST:
        print('received add POST')
        ssid_name = request.POST.get('name')
        #getting values from name field
        ssid_name_list=[s.strip() for s in re.split(",|;/", ssid_name)]
        ssid_vendor = json.loads(request.POST.get('vendor'))
        #print('SSID VENDOR LIST',ssid_vendor)
        #ssid_device=json.loads(request.POST.get('device'))
        #print('SSID DEVICE',ssid_device)
        ssid_server = request.POST.get('server')
        #ssid_auth_scheme=request.POST.get('auth_scheme')
        #ssid_group_list=json.loads(request.POST.get('group'))
        #ssid_server_ip = request.POST.get('custom_server_ip')
        try:
            ssid_server_ip=socket.gethostbyname(ssid_server)
        except socket.gaierror:
            print("Couldn't resolve hostname")
            return JsonResponse({'ssid_server_ip': 'server name is not resolvable'})
        ssid_server_object=auth_server.objects.get_or_create(name=ssid_server,defaults={'ip':ssid_server_ip})[0]
        ssid_server_object.group.add(Group.objects.get(id=1))
        ssid_server_object.save()
        #ssid_auth_scheme_object=auth_scheme.objects.get(name=ssid_auth_scheme)
        ssid_vendor=list(device_queryset.filter(name__in=ssid_device).values_list('vendor__name', flat=True))
        ssid_device_objects = device_queryset.filter(name__in=ssid_device)
        process_list = []
        for i in ssid_device_objects:
            vendor = ssid.objects.values_list('vendor__name', flat=True).distinct().filter(ip__name=i.name)[0]
            ssid_name=ssid_name + '_' + i.vendor.name
            #p = (threading.Thread(target=globals()['{}'.format(vendor)], kwargs={'i':i.name,'action':'add','ssid_name':ssid_name,'ssid_server':ssid_server_object}))
            #p.start()
            #process_list.append(p)
            #creating new ssid object
            new_ssid = ssid()
            new_ssid.name = ssid_name
            new_ssid.vendor = i.vendor
            new_ssid.ip = i
            new_ssid.web = ssid_server_object
            ssid_auth_scheme_object=auth_scheme.objects.get(name=list(vendor.objects.get(name=vendor).auth_scheme.values_list('name',flat=True))[0])
            new_ssid.auth_scheme=ssid_auth_scheme_object
            new_ssid.save()
            #default mapping to ssidapp group
            new_ssid.group.add(Group.objects.get(id=11))
            new_ssid.save()
        #for i in process_list:
        #    i.join()
        #    print('Join test')
        return JsonResponse({'created_ssids': ssid_name})
        print('SSID objects created')
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

