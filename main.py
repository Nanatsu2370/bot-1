from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
#from megacli.mega import Mega
#import megacli.megafolder as megaf
#import megacli.mega
import datetime
import time
import youtube
import NexCloudClient

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
developer = 'AresDza'


def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'🤜Preparando Para Subir☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendario':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'perfil':
                             fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                bot.editMessageText(message,'❌Error En La Pagina❌')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'🤜Subiendo ☁ Espere Mientras... 😄')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,'❌Error❌\n' + str(ex))
        return None


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'🤜Preparando Archivo📄...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype']=='calendario':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'❌Error En La Pagina❌')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            megadl(update,bot,message,url,file_name,thread,jdb=jdb)

def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
        if not megadl.stoping:
            processFile(update,bot,message,file_name,thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
            if not megadl.stoping:
                processFile(update,bot,message,file_name,thread=thread)
        pass
    pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    password = os.environ.get('password')
    if developer == password :
        try :
            thread = bot.this_thread
            username = update.message.sender.username
            tl_admin_user = os.environ.get('tl_admin_user')

            #set in debug
            tl_admin_user = 'FriendXfriendss'

            jdb = JsonDatabase('database')
            jdb.check_create()
            jdb.load()

            user_info = jdb.get_user(username)

            if username == tl_admin_user or user_info :  # validate user
                if user_info is None:
                    if username == tl_admin_user:
                        jdb.create_admin(username)
                    else:
                        jdb.create_user(username)
                    user_info = jdb.get_user(username)
                    jdb.save()
            else:return


            msgText = ''
            try: msgText = update.message.text
            except:pass

            # comandos de admin
            if '/add_user' in msgText:
                isadmin = jdb.is_admin(username)
                if isadmin:
                    try:
                        user = str(msgText).split(' ')[1]
                        jdb.create_user(user)
                        jdb.save()
                        msg = '😃Genial @'+user+' ahora tiene acceso al bot👍'
                        bot.sendMessage(update.message.chat.id,msg)
                    except:
                        bot.sendMessage(update.message.chat.id,'❌Error en el comando /add_user username❌')
                else:
                    bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
                return
            if '/add_admin' in msgText:
                isadmin = jdb.is_admin(username)
                if isadmin:
                    try:
                        user = str(msgText).split(' ')[1]
                        jdb.create_admin(user)
                        jdb.save()
                        msg = '😃Genial @'+user+' ahora es Admin del BOT'
                        bot.sendMessage(update.message.chat.id,msg)
                    except:
                        bot.sendMessage(update.message.chat.id,'❌Error en el comando /add_admin username❌')
                else:
                    bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
                return
            if '/kick_user' in msgText:
                isadmin = jdb.is_admin(username)
                if isadmin:
                    try:
                        user = str(msgText).split(' ')[1]
                        if user == username:
                            bot.sendMessage(update.message.chat.id,'❌No Se Puede Expulsar Usted❌')
                            return
                        jdb.remove(user)
                        jdb.save()
                        msg = '🦶Fuera @'+user+' Expulsado❌'
                        bot.sendMessage(update.message.chat.id,msg)
                    except:
                        bot.sendMessage(update.message.chat.id,'❌Error en el comando /kick_user username❌')
                else:
                    bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
                return
            if '/getdb' in msgText:
                isadmin = jdb.is_admin(username)
                if isadmin:
                    bot.sendMessage(update.message.chat.id,'Base De Datos👇')
                    bot.sendFile(update.message.chat.id,'database.jdb')
                else:
                    bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
                return
            # end

            # comandos de usuario
            if '/tutorial' in msgText:
                tuto = open('tuto.txt','r')
                bot.sendMessage(update.message.chat.id,tuto.read())
                tuto.close()
                return
            if '/myuser' in msgText:
                getUser = user_info
                if getUser:
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
                    return
            if '/zips' in msgText:
                getUser = user_info
                if getUser:
                    try:
                       size = int(str(msgText).split(' ')[1])
                       getUser['zips'] = size
                       jdb.save_data_user(username,getUser)
                       jdb.save()
                       msg = '😃Genial los zips seran de '+ sizeof_fmt(size*1024*1024)+' las partes👍'
                       bot.sendMessage(update.message.chat.id,msg)
                    except:
                       bot.sendMessage(update.message.chat.id,'❌Error en el comando /zips size❌')
                    return
            if '/account' in msgText:
                try:
                    account = str(msgText).split(' ',2)[1].split(',')
                    user = account[0]
                    passw = account[1]
                    getUser = user_info
                    if getUser:
                        getUser['moodle_user'] = user
                        getUser['moodle_password'] = passw
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /account user,password❌')
                return
            if '/host' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    host = cmd[1]
                    getUser = user_info
                    if getUser:
                        getUser['moodle_host'] = host
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /host moodlehost❌')
                return
            if '/repoid' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    repoid = int(cmd[1])
                    getUser = user_info
                    if getUser:
                        getUser['moodle_repo_id'] = repoid
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /repo id❌')
                return
            if '/cloud' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    repoid = cmd[1]
                    getUser = user_info
                    if getUser:
                        getUser['cloudtype'] = repoid
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /cloud (moodle or cloud)❌')
                return
            if '/uptype' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    tipo = cmd[1]
                    getUser = user_info
                    if getUser:
                        if  tipo == 'evidence' or tipo == 'draft' or tipo == 'perfil' or tipo == 'blog':
                            getUser['uploadtype'] = tipo
                            jdb.save_data_user(username,getUser)
                            jdb.save()
                            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                            bot.sendMessage(update.message.chat.id,statInfo)
                        elif tipo == 'calendar' or tipo == 'calendario':
                            getUser['uploadtype'] = 'calendario'
                            jdb.save_data_user(username,getUser)
                            jdb.save()
                            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                            bot.sendMessage(update.message.chat.id,statInfo)
                        else :
                            bot.sendMessage(update.message.chat.id,'✖️Tienes que poner uno de estos Métodos de Subidas ✖️\n↖️ evidence  -  draft  -  perfil  -  blog  -  calendar o calendario')
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /uptype (typo de subida (evidence,draft,blog))❌')
                return

            if '/view_proxy' in msgText:
                try:
                    getUser = user_info
                    
                    if getUser:
                        proxy = getUser['proxy']
                        bot.sendMessage(update.message.chat.id,proxy)
                except:
                    if user_info:
                        proxy = user_info['proxy']
                        bot.sendMessage(update.message.chat.id,proxy)
                return
            
            if '/search_proxy' in msgText:
                msg_start = 'Buscando Proxy'
                bot.sendMessage(update.message.chat.id,msg_start)
                print("Buscando proxy...")
                for port in range(2080,2085):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('181.225.253.188',port))  
                    
                    if result == 0:
                        print ("Puerto abierto!")
                        print (f"Puerto: {port}")  
                        proxy = f'181.225.253.188:{port}'
                        proxy_new = S5Crypto.encrypt(f'{proxy}')
                        msg = 'Su nuevo proxy es:\n\nsocks5://' + proxy_new
                        bot.sendMessage(update.message.chat.id,msg)
                        break
                    else: 
                        print ("Error...Buscando...")
                        print (f"Buscando en el puerto: {port}")
                        sock.close()
                return

            if '/encriptar_proxy' in msgText:
                proxy_sms = str(msgText).split(' ')[1]
                proxy = S5Crypto.encrypt(f'{proxy_sms}')
                bot.sendMessage(update.message.chat.id, f'🔒Encriptado Completado:\n{proxy}')
                return
            
            if '/desencriptar_proxy' in msgText:
                proxy_sms = str(msgText).split(' ')[1]
                proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
                bot.sendMessage(update.message.chat.id, f'🔓Desencriptado Completado:\n{proxy_de}')
                return
            
            if '/proxy' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    proxy = cmd[1]
                    getUser = user_info
                    if getUser:
                        getUser['proxy'] = proxy
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    if user_info:
                        user_info['proxy'] = ''
                        statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                return
            if '/del_proxy' in msgText:
                try:
                    getUser = user_info
                    if getUser:
                        getUser['proxy'] = ''
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        succes_msg = 'PROXY ELIMINADO CON ÉXITO ....'
                        bot.sendMessage(update.message.chat.id,succes_msg)
                except:
                    if user_info:
                        user_info['proxy'] = ''
                        statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                return
            
            if '/dir' in msgText:
                try:
                    cmd = str(msgText).split(' ',2)
                    repoid = cmd[1]
                    getUser = user_info
                    if getUser:
                        getUser['dir'] = repoid + '/'
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /dir folder❌')
                return
            if '/cancel_' in msgText:
                try:
                    cmd = str(msgText).split('_',2)
                    tid = cmd[1]
                    tcancel = bot.threads[tid]
                    msg = tcancel.getStore('msg')
                    tcancel.store('stop',True)
                    time.sleep(3)
                    bot.editMessageText(msg,'❌Tarea Cancelada❌')
                except Exception as ex:
                    print(str(ex))
                return
            #end

            message = bot.sendMessage(update.message.chat.id,'⏳ Cargando ...')

            thread.store('msg',message)

            if '/start' in msgText:
                start_msg = '✅BIENVENIDO✅🔱Estas usando #RTFree la cadena de bot para subir y descargar de la nube sin consumo de MB. 🌀Disfruta de tu estancia en el bot.\n⚠️Si quiere contactar con los dueños pq posee alguna duda escribanos😁 @rockstar984 o @TuguerX\n\n👾Code por: @AresDza'
                bot.editMessageText(message,start_msg)
            elif '/files' == msgText and user_info['cloudtype']=='moodle':
                 proxy = ProxyCloud.parse(user_info['proxy'])
                 client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],proxy=proxy)
                 loged = client.login()
                 if loged:
                        List = client.getEvidences()
                        List1=List[:45]
                        total=len(List)
                        List2=List[46:]
                        info1 = f'<b>Archivos: {str(total)}</b>\nEliminar todo: /del_all\n\n'
                        info = f'<b>Archivos: {str(total)}</b>\nEliminar todo: /del_all\n\n'
                        
                        i = 1
                        for item in List1:
                            info += '<b>/del_'+str(i)+'</b>\n'
                            for file in item['files']:                  
                                info += '<a href="'+file['directurl']+'">\t'+file['name']+'</a>\n'
                            info+='\n'
                            i+=1
                            bot.editMessageText(message, f'{info}',parse_mode="html")
                
                        if len(List2)>0:
                            bot.sendMessage(update.message.chat.id,'Conectando con Lista número 2...')
                            for item in List2:
                        
                                info1 += '<b>/del_'+str(i)+'</b>\n'
                                for file in item['files']:                  
                                    info1 += '<a href="'+file['url']+'">\t'+file['name']+'</a>\n'
                                info1+='\n'
                                i+=1
                                bot.editMessageText(message, f'{info1}',parse_mode="html")
                 else:
                    bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
            elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
                 findex = str(msgText).split('_')[1]
                 findex = int(findex)
                 proxy = ProxyCloud.parse(user_info['proxy'])
                 client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],proxy=proxy)
                 loged = client.login()
                 if loged:
                     evidences = client.getEvidences()
                     evindex = evidences[findex]
                     txtname = evindex['name']+'.txt'
                     sendTxt(txtname,evindex['files'],update,bot)
                     client.logout()
                     bot.editMessageText(message,'TxT Aqui👇')
                 else:
                    bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
                 pass
            elif '/del_' in msgText and user_info['cloudtype']=='moodle':
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    evfile = client.getEvidences()[findex]
                    client.deleteEvidence(evfile)
                    client.logout()
                    bot.editMessageText(message,'🗑Archivo Eliminado Correctamente🗑')
                else:
                    bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
            elif 'http' in msgText:
                url = msgText
                ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            else:
                #if update:
                #    api_id = os.environ.get('api_id')
                #    api_hash = os.environ.get('api_hash')
                #    bot_token = os.environ.get('bot_token')
                #    
                # set in debug
                #    api_id = 7386053
                #    api_hash = '78d1c032f3aa546ff5176d9ff0e7f341'
                #    bot_token = '5124841893:AAH30p6ljtIzi2oPlaZwBmCfWQ1KelC6KUg'

                #    chat_id = int(update.message.chat.id)
                #    message_id = int(update.message.message_id)
                #    import asyncio
                #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
                #    return
                bot.editMessageText(message,'🛑 Error al Intentar leer como una URL 🛑')
        except Exception as ex:
               print(str(ex))


def main():
    bot_token = '5233279296:AAH1UHHO4xGJRUeANARpuUrLTzQ3jxBP6b8'


    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
