# Copyright (C) 2018-2023 Mark McIntyre

from tksheet import Sheet
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, Frame, Menu
from tkinter import simpledialog
import boto3
import shutil
import datetime
import os
import pandas
import paramiko
import json 
import time
from scp import SCPClient

from camTable import addRow as addRowToDDB
from camTable import getCamUpdateDate


class infoDialog(simpledialog.Dialog):
    def __init__(self, parent, title, location, user, email, sshkey='', id=''):
        self.data = []
        self.data.append(id)
        self.data.append(location)
        self.data.append('')
        self.data.append(user)
        self.data.append(email)
        self.data.append(sshkey)

        super().__init__(parent, title)    

    def body(self, frame):
        # print(type(frame)) # tkinter.Frame
        self.camid_label = tk.Label(frame, width=25, text="RMS ID")
        self.camid_label.pack()
        self.camid_box = tk.Entry(frame, width=25)
        self.camid_box.insert(tk.END, self.data[0])
        self.camid_box.pack()

        self.location_label = tk.Label(frame, width=25, text="Location")
        self.location_label.pack()
        self.location_box = tk.Entry(frame, width=25)
        self.location_box.insert(tk.END, self.data[1])
        self.location_box.pack()

        self.direction_label = tk.Label(frame, width=25, text="direction")
        self.direction_label.pack()
        self.direction_box = tk.Entry(frame, width=25)
        self.direction_box.pack()

        self.ownername_label = tk.Label(frame, width=25, text="owner name")
        self.ownername_label.pack()
        self.ownername_box = tk.Entry(frame, width=25)
        self.ownername_box.insert(tk.END, self.data[3])
        self.ownername_box.pack()

        self.email_label = tk.Label(frame, width=25, text="email address")
        self.email_label.pack()
        self.email_box = tk.Entry(frame, width=25)
        self.email_box.insert(tk.END, self.data[4])
        self.email_box.pack()

        self.sshkey_label = tk.Label(frame, width=25, text="SSH key")
        self.sshkey_label.pack()
        self.sshkey_box = tk.Entry(frame, width=50)
        self.sshkey_box.insert(tk.END, self.data[5])
        self.sshkey_box.pack()

    def ok_pressed(self):
        self.data[0] = self.camid_box.get().strip()
        self.data[1] = self.location_box.get().strip()
        self.data[2] = self.direction_box.get().strip()
        self.data[3] = self.ownername_box.get().strip()
        self.data[4] = self.email_box.get().strip()
        self.data[5] = self.sshkey_box.get().strip()
        self.destroy()

    def cancel_pressed(self):
        # print("cancel")
        self.data[0] = ''
        self.destroy()

    def buttonbox(self):
        self.ok_button = tk.Button(self, text='OK', width=5, command=self.ok_pressed)
        self.ok_button.pack(side="left")
        cancel_button = tk.Button(self, text='Cancel', width=5, command=self.cancel_pressed)
        cancel_button.pack(side="right")
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.cancel_pressed())


class statOwnerDialog(simpledialog.Dialog):
    def __init__(self, parent, statfile):
        self.statfile = statfile
        self.parent = parent
        super().__init__(parent, 'Owner Info')    
    
    def body(self, frame):
        columns = ('#1','#2','#3','#4')
        print(columns)
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        tree.heading('#1', text='camid')
        tree.heading('#2', text='site')
        tree.heading('#3', text='humanName')
        tree.heading('#4', text='email')
        contacts = []
        with open(os.path.join('caminfo', self.statfile),'r') as inf:
            _ = inf.readline() # skip header
            lis=inf.readlines()
            for li in lis:
                spls = li.split(',')
                contacts.append((spls[0], spls[1], spls[2], spls[3]))
        for contact in contacts:
            tree.insert('', tk.END, values=contact)
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        return 


class CamMaintenance(Frame):

    def __init__(self, parent):
        self.parent = parent
        Frame.__init__(self, parent)

        self.archprof = os.getenv('ARCH_PROFILE', default='ukmda_admin')
        conn = boto3.Session(profile_name=self.archprof)
        s3 = conn.client('s3')
        self.bucket_name = os.getenv('SRCBUCKET', default='ukmda-shared')

        os.makedirs('jsonkeys', exist_ok=True)
        os.makedirs('csvkeys', exist_ok=True)
        os.makedirs('users', exist_ok=True)
        os.makedirs('inifs', exist_ok=True)
        os.makedirs('sshkeys', exist_ok=True)

        self.camfile = 'camera-details.csv'
        self.fullname = 'consolidated/{}'.format(self.camfile)
        self.localfile = os.path.join('caminfo', self.camfile)
        self.statfile='stationdetails.csv'
        self.fullstat = 'admin/'+self.statfile
        self.locstatfile = os.path.join('caminfo', self.statfile)
        try: 
            s3.download_file(Bucket=self.bucket_name, Key=self.fullname, Filename=self.localfile)
            s3.download_file(Bucket=self.bucket_name, Key=self.fullstat, Filename=self.locstatfile)
            pass
        except:
            print('unable to get data files, using last good files')

        self.caminfo = pandas.read_csv(self.localfile)
        self.caminfo = self.caminfo.sort_values(by=['active','camtype','camid'],ascending=[True,False,False])
        self.data = self.caminfo.values.tolist()
        self.hdrs = self.caminfo.columns.tolist()
        self.datachanged = True
     
        #self.parent = tk.Tk.__init__(self)
        self.parent.title('Station Maintenance')

        # Make menu
        self.menuBar = Menu(self.parent)
        self.parent.config(menu=self.menuBar)

        # File menu
        fileMenu = Menu(self.menuBar, tearoff=0)
        fileMenu.add_command(label="Exit", command=self.on_closing)

        camMenu = Menu(self.menuBar, tearoff=0)
        camMenu.add_command(label = "Add Camera", command = self.addCamera)
        camMenu.add_command(label = "Relocate Camera", command = self.moveCamera)
        camMenu.add_command(label = "Remove Camera", command = self.delCamera)
        camMenu.add_separator()
        camMenu.add_command(label = "Remove Location", command = self.delOperator)
        camMenu.add_separator()
        camMenu.add_command(label = "Update SSH Key", command = self.newSSHKey)
        camMenu.add_command(label = "Update AWS Key", command = self.newAWSKey)
        camMenu.add_separator()
        camMenu.add_command(label = "Check Camera", command = self.checkLastUpdate)

        ownMenu = Menu(self.menuBar, tearoff=0)
        ownMenu.add_command(label = "View Owner Data", command = self.viewOwnerData)

        self.menuBar.add_cascade(label="File", underline=0, menu=fileMenu)
        self.menuBar.add_cascade(label="Camera", underline=0, menu=camMenu)
        self.menuBar.add_cascade(label="Owners", underline=0, menu=ownMenu)

        parent.grid_columnconfigure(0, weight = 1)
        parent.grid_rowconfigure(0, weight = 1)
        self.frame = tk.Frame(self)

        self.frame.grid_columnconfigure(0, weight = 1)
        self.frame.grid_rowconfigure(0, weight = 1)
        self.sheet = Sheet(self.parent,
            page_up_down_select_row = True,
            expand_sheet_if_paste_too_big = True,
            #empty_vertical = 0,
            column_width = 120,
            startup_select = (0,1,"rows"),
            data = self.data, 
            headers = self.hdrs, 
            height = 700, 
            width = 700) 

        self.sheet.enable_bindings(("single_select", 
                                         "drag_select", 
                                    "select_all",
                                         "column_width_resize",
                                         "double_click_column_resize",
                                         "row_width_resize",
                                         "column_height_resize",
                                         "arrowkeys",
                                         "row_height_resize",
                                         "double_click_row_resize",
                                         "right_click_popup_menu",
                                         "rc_delete_row",
                                         "copy",
                                         "cut",
                                         "paste",
                                         "delete",
                                         "undo",
                                         "edit_cell"
                                    ))
        self.sheet.popup_menu_add_command("Sort by this Column", self.columns_sort)

        self.frame.grid(row = 1, column = 0, sticky = "nswe")
        self.sheet.grid(row = 0, column = 0, sticky = "nswe")
        
        self.sheet.change_theme("light green")

        self.sheet.set_all_column_widths()

        self.sheet.extra_bindings("begin_edit_cell", self.begin_edit_cell)
        self.sheet.extra_bindings("end_edit_cell", self.end_edit_cell)
        self.sheet.extra_bindings("end_delete_rows", self.end_delete_rows)
        self.sheet.extra_bindings("column_select", self.column_select)
        self.sheet.extra_bindings([("all_select_events", self.all_extra_bindings)])

        self.sheet.popup_menu_add_command('Sort', self.columns_sort, table_menu = False, index_menu = False)

    def hide_columns_right_click(self, event = None):
        currently_displayed = self.sheet.display_columns()
        exclude = set(currently_displayed[c] for c in self.sheet.get_selected_columns())
        indexes = [c for c in currently_displayed if c not in exclude]
        self.sheet.display_columns(indexes = indexes, enable = True, refresh = True)

    def all_extra_bindings(self, event):
        #print(event)
        pass

    def begin_edit_cell(self, event):
        self.oldval = self.data[event[0]][event[1]]
        # print(event)   # event[2] is keystroke
        #return event[2] # return value is the text to be put into cell edit window
        return self.oldval

    def end_edit_cell(self, event):
        self.newval = self.data[event[0]][event[1]]
        if self.newval != self.oldval and self.datachanged is False: 
            self.datachanged = True

    def end_delete_rows(self, event):
        self.datachanged = True

    def window_resized(self, event):
        pass
        #print(event)

    def mouse_motion(self, event):
        pass

    def deselect(self, event):
        print(event, self.sheet.get_selected_cells())

    def rc(self, event):
        print(event)
        
    def cell_select(self, response):
        #print(response)
        pass

    def shift_select_cells(self, response):
        #print(response)
        pass

    def drag_select_cells(self, response):
        #print (response)
        pass

    def ctrl_a(self, response):
        #print(response)
        pass

    def row_select(self, response):
        #print(response)
        pass

    def shift_select_rows(self, response):
        print(response)

    def drag_select_rows(self, response):
        pass
        #print(response)

    def columns_sort(self):
        cursel = self.sheet.get_selected_cells()
        col = list(cursel)[0][1]
        print(self.hdrs[col])
        pass
        
    def column_select(self, response):
        pass

    def shift_select_columns(self, response):
        #print(response)
        pass 

    def drag_select_columns(self, response):
        #print(response)
        pass
    
    def doSaveChanges(self):
        bkpfile = '{}.{}'.format(self.camfile, datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.copy(self.localfile, os.path.join('caminfo', bkpfile))

        newdf = pandas.DataFrame(self.data, columns=self.hdrs)
        newdf = newdf.sort_values(by=['active','camtype','camid'],ascending=[True,False,True])
        newdf.to_csv(self.localfile, index=False)

        conn = boto3.Session(profile_name=self.archprof)
        s3 = conn.client('s3')
        s3.upload_file(Bucket=self.bucket_name, Key=self.fullname, Filename=self.localfile)
        s3.upload_file(Bucket=self.bucket_name, Key=self.fullstat, Filename=self.locstatfile)
        self.uploadCfgToServer()

        return 

    def on_closing(self):
        if self.datachanged is True:
            if messagebox.askyesno("Quit", "Do you want to save changes?"):
                self.doSaveChanges()
        self.destroy()
        self.parent.quit()
        self.parent.destroy()

    def delCamera(self):
        # TODO : when active marked zero, find and deactivate corresponding row in stationdetails. 
        #        needs an active flag in that file
        tk.messagebox.showinfo(title="Information", message='To remove a camera, set Active=current date yyyymmdd')
        return

    def delOperator(self):
        tk.messagebox.showinfo(title="Information", message='Not implemented yet')
        return
    
    def viewOwnerData(self):
        statOwnerDialog(self, self.statfile)
        return

    def moveCamera(self):
        self.addCopyCamera(move=True)
        return
    
    def checkLastUpdate(self):
        cursel = self.sheet.get_selected_cells()
        cr = list(cursel)[0][0]
        curdata = self.data[cr]
        camid = curdata[1]
        lastupd = getCamUpdateDate(camid)
        msg = f'{camid} last sent a live image on {lastupd}'
        tk.messagebox.showinfo(title="Information", message=msg)
        return 

    def addCamera(self):
        self.addCopyCamera(move=False)
        return 

    def addCopyCamera(self, move=False):
        cursel = self.sheet.get_selected_cells()
        cr = list(cursel)[0][0]
        curdata = self.data[cr]
        user,email = getUserDetails(self.statfile, curdata[1])
        if move is True:
            sshkey = getSSHkey(curdata[0], curdata[3])
            id = curdata[1]
            title = 'Move Camera'
            oldloc = curdata[0].lower() + '_' + curdata[3].lower()
        else:
            sshkey = ''
            id = ''
            title = 'Add Camera'
            oldloc = ''
        answer = infoDialog(self, title, curdata[0], user, email, sshkey, id)
        if answer.data[0].strip() != '': 
            d = answer.data
            rmsid = str(d[0]).upper()
            location = str(d[1]).capitalize()
            cameraname = d[1].lower() + '_' + d[2].lower()
            with open(os.path.join('sshkeys', cameraname + '.pub'), 'w') as outf:
                outf.write(d[5])
            rowdata=[d[1],d[0],d[0],d[2],'2',d[0],'1']
            self.sheet.insert_row(values=rowdata, idx=0)
            addNewAwsUser(location)
            createIniFile(cameraname)
            addNewUnixUser(location, cameraname, oldloc)
            addNewOwner(self.locstatfile, rmsid, location, d[3], d[4])
            self.datachanged = True
        return 

    def newSSHKey(self):
        cursel = self.sheet.get_selected_cells()
        cr = list(cursel)[0][0]
        curdata = self.data[cr]
        user,email = getUserDetails(self.statfile, curdata[1])
        sshkey = ''
        id = ''
        title = 'Update SSH Key'
        answer = infoDialog(self, title, curdata[0], user, email, sshkey, id)
        if answer.data[0].strip() != '': 
            d = answer.data
            location = str(d[1]).capitalize()
            cameraname = d[1].lower() + '_' + d[2].lower()
            with open(os.path.join('sshkeys', cameraname + '.pub'), 'w') as outf:
                outf.write(d[5])
            addNewUnixUser(location, cameraname, updatemode=2)
            self.datachanged = True
        return 

    def newAWSKey(self):
        cursel = self.sheet.get_selected_cells()
        cr = list(cursel)[0][0]
        curdata = self.data[cr]
        location = curdata[0]
        createNewAwsKey(location, self.caminfo)

    def uploadCfgToServer(self):
        server=os.getenv('HELPERSERVER', default='ukmonhelper')
        user='ec2-user'
        k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/ukmonhelper'))
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(hostname = server, username = user, pkey = k)
        scpcli = SCPClient(c.get_transport())
        # push the raw keyfile
        scpcli.put(self.localfile, 'prod/data/consolidated/')
        scpcli.put(self.locstatfile, 'prod/data/admin/')
        return


def updateKeyfile(caminfo, location):
    server=os.getenv('HELPERSERVER', default='ukmonhelper')
    user='ec2-user'
    keyf = os.path.join('jsonkeys', location + '.key')
    currkey = json.load(open(keyf, 'r'))
    keyid = currkey['AccessKey']['AccessKeyId']
    secid = currkey['AccessKey']['SecretAccessKey']
    affectedcamlist = caminfo[caminfo.site == location]
    k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/ukmonhelper'))
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname = server, username = user, pkey = k)
    scpcli = SCPClient(c.get_transport())
    # push the raw keyfile
    scpcli.put(keyf, 'keymgmt/rawkeys/live/')

    for _, cam in affectedcamlist.iterrows():
        cameraname = cam.site.lower() + '_' + cam.site.lower()
        # get live.key for the camera
        livef=f'/var/sftp/{cameraname}/live.key'
        localf = f'./keys/{location.lower()}.key'
        scpcli.get(livef, localf)
        # replace the key and secret
        lis = open(localf, 'r').readlines()
        newlis=[]            
        for li in lis:
            if 'AWS_ACCESS_KEY_ID' in li:
                newlis.append(f'export AWS_ACCESS_KEY_ID={keyid}\n')
            if 'AWS_SECRET_ACCESS_KEY' in li:
                newlis.append(f'export AWS_SECRET_ACCESS_KEY={secid}\n')
            else:
                newlis.append(li)
        with open(localf, 'w') as outf:
            for li in newlis:
                outf.write(li)
        # reupload it to the central loc
        scpcli.put(localf, 'keymgmt/live/')
        command = f'sudo cp keymgmt/live/{location.lower()}.key /var/sftp/{cameraname}/'
        print(f'running {command}')
        _, stdout, stderr = c.exec_command(command, timeout=10)
        for line in iter(stdout.readline, ""):
            print(line, end="")
        for line in iter(stderr.readline, ""):
            print(line, end="")


def addNewOwner(locstatfile, rmsid, location, user, email):
    print('adding new owner')
    caminfo = pandas.read_csv(locstatfile)
    newdata = {'camid': [rmsid], 'site': [location], 'humanName':[user], 'eMail': [email]}
    newdf = pandas.DataFrame(newdata)
    caminfo = caminfo.append(newdf).sort_values(by=['camid'])
    caminfo.to_csv(locstatfile, index=False)

    archprof = os.getenv('ARCH_PROFILE', default='ukmda_admin')
    conn = boto3.Session(profile_name=archprof)
    ddb = conn.resource('dynamodb', region_name='eu-west-2')
    addRowToDDB(rmsid, location, ddb)

    liveprof = os.getenv('LIVE_PROFILE', default='ukmonshared')
    conn = boto3.Session(profile_name=liveprof)
    ddb = conn.resource('dynamodb', region_name='eu-west-1')
    addRowToDDB(rmsid, location, ddb, tblname='ukmon_camdetails')

    return


def getSSHkey(loc, dir):
    server=os.getenv('HELPERSERVER', default='ukmonhelper')
    user='ec2-user'
    tmpdir=os.getenv('TEMP', default='c:/temp')
    cameraname = (loc + '_' + dir).lower()
    k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/ukmonhelper'))
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname = server, username = user, pkey = k)
    scpcli = SCPClient(c.get_transport())
    tmpfil = os.path.join(tmpdir,'./tmp.txt')
    # dont use os.path.join - source is on unix we are on windows!
    scpcli.get(f'keymgmt/sshkeys/{cameraname}.pub', tmpfil)

    with open(tmpfil, 'r') as inf:
        lis = inf.readlines()
    #os.remove('./tmp.txt')
    return lis[0].strip()


def getUserDetails(statfile, camid):
    with open(os.path.join('caminfo', statfile),'r') as inf:
        lis = inf.readlines()
    print(camid)
    for li in lis:
        if li[:6] == camid:
            spls = li.split(',')
            print(li)
            return spls[2],spls[3]
    return '',''


def addNewUnixUser(location, cameraname, oldcamname='', updatemode=0):
    server=os.getenv('HELPERSERVER', default='ukmonhelper2')
    user='ec2-user'
    print(f'adding new Unix user {cameraname}')
    k = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/ukmonhelper'))
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname = server, username = user, pkey = k)
    scpcli = SCPClient(c.get_transport())
    scpcli.put(os.path.join('sshkeys', cameraname + '.pub'), 'keymgmt/sshkeys/')
    scpcli.put(os.path.join('keys', location.lower() + '.key'), 'keymgmt/keys/')
    scpcli.put(os.path.join('inifs', cameraname + '.ini'), 'keymgmt/inifs/')
    command = f'/home/{user}/keymgmt/addSftpUser.sh {cameraname} {location} {updatemode} {oldcamname}'
    print(f'running {command}')
    _, stdout, stderr = c.exec_command(command, timeout=10)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="")

    print('done, collecting output')
    infname = os.path.join('keymgmt/inifs/',cameraname + '.ini')
    outfname = os.path.join('./inifs', cameraname + '.ini')
    while os.path.isfile(outfname) is False:
        try:
            time.sleep(3)
            scpcli.get(infname, outfname)
        except Exception:
            continue
    return


def addNewAwsUser(location):
    print(f'adding new location {location} to AWS')
    group = 'ukmon'
    livekeyf = 'jsonkeys/' + location + '_live.key'
    archkeyf = 'jsonkeys/' + location + '_arch.key'
    liveuserdets = 'users/' + location + '_live.txt'
    archuserdets = 'users/' + location + '_arch.txt'
    livecsvf = os.path.join('csvkeys', location + '_live.csv')
    archcsvf = os.path.join('csvkeys', location + '_arch.csv')
    os.makedirs('jsonkeys', exist_ok=True)
    os.makedirs('csvkeys', exist_ok=True)
    os.makedirs('users', exist_ok=True)

    archprof = os.getenv('ARCH_PROFILE', default='ukmda_admin')
    archconn = boto3.Session(profile_name=archprof)
    liveprof = os.getenv('LIVE_PROFILE', default='ukmon-markmcintyre')
    liveconn = boto3.Session(profile_name=liveprof)
    
    iamc = liveconn.client('iam')
    sts = liveconn.client('sts')
    acct = sts.get_caller_identity()['Account']
    policyarn = 'arn:aws:iam::' + acct + ':policy/UkmonLive'
    try: 
        _ = iamc.get_user(UserName=location)
        print('location exists, not adding it')
        livekey = None
    except Exception:
        print('new location')
        usr = iamc.create_user(UserName=location)
        _ = iamc.attach_user_policy(UserName=location, PolicyArn=policyarn)
        _ = iamc.add_user_to_group(UserName=location, GroupName=group)
        with open(liveuserdets, 'w') as outf:
            outf.write(str(usr))
        livekey = iamc.create_access_key(UserName=location)
        with open(livekeyf, 'w') as outf:
            outf.write(json.dumps(livekey, indent=4, sort_keys=True, default=str))
        with open(livecsvf,'w') as outf:
            outf.write('Access key ID,Secret access key\n')
            outf.write('{},{}\n'.format(livekey['AccessKey']['AccessKeyId'], livekey['AccessKey']['SecretAccessKey']))

    iamc = archconn.client('iam')
    sts = archconn.client('sts')
    acct = sts.get_caller_identity()['Account']
    policyarn = 'arn:aws:iam::' + acct + ':policy/UkmonLive'
    policyarn2 = 'arn:aws:iam::' + acct + ':policy/UKMDA-shared'
    try: 
        _ = iamc.get_user(UserName=location)
        print('location exists, not adding it')
        archkey = None
    except Exception:
        print('new location')
        usr = iamc.create_user(UserName=location)
        _ = iamc.attach_user_policy(UserName=location, PolicyArn=policyarn)
        _ = iamc.attach_user_policy(UserName=location, PolicyArn=policyarn2)
        with open(archuserdets, 'w') as outf:
            outf.write(str(usr))
        archkey = iamc.create_access_key(UserName=location)
        with open(archkeyf, 'w') as outf:
            outf.write(json.dumps(archkey, indent=4, sort_keys=True, default=str))
        with open(archcsvf,'w') as outf:
            outf.write('Access key ID,Secret access key\n')
            outf.write('{},{}\n'.format(archkey['AccessKey']['AccessKeyId'], archkey['AccessKey']['SecretAccessKey']))
    
    if archkey is not None and livekey is not None: 
        createKeyFile(livekey, archkey, location)
    return 


def createKeyFile(livekey, archkey, location):
    archbucket = os.getenv('SRCBUCKET', default='ukmda-shared')
    livebucket = os.getenv('LIVEBUCKET', default='ukmon-live')
    webbucket = os.getenv('WEBSITEBUCKET', default='ukmda-website')

    os.makedirs('keys', exist_ok=True)
    outf = 'keys/' + location.lower() + '.key'
    with open(outf, 'w') as ouf:
        ouf.write(f"export AWS_ACCESS_KEY_ID={archkey['AccessKey']['AccessKeyId']}\n")
        ouf.write(f"export AWS_SECRET_ACCESS_KEY={archkey['AccessKey']['SecretAccessKey']}\n")
        ouf.write(f"export LIVE_ACCESS_KEY_ID={livekey['AccessKey']['AccessKeyId']}\n")
        ouf.write(f"export LIVE_SECRET_ACCESS_KEY={livekey['AccessKey']['SecretAccessKey']}\n")
        ouf.write('export AWS_DEFAULT_REGION=eu-west-1\n')
        ouf.write(f'export CAMLOC="{location}"\n')
        ouf.write(f'export S3FOLDER="archive/{location}/"\n')
        ouf.write(f'export ARCHBUCKET={archbucket}\n')
        ouf.write(f'export LIVEBUCKET={livebucket}\n')
        ouf.write(f'export WEBBUCKET={webbucket}\n')
        ouf.write('export ARCHREGION=eu-west-2\n')
        ouf.write('export LIVEREGION=eu-west-1\n')
        ouf.write('export MATCHDIR=matches/RMSCorrelate\n')
    return 


def createIniFile(cameraname):
    helperip = os.getenv('HELPERIP', default='3.11.55.160')
    os.makedirs('inifs', exist_ok=True)
    outf = 'inifs/' + cameraname + '.ini'
    with open(outf, 'w') as outf:
        outf.write('# config data for this station\n')
        outf.write(f'export LOCATION={cameraname}\n')
        outf.write(f'export UKMONHELPER={helperip}\n')
        outf.write('export UKMONKEY=~/.ssh/ukmon\n')
        outf.write('export RMSCFG=~/source/RMS/.config\n')
    return 


def createNewAwsKey(location, caminfo):
    keyf = os.path.join('jsonkeys', location + '.key')
    oldkeyf = os.path.join('jsonkeys', location + '-prev.key')
    csvf = os.path.join('csvkeys', location + '.csv')
    shutil.copyfile(keyf, oldkeyf)
    currkey = json.load(open(keyf, 'r'))
    keyid = currkey['AccessKey']['AccessKeyId']
    print(location, keyid)
    affectedcamlist = caminfo[caminfo.site == location]
    for _, cam in affectedcamlist.iterrows():
        print(cam.site.lower(), cam.sid.lower())
    return 

    iamc = boto3.client('iam')
    iamc.update_access_key(UserName=location, AccessKeyId=keyid, Status='Inactive')
    key = iamc.create_access_key(UserName=location)
    with open(keyf, 'w') as outf:
        outf.write(json.dumps(key, indent=4, sort_keys=True, default=str))
    with open(csvf,'w') as outf:
        outf.write('Access key ID,Secret access key\n')
        outf.write('{},{}\n'.format(key['AccessKey']['AccessKeyId'], key['AccessKey']['SecretAccessKey']))

    return 


if __name__ == '__main__':
    # Initialize main window
    root = tk.Tk()
    app = CamMaintenance(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
