import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Markup
from contextlib import closing
import glob
import os

cr = '%c' % 10
dotchar = '$'
uscore = '_'
progresschar = '*'
dgmode = 0
DIRGRID = 1
SUBGRID = 2
FOLDR_RIGHT = '-11'
FOLDR_LEFT = '-12'
FACES_PORT = 6996
foldridx = 0
nameidx = 0
pageidx = 0
dnameidx = 0
dpageidx = 0
pagesize = 18  # const
sfcount = 0
debug = False
isrecursion = False
isalldirs = True
isgendir = True
sepch = os.sep
faceskey = 'FACES_PATH'
rootfolder = 'pixroot'
#staticdir = '/static/pixroot/'
dirlist = []
dirimglist = []
dirsublist = []

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# inz path constants
facespath = os.getenv(faceskey, '')
staticdir = os.path.join('static', rootfolder)
staticdir = sepch + staticdir + sepch
imgroot = facespath + staticdir
imgdir = imgroot
locport = 'localhost:%d' % FACES_PORT

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'faces.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FACES_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    print 'About to Initialize the database.'
    init_db()
    print 'Initialized the database.'
    
def gendirinfo(imd):
    """Populate image/file/dir lists."""
    global dirlist
    global dirimglist
    global dirsublist
    global imgdir
    if not isalldirs:
        gendirinfofast(imd)
        return
    imgdir = imd
    dirlist = []
    dirimglist = []
    dirsublist = []
    filelist = []
    absdirlist = glob.glob(imgdir + '*')
    absdirlist = sorted(absdirlist)
    # for each subdirectory (full dir names)
    for absdir in absdirlist:
        dirname = os.path.basename(absdir)
        if not os.path.isdir(absdir):
            filename = dirname
            if debug:
                print 'filename:', filename
            # filelist contains files, not dirs.
            filelist.append(filename)
            continue
        if debug:
            print 'dirname:', dirname
        # dirlist contains dirs., not files
        dirlist.append(dirname)
        imglist = []
        absimglist = getimglist(absdir)
        # for each image file in subdirectory
        for absimg in absimglist:
            filename = os.path.basename(absimg)
            if debug:
                print filename
            # only gather valid image filenames containing printable chars.
            if isValidAsciiStr(filename):
                imglist.append(filename)
        imglist = sorted(imglist)
        if debug:
            print 'imglist:', imglist
        # dirimglist contains a list of lists of image filenames
        dirimglist.append(imglist)
        subdirlist = getsubdirlist(absdir, True)
        subdirlist = sorted(subdirlist)
        # subdirlist contains list of subdirectories of this subdirectory
        # dirsublist contains list of all subdirlist lists
        dirsublist.append(subdirlist)
    if len(filelist) > 0:
        # files found in image directory
        # append $ to list of dirs. (= current dir.)
        dirlist.append(dotchar)
        filelist = sorted(filelist)
        dirimglist.append(filelist)
        dirsublist.append([])
    if debug:
        print 'dirimglist:', dirimglist
        print 'dirsublist:', dirsublist
        print '   dirlist:', dirlist

def gendirinfofast(imd):
    """Populate image/file/dir lists (use faces.db)."""
    global dirlist
    global dirimglist
    global dirsublist
    global imgdir
    imgdir = imd
    dirlist = []
    dirimglist = []
    dirsublist = []
    filelist = []
    # dir recs. of ancestors may be added
    dirid = getdiridfull(imgdir)
    rows = getimgrows(dirid)
    for row in rows:
        filename = row[2]
        isdel = row[4]
        if not isdel:
            # gather non-empty img file names
            filelist.append(filename)
    rows = getdirrows(dirid)
    # for all subdirectories
    for row in rows:
        dirid = row[0]
        dirname = row[2]
        isdel = row[5]
        if isdel:
            # ignore empty dir recs.
            continue
        # gather non-empty dir names
        dirlist.append(dirname)
        imglist = []
        absdir = imgdir + dirname
        subrows = getimgrows(dirid)
        # for all img files in subdirectory
        for subrow in subrows:
            filename = subrow[2]
            isdel = subrow[4]
            if not isdel:
                # gather non-empty img filenames
                imglist.append(filename)
        imglist = sorted(imglist)
        # dirimglist contains a list of lists of image filenames
        dirimglist.append(imglist)
        subdirlist = []
        subrows = getdirrows(dirid)
        for subrow in subrows:
            dirname = subrow[2]
            isdel = subrow[5]
            if not isdel:
                subdirlist.append(dirname)
        subdirlist = sorted(subdirlist)
        dirsublist.append(subdirlist)
    if len(filelist) > 0:
        dirlist.append(dotchar)
        filelist = sorted(filelist)
        dirimglist.append(filelist)
        dirsublist.append([])
    if debug:
        print 'dirimglist:', dirimglist
        print 'dirsublist:', dirsublist
        print '   dirlist:', dirlist

def getimglist(absdir):
    """Return image full filenames contained in dir."""
    absdir_sep = absdir + sepch
    absimglist = \
        glob.glob(absdir_sep + '*.jpg') + \
        glob.glob(absdir_sep + '*.jpeg') + \
        glob.glob(absdir_sep + '*.png') + \
        glob.glob(absdir_sep + '*.gif') + \
        glob.glob(absdir_sep + '*.bmp')
    return absimglist
    
def getsubdirlist(absdir, verbose):
    """Return list of dir. names contained in dir."""
    subdirlist = []
    absdir_sep = absdir + sepch
    absfilelist = glob.glob(absdir_sep + '*' + sepch)
    for absfile in absfilelist:
        filename = os.path.basename(absfile)
        if filename == '':
            filename = os.path.basename(absfile[:-1])
            if verbose and debug:
                print 'subdir:', filename
            subdirlist.append(filename)
    return subdirlist

@app.route('/foldr/')
@app.route('/foldr/<adir>')
def foldr(adir=None):
    """Handle folder template: unordered list of directories."""
    if debug:
        print 'top of foldr'
    global imgdir
    global foldridx
    global dgmode
    global isrecursion
    global isalldirs
    global isgendir
    global sfcount
    imgcount = -2
    if isgendir:
        gendirinfo(imgdir)
    isgendir = True
    if adir != None:
        idir = int(adir)
    if adir == None:
        pass
    elif adir == FOLDR_RIGHT:
        foldridx += 1
        isgendir = False
    elif adir == FOLDR_LEFT:
        foldridx += len(dirlist) - 1
        isgendir = False
    elif adir == "0":  # up arrow
        # go to parent folder
        parentdir = imgdir[:-1]
        parent = os.path.basename(parentdir)
        if debug:
            print parent
        if imgdir != imgroot:
            imgdir = os.path.dirname(parentdir) + sepch
        gendirinfo(imgdir)
        foldridx = 0
    elif adir == "-1":  # Enter
        # go down a level in tree
        foldername = dirlist[foldridx]
        if debug:
            print 'foldr: foldername =', foldername
        ch = foldername[-1]  # last ch. of folder name
        subdirlist = dirsublist[foldridx]
        if ch == uscore:
            if debug:
                print 'foldr: ch == uscore'
            initpgnamidx()
            dgmode = DIRGRID
        elif len(subdirlist) == 0:
            initpgnamidx()
            dgmode = 0
            return redirect(url_for('grid'))
        # handle list of subdirectories...
        imgdir = os.path.join(imgdir, dirlist[foldridx]) + sepch
        if debug:
            print 'imgdir =', imgdir
        gendirinfo(imgdir)
        foldridx = 0
        if ch == uscore:
            return redirect(url_for('dgrid'))
    elif adir == "-3":  # up arrow from lower level grid
        dgmode = 0
        parentdir = imgdir[:-1]
        parent = os.path.basename(parentdir)
        if debug:
            print parent
        if imgdir != imgroot:
            imgdir = os.path.dirname(parentdir) + sepch
        gendirinfo(imgdir)
        foldridx = 0
    elif (adir == "-4") or (adir == "-5"):  # SYNC or PACK
        foldername = dirlist[foldridx]
        fulldirname = os.path.join(imgdir, foldername) + sepch
        absimglist = getimglist(fulldirname)
        subdirlist = getsubdirlist(fulldirname, False)
        ispack = (adir == "-5")
        sfcount = 0
        imgcount, emptycount = syncfolder(fulldirname, \
            absimglist, subdirlist, isrecursion, ispack)
    elif adir == "-6":  # toggle recursion flag
        isrecursion = not isrecursion
    elif adir == "-7":  # toggle all-directories flag
        isalldirs = not isalldirs
        foldridx = 0
        # if all dirs flag then slow gendirinfo:
        #   don't use faces.db when populating img/dir lists
        # else use fast gendirinfofast:
        #   use faces.db when populating those lists
    elif idir > 0:
        foldridx = idir - 1

    foldridx = getpgidxofcount(foldridx, len(dirlist))
    udirlist = '<ul>'
    for i in range(len(dirlist)):
        dirname = dirlist[i]
        iscurrline = (i == foldridx)
        if iscurrline:
            j = -1
        else:
            j = i + 1
        imgtag = ('<a href="/foldr/%d">' % j) + dirname + '</a>'
        # current dir name line is selected
        if iscurrline:
            # allow user to SYNC or PACK or toggle 2 flags
            synctag = '<a href="/foldr/-4">SYNC</a>'
            packtag = '<a href="/foldr/-5">PACK</a>'
            if isrecursion:
                recuryesno = 'Y'
            else:
                recuryesno = 'N'
            if isalldirs:
                alldirsyesno = 'Y'
            else:
                alldirsyesno = 'N'
            recurtag = '<a href="/foldr/-6">' + recuryesno + '</a>'
            alldirstag = '<a href="/foldr/-7">' + alldirsyesno + '</a>'
            imgtag = '[ ' + imgtag + ' ] [ ' + synctag + ' ] [ ' + \
                packtag + ' ] recursion = [' + recurtag + '] ' + \
                'all = [' + alldirstag + '] '
            if imgcount >= -1:
                imgtag += '(%d, %d)' % (imgcount, emptycount)
        imgtag = '<li>' + imgtag + '</li>'
        udirlist += cr + imgtag
    udirlist += cr + '</ul>'
    jdir = imgdir
    while True:
        parentdir = jdir[:-1]
        parent = os.path.basename(parentdir)
        if debug:
            print parent
        udirlist = '<ul>' + cr + '<li>' + parent + cr + udirlist + cr + \
            '</li>' + cr + '</ul>'
        if jdir == imgroot:
            break
        jdir = os.path.dirname(parentdir) + sepch
    if debug:
        print udirlist
    udirlist = Markup(udirlist)
    if debug:
        print 'btm of foldr'
    return render_template('foldr.html', udirlist=udirlist)

def getdiridfull(fulldirname):
    """Return dirid of dir. & add ancestor dir recs. if non-existent
    
    should not return zero
    """
    parid = 0
    pardirspath = getpardirspath(fulldirname)
    dirlist = pathtolist(pardirspath)
    dirlist.append(rootfolder)
    dirlist.reverse()
    # sync ancestor folders:
    for dirname in dirlist:
        dirid = getfolderid(parid, dirname)
        if debug:
            print 'getdiridfull: dirname = ', dirname, ', dirid = ', dirid
        if dirid == 0:
            dirid = addfolder(parid, dirname)
            if dirid > 0:
                #imgcount += 1
                pass
        parid = dirid
    return dirid

def syncfolder(fulldirname, absimglist, subdirlist, isrecur, ispack):
    """Sync images in full dir name
    
    use list of full img filenames, list of subdirectories,
    include subdirectories Y/N,
    get rid of empty img recs. Y/N
    
    return accumulated counters: imgs added,
    img recs. deleted + no. of img recs. in db not found in dir
    """
    global sfcount
    imgcount = 0
    dirid = getdiridfull(fulldirname)
    # error condition:
    if dirid == 0:
        return (-1, -1)
    sfcount += 1
    print 'sf:', sfcount
    # sync curr folder (use absimglist)...
    emptycount = 0
    imglist = []
    newimglist = []
    for absimg in absimglist:
        filename = os.path.basename(absimg)
        if debug:
            print filename
        if isValidAsciiStr(filename):
            imglist.append(filename)
    firstid, emptyid = getfirstemptyids(dirid)
    for filename in imglist:
        imgid = getimgid(dirid, filename)
        # new img file found:
        if imgid == 0:
            imgid = addimage(dirid, filename, 0)
            if imgid > 0:
                imgcount += 1
                newimglist.append(filename)
                setnextid(imgid, firstid)
                firstid = imgid
                if (imgcount % pagesize) == 0:
                    print imgcount // pagesize
        elif isdelimage(imgid):
            emptyid = undelimage(imgid, emptyid)
            setnextid(imgid, firstid)
            firstid = imgid
            setisdel(imgid, False)
    for filename in newimglist:
        imglist.append(filename)
    rows = getimgrows(dirid)
    for row in rows:
        imgid = row[0]
        dirid = row[1]
        filename = row[2]
        nextid = row[3]
        isdel = row[4]
        if filename in imglist:
            continue
        # filename in db not found in dir
        setnextid(imgid, emptyid)
        emptyid = imgid
        setisdel(imgid, True)
        emptycount += 1
    if ispack:
        emptycount = 0
        rows = getimgrows(dirid)
        for row in rows:
            imgid = row[0]
            isdel = row[4]
            if isdel:
                delimage(imgid)
                emptycount += 1
        emptyid = -1
    setfirstemptyids(dirid, firstid, emptyid)
    if isrecur:
        for foldername in subdirlist:
            fullsubdir = os.path.join(fulldirname, foldername) + sepch
            absimglist = getimglist(fullsubdir)
            subdirlist = getsubdirlist(fullsubdir, False)
            icount, ecount = syncfolder(fullsubdir, absimglist, subdirlist, True, ispack)
            imgcount += icount
            emptycount += ecount
    return (imgcount, emptycount)
    
def pathtolist(path):
    """Return list of path parts, lowest to highest level
    
    assumes path is not absolute.
    """
    dirlist = []
    while path != '':
        head, tail = os.path.split(path)
        if tail != '':
            dirlist.append(tail)
        path = head
    return dirlist
    
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

def addimage(dirid, filename, nextid):
    """Add new img rec. & return its imgid."""
    db = get_db()
    db.execute('insert into images (dirid, filename, nextid, isurl, isvid, isdel) values (?, ?, ?, ?, ?, ?)',
        [dirid, filename, nextid, False, False, False])
    db.commit()
    return getimgid(dirid, filename)

def delimage(imgid):
    """Delete img rec."""
    db = get_db()
    db.execute('delete from images where imgid = %d' % imgid)
    db.commit()
    
def getimgid(dirid, filename):
    """Return imgid of img rec. having a given dirid/filename."""
    db = get_db()
    cur = db.execute('select imgid, dirid, filename from images ' + \
        ('where dirid = %d and filename = "' % dirid) + filename + '"')
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    imgid = row[0]
    return imgid

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

@app.route('/dgrid/')
@app.route('/dgrid/<adir>')
def dgrid(adir=None):
    """Handle grid of first images in each subdirectory."""
    if debug:
        print 'top of dgrid'
    global imgdir
    global pageidx
    global nameidx
    global dpageidx
    global dnameidx
    if adir == "-3":  # up arrow from sub-grid
        parentdir = imgdir[:-1]
        parent = os.path.basename(parentdir)
        if debug:
            print 'dgrid: parent =', parent
        if imgdir != imgroot:
            imgdir = os.path.dirname(parentdir) + sepch
        gendirinfo(imgdir)
    namelist = []
    for images in dirimglist:
        if len(images) > 0:
            namelist.append(images[0])
        else:
            namelist.append('')
    pagecount = (len(namelist) - 1) // pagesize
    pagecount += 1     ### pagecount = 0 ??
    if adir == "-2":  # right arrow
        dpageidx += 1
        dnameidx = 0
    elif adir == "-1":  # left arrow
        dpageidx += pagecount - 1
        dnameidx = 0
    # elif adir == "-3":  
    elif debug:
        print 'dgrid: dpageidx =', dpageidx
        print 'dgrid: pagecount =', pagecount
    dpageidx = getpgidxofcount(dpageidx, pagecount)
    dirname = dirlist[foldridx]
    fulldirname = staticdir + getpardirspath(imgdir)
    if debug:
        print 'dgrid: fulldirname =', fulldirname
    imgfilelist = ''
    j = 0
    for i in range(pagesize):
        k = (dpageidx * pagesize) + i
        if k >= len(namelist):
            break
        j = k + 1
        filename = namelist[k]
        dirname = dirlist[k]
        fullfilename = getffndirname(dirname, filename)
        fullfilename = fulldirname + fullfilename
        if debug:
            print fullfilename
        imgtag = '<img id=monoimg%d src="%s"></img>' % (j, fullfilename)
        imgtag = ('<a href="/grid/%d">' % k) + imgtag + '</a>'
        s = '<div id=monodiv%d>' % j
        imgtag = s + imgtag + '</div>' 
        imgfilelist += imgtag + cr
    if debug:
        print imgfilelist
    imgfilelist = Markup(imgfilelist)
    if debug:
        print 'btm of dgrid'
    return render_template('grid.html', imgfilelist=imgfilelist, \
        a=(dpageidx * pagesize), b=j, dgmode=DIRGRID)

@app.route('/grid/')
@app.route('/grid/<adir>')
def grid(adir=None):
    """Handle grid of images in current directory."""
    if debug:
        print 'top of grid'
    global imgdir
    global foldridx
    global dgmode
    global pageidx
    global nameidx
    global dpageidx
    global dnameidx
    # dgmode = 0
    namelist = dirimglist[foldridx]
    pagecount = (len(namelist) - 1) // pagesize
    pagecount += 1     ### pagecount = 0 ??
    if adir != None:
        idir = int(adir)
    else:
        idir = -1
    if adir == "-2":  # right arrow
        pageidx += 1
        nameidx = 0
    elif adir == "-1":  # left arrow
        pageidx += pagecount - 1
        nameidx = 0
    elif idir >= 0:
        dgmode = SUBGRID
        ## do something with idir...
        dirname = dirlist[idir]
        imgdir = os.path.join(imgdir, dirname) + sepch
        if debug:
            print 'grid: imgdir =', imgdir
        gendirinfo(imgdir)
        namelist = dirimglist[0]
        pagecount = (len(namelist) - 1) // pagesize
        pagecount += 1  
        foldridx = 0
        pageidx = 0
        nameidx = 0
    elif debug:
        print 'grid: pageidx =', pageidx
        print 'grid: pagecount =', pagecount
    pageidx = getpgidxofcount(pageidx, pagecount)
    dirname = dirlist[foldridx]
    fulldirname = staticdir + getpardirspath(imgdir)
    if debug:
        print 'grid: fulldirname =', fulldirname
    imgfilelist = ''
    j = 0
    for i in range(pagesize):
        k = (pageidx * pagesize) + i
        if k >= len(namelist):
            break
        j = k + 1
        filename = namelist[k]
        fullfilename = getffndirname(dirname, filename)
        fullfilename = fulldirname + fullfilename
        if debug:
            print fullfilename
        imgtag = '<img id=monoimg%d src="%s"></img>' % (j, fullfilename)
        imgtag = ('<a href="/mono/%d">' % k) + imgtag + '</a>'
        s = '<div id=monodiv%d>' % j
        imgtag = s + imgtag + '</div>' 
        imgfilelist += imgtag + cr
    if debug:
        print imgfilelist
    imgfilelist = Markup(imgfilelist)
    if debug:
        print 'btm of grid'
    return render_template('grid.html', imgfilelist=imgfilelist, \
        a=(pageidx * pagesize), b=j, dgmode=dgmode)

@app.route('/mono/')
@app.route('/mono/<adir>')
def mono(adir=None):
    """Handle mono template (single big image displayed)
    
    If user presses F, then display free template:
    - clickable freeones URL of facelooker star (link text is star's name)
    - Back link to grid template
    """
    if debug:
        print 'top of mono'
    global nameidx
    global pageidx
    namelist = dirimglist[foldridx]
    gofreeflag = False
    if adir != None:
        idir = int(adir)
    if adir == None:
        pass
    elif idir == -3:  # press F
        gofreeflag = True
    elif idir == -2:  # right arrow
        nameidx += 1
    elif idir == -1:  # left arrow
        nameidx += len(namelist) - 1
    elif idir >= 0:  # image in grid clicked on
        nameidx = idir
    nameidx = getpgidxofcount(nameidx, len(namelist))
    pageidx = nameidx // pagesize
    fulldirname = staticdir + getpardirspath(imgdir)
    dirname = dirlist[foldridx]
    filename = namelist[nameidx]
    fullfilename = getffndirname(dirname, filename)
    # print 'ffn #1', fullfilename
    # fullfilename = url_for('static', filename='pixroot/' + fullfilename)
    fullfilename = fulldirname + fullfilename
    if gofreeflag:
        filename = getfreename(fulldirname, dirname)
        url = getfreeurl(fulldirname, dirname)
        return render_template('free.html', url=url, filename=filename)
    if debug:
        print 'ffn #2', fullfilename
        print 'mono: pageidx =', pageidx
        print 'btm of mono'
    return render_template('mono.html', filename=fullfilename)

def getffndirname(dirname, filename):
    """Return path join of dir./filename (not full filenames)
    
    if dirname = $ (current dir.) just return filename
    """
    if dirname == dotchar:
        fullfilename = filename
    else:
        fullfilename = os.path.join(dirname, filename)
    return fullfilename

def getfreeurl(fulldirname, dirname):
    """Return URL of facelooker star's home page on freeones.com
    
    Upon success, ch is first ch. of first name
    Otherwise give up and don't try to access freeones (go to grid template)
    """
    filename = getfreename(fulldirname, dirname)
    badname = '/grid/'
    if filename == '':
        return badname
    ch = filename[0]
    if not ch.isalpha():
        return badname
    outbuf = 'http://www.freeones.com/html/%s_links/%s/' % (ch, filename)
    return outbuf

def getfreename(fulldirname, dirname):
    """Massage dir name to use for freeones facelooker star home page
    
    Sometimes dirname = $ (current dir.):
    then use fulldirname, otherwise just use dirname
    
    scan filename in reverse until non-Linux slash encountered
    keep scanning in reverse until another slash or invalid ch. encountered
    (invalid means non-alpha and non-hyphen/underscore ch.)
    take resulting substring
    strip initial slash (if any)
    strip initial underscores
    return resulting substring = facelooker star's name
    """
    if dirname == dotchar:
        filename = fulldirname
    else:
        filename = dirname
    outbuf = ''
    ch = sepch
    i = len(filename) - 1
    while filename[i] == ch:
        i -= 1
    ch = getfilenamechar(filename, i)
    while (i >= 0) and (ch != '') and (ch != sepch):
        outbuf = ch + outbuf
        i -= 1
        ch = getfilenamechar(filename, i)
    if ch == sepch:
        outbuf = outbuf[1:]
    i = 0
    n = len(outbuf)
    while (i < n) and (outbuf[i] == uscore):
        i += 1
    filename = outbuf[i:]
    return filename

def getfilenamechar(filename, i):
    """Massage filenames by scanning one char. at a time
    
    Assume ch = filename[i] 
    convert hyphen to underscore
    convert upper to lower case
    strip non-alphas (except hyphens/underscores)
    return null string if invalid ch.
    """
    if (i < 0) or (i >= len(filename)):
        return ''
    ch = filename[i]
    if (ch == uscore) or (ch == '-'):
        return uscore
    if not ch.isalpha():
        return ''
    ch = ch.lower()
    return ch

def isValidAsciiStr(filename):
    """Return false if filename contains non-printable char."""
    for i in range(len(filename)):
        s = filename[i]
        c = ord(s)
        if (c < 32) or (c >= 127):
            return False
    return True
    
def getpgidxofcount(pageidx, pagecount):
    """Return pageidx % pagecount
    
    if pagecount = 0, return zero
    """
    if pagecount == 0:
        return 0
    pageidx %= pagecount
    return pageidx

def initpgnamidx():
    global pageidx
    global nameidx
    global dpageidx
    global dnameidx
    pageidx = 0
    nameidx = 0
    dpageidx = 0
    dnameidx = 0
    
@app.route('/')
def hello_world():
    gendirinfo(imgdir)
    return 'Hello World!'

def getpardirspath(imgdir):
    """Return part of full dirname, post '/.../static/pixroot/'.
    
    note that string returned does not start with slash
    """
    n = len(imgroot)
    pardirspath = imgdir[n:]
    return pardirspath

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FACES_PORT)
