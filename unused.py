def syncalloldbytros():
    """Unused: inefficient O(N) database writes"""
    global bytroidx
    global bytrolist
    bytroidx = 0
    bytcount = 0
    count = 0
    isAddBytroFail = False
    bytflag = True
    isFirstBytro = True
    absdirlist = glob.glob(imgdir + '*')
    absdirlist = sorted(absdirlist)
    for absdir in absdirlist:  # for all bytro folders
        print('')
        print('=>', absdir)
        bytroname = os.path.basename(absdir)
        if not os.path.isdir(absdir):
            print('Bytro Failure (unexpected file name) occurred!')
            continue
        if bytroname in bytrolist:
            bytid = getbytroid(bytroname)
        else:
            bytid = addbytro(bytroname)
            bytrolist.append(bytroname)
        if bytid <= 0:
            isAddBytroFail = True
            print('Add/Get Bytro Failure occurred!')
            continue
        if isFirstBytro:
            bytflag = getbytroflag(bytid)
        isFirstBytro = False
        count += syncbytro(bytcount)
        bytcount += 1
        setbytroflag(bytid, not bytflag)
        print('bottom of bytro 1st outer loop')
    delcount = 0
    bytrolist = sorted(bytrolist)
    for bytroname in bytrolist:
        bytid = getbytroid(bytroname)
        flag = getbytroflag(bytid)
        if flag == bytflag:
            proidlist = getallproidlist(bytid)
            for proid in proidlist:
                imgidlist = getallimgidlist(proid)
                for imgid in imgidlist:
                    delimg(imgid)
                    delcount += 1
                delpicro(proid)
            delbytro(bytid)
        print('bottom of bytro 2nd outer loop')
    print('bytro del count = ', delcount)
    print('bytro count = ', bytcount)
    if isAddBytroFail:
        print('Final: Add/Get Bytro Failure occurred!')
    return count

def syncbytro(bytroidx):
    """Unused: inefficient O(N) database writes"""
    bytroname = bytrolist[bytroidx]
    bytid = getbytroid(bytroname)
    picrolist = getpicrolist(bytid)
    picrocount = len(picrolist)
    print('Sync bytro: bytro name =', bytroname)
    print('Sync bytro: picro count =', picrocount)
    count = 0
    badcount = 0
    picroidx = 0
    isAddPicroFail = False
    isAddImgFail = False
    allvalid = True
    isFirstPicro = True
    proflag = True
    imd = imgdir + bytroname
    absdirlist = glob.glob(imd + sepch + '*')
    absdirlist = sorted(absdirlist)
    for absdir in absdirlist:  # for all picro folders
        print('')
        print('>', absdir)
        picroidx += 1
        picroname = os.path.basename(absdir)
        if not os.path.isdir(absdir):
            print('Picro Failure (unexpected file name) occurred!')
            continue
        proid = getproid(bytid, picroname)
        if isFirstPicro:
            proflag = getpicroflag(proid)
        isFirstPicro = False
        if picroname not in picrolist: 
            proid = addpicro(bytid, picroname)
            if proid <= 0:
                isAddPicroFail = True
                print('Add Picro Failure occurred!')
                continue
        subdir = absdir
        imgtuple = getimglistpair(proid, True)
        imgreclist = imgtuple[0]
        imgcorelist = imgtuple[1]
        if len(imgreclist) > 0:
            filename = imgreclist[0]
            imgid = getimgidcore(proid, filename, False)
            imgflag = getimgflag(imgid)
        elif len(imgcorelist) > 0:
            filename = imgcorelist[0]
            imgid = getimgidcore(proid, filename, True)
            imgflag = getimgflag(imgid)
        else:
            imgflag = True
        for j in range(2):
            imglist = []
            absimglist = getimglist(subdir)
            # for each image file in picro
            for absimg in absimglist:
                filename = os.path.basename(absimg)
                if os.path.isdir(absimg):
                    continue
                # only gather valid image filenames containing printable chars.
                if not isValidAsciiStr(filename):
                    allvalid = False
                    badcount += 1
                    continue
                imglist.append(filename)
            imglist = sorted(imglist)
            listsiz = len(imglist)
            count += listsiz
            print('%d images in folder' % listsiz)
            for i in range(len(imglist)):
                filename = imglist[i]
                iscore = (j > 0)
                if iscore:
                    if filename in imgcorelist:
                        imgid = getimgid(proid, filename)
                    else:
                        imgid = addimg(proid, filename, iscore)
                elif filename in imgreclist:
                    imgid = getimgid(proid, filename)
                else:
                    imgid = addimg(proid, filename, iscore)
                if imgid > 0:
                    setimgflag(imgid, not imgflag)
                else:
                    isAddImgFail = True
                    print('Add Img Failure occurred!')
                    continue
                outdot(i + 1, filename)
            corename = subdir + sepch + dotchar
            if not os.path.isdir(corename):
                break
            subdir = corename
            if j < 1:
                print('')
                print('>>', subdir)
            print('')
        delcount = 0
        for filename in imgreclist:
            imgid = getimgidcore(proid, filename, False)
            flag = getimgflag(imgid)
            if flag == imgflag:
                delimg(imgid)
                delcount += 1
        delcorecount = 0
        for filename in imgcorelist:
            imgid = getimgidcore(proid, filename, True)
            flag = getimgflag(imgid)
            if flag == imgflag:
                delimg(imgid)
                delcorecount += 1
        setpicroflag(proid, not proflag)
        print('')
        print('del counts = (%d, %d)' % (delcount, delcorecount))
        print('len imgreclist = ', len(imgreclist))
        print('bottom of 1st outer loop')
    print('')
    delcount = 0
    for filename in picrolist:
        proid = getproid(bytid, filename)
        flag = getpicroflag(proid)
        if flag == proflag:
            imgidlist = getallimgidlist(proid)
            for imgid in imgidlist:
                delimg(imgid)
                delcount += 1
            delpicro(proid)
        print('bottom of 2nd outer loop')
    print('outer del count = ', delcount)
    if not allvalid:
        print('%d invalid image file name(s) found!' % badcount)
    if isAddPicroFail:
        print('Final: Add Picro Failure occurred!')
    if isAddImgFail:
        print('Final: Add Img Failure occurred!')
    return count

def getbytroflag(bytid):
    """Return flag of bytrotab rec. having a given id."""
    db = get_db()
    cur = db.execute('select id, flag from bytrotab ' + \
        'where id = %d' % bytid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return False
    row = rows[0]
    bytroflag = row[1]
    return bytroflag

def getpicroflag(proid):
    """Return flag of picrotab rec. having a given id."""
    db = get_db()
    cur = db.execute('select id, flag from picrotab ' + \
        'where id = %d' % proid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return False
    row = rows[0]
    picroflag = row[1]
    return picroflag

def getimgflag(imgid):
    """Return flag of imgtab rec. having a given id."""
    db = get_db()
    cur = db.execute('select id, flag from imgtab ' + \
        'where id = %d' % imgid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return False
    row = rows[0]
    flag = row[1]
    return flag

def setimgflag(imgid, flag):
    """Set flag of img rec."""
    if flag:
        isflagbit = 1
    else:
        isflagbit = 0
    db = get_db()
    qry = 'update imgtab set flag = %d where id = %d ' % (isflagbit, imgid)
    db.execute(qry)
    db.commit()

def setpicroflag(proid, flag):
    """Set flag of picro rec."""
    if flag:
        isflagbit = 1
    else:
        isflagbit = 0
    db = get_db()
    qry = 'update picrotab set flag = %d where id = %d ' % (isflagbit, proid)
    db.execute(qry)
    db.commit()

def setbytroflag(bytid, flag):
    """Set flag of bytro rec."""
    if flag:
        isflagbit = 1
    else:
        isflagbit = 0
    db = get_db()
    qry = 'update bytrotab set flag = %d where id = %d ' % (isflagbit, bytid)
    db.execute(qry)
    db.commit()

####################################################################

def addfolder(parid, dirname):
    """Add new dir rec. & return its dirid
    """
    db = get_db()
    db.execute('insert into dirs (parid, dirname, firstid, emptyid, isdel) values (?, ?, ?, ?, ?)',
        [parid, dirname, 0, 0, False])
    db.commit()
    return getfolderid(parid, dirname)
    
def getfolderid(parid, dirname):
    """Return dirid of dir rec. having a given parid & dir name."""
    db = get_db()
    cur = db.execute('select dirid, parid, dirname from dirs ' + \
        ('where parid = %d and dirname = "' % parid) + dirname + '"')
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    dirid = row[0]
    return dirid

def getfirstemptyids(dirid):
    """Return first/empty ids of dir rec."""
    db = get_db()
    cur = db.execute('select dirid, firstid, emptyid from dirs ' + \
        'where dirid = %d' % dirid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return (0, 0)
    row = rows[0]
    firstid = row[1]
    emptyid = row[2]
    return (firstid, emptyid)

def setfirstemptyids(dirid, firstid, emptyid):
    """Set first/empty ids of dir rec. = dirid."""
    db = get_db()
    qry = 'update dirs set firstid = %d, emptyid = %d where dirid = %d ' % (firstid, emptyid, dirid)
    db.execute(qry)
    db.commit()

def getimgrows(dirid):
    """Return list of img recs. all having same dirid."""
    db = get_db()
    cur = db.execute('select imgid, dirid, filename, nextid, isdel from images ' + \
        'where dirid = %d' % dirid)
    rows = cur.fetchall()
    return rows

def getdirrows(dirid):
    """Return list of dir recs. all having same parid."""
    db = get_db()
    cur = db.execute('select dirid, parid, dirname, firstid, emptyid, isdel from dirs ' + \
        'where parid = %d' % dirid)
    rows = cur.fetchall()
    return rows

def getnextid(imgid):
    """Return nextid from img rec."""
    db = get_db()
    cur = db.execute('select imgid, nextid from images where imgid = %d' % imgid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return -1
    row = rows[0]
    imgid = row[0]
    nextid = row[1]
    return nextid

def setnextid(imgid, nextid):
    """Set nextid of img rec."""
    db = get_db()
    qry = 'update images set nextid = %d where imgid = %d ' % (nextid, imgid)
    db.execute(qry)
    db.commit()

def setisdel(imgid, isdel):
    """Set isdel bit of img rec."""
    if isdel:
        isdelbit = 1
    else:
        isdelbit = 0
    db = get_db()
    qry = 'update images set isdel = %d where imgid = %d ' % (isdelbit, imgid)
    db.execute(qry)
    db.commit()

def isdelimage(imgid):
    """Return isdel flag of img rec."""
    db = get_db()
    cur = db.execute('select imgid, isdel from images where imgid = %d' % imgid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return False
    row = rows[0]
    imgid = row[0]
    isdel = row[1]
    return isdel

def undelimage(imgid, emptyid):
    """Remove img rec. from empty rec. list
    
    return emptyid (head of empty rec. list) if unchanged,
    otherwise return new emptyid
    """
    lastid = -1
    currid = emptyid
    while (currid >= 0) and (currid != imgid):
        lastid = currid
        currid = getnextid(currid)
    if currid != imgid:
        return emptyid
    currid = getnextid(currid)
    if lastid < 0:
        return currid
    setnextid(lastid, currid)
    return emptyid

