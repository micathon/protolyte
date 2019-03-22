import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Markup
from contextlib import closing
import glob
import os
import random

cr = '%c' % 10
dotchar = '$'
uscore = '_'
progresschar = '*'
ishello = False
PICRO_PORT = 6996
bytroidx = 0
picroidx = 0
savproidx = 0
nameidx = 0
pageidx = 0
pagesize = 18  # const
onameidx = 0
outerpgidx = 0
shuffleidx = 0
debug = False
sepch = os.sep
picrokey = 'PICRO_PATH'
rootfolder = 'pixroot'
seedlist = []
bytrolist = []
currimglist = []
currcorelist = []
bytroimglist = []
picrolist = []
propgidxlist = []
corepgidxlist = []
iscoremode = False
isouter = False

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# inz path constants
picropath = os.getenv(picrokey, '')
staticdir = os.path.join('static', rootfolder)
staticdir = sepch + staticdir + sepch
imgroot = picropath + staticdir
imgdir = imgroot
locport = 'localhost:%d' % PICRO_PORT

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'picro.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('PICRO_SETTINGS', silent=True)

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
    print('About to Initialize the database.')
    init_db()
    print('Initialized the database.')
    
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
    
def gendircount(imd):
    """Load a fresh database, after using initdb command"""
    count = 0
    badcount = 0
    bytrocount = 0
    isAddPicroFail = False
    isAddImgFail = False
    isCoreFound = False
    allvalid = True
    imgdir = imd
    absdirlist = glob.glob(imgdir + sepch + '*')
    absdirlist = sorted(absdirlist)
    for absdir in absdirlist:
        print('')
        print('>', absdir)
        dirname = os.path.basename(absdir)
        if not os.path.isdir(absdir):
            print('Bytro Failure (unexpected file name) occurred!')
            continue
        if bytrocount > 1:  # debug use: only 2 bytros
            #break
            pass
        bytid = addbytro(dirname)
        if bytid > 0:
            bytrocount += 1
        else:
            print('Add Bytro Failure occurred!')
            continue
        subdirlist = glob.glob(absdir + sepch + '*')
        subdirlist = sorted(subdirlist)
        for subdir in subdirlist:
            print('')
            print('>>', subdir)
            subdirname = os.path.basename(subdir)
            if not os.path.isdir(subdir):
                print('Picro Failure (unexpected file name) occurred!')
                continue
            proid = addpicro(bytid, subdirname)
            if proid <= 0:
                isAddPicroFail = True
                print('Add Picro Failure occurred!')
                continue
            for j in range(2):
                imglist = []
                absimglist = getimglist(subdir)
                # for each image file in subdirectory
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
                    imgid = addimg(proid, filename, iscore)
                    if imgid <= 0:
                        isAddImgFail = True
                        print('Add Img Failure occurred!')
                        continue
                    outdot(i + 1, filename)  # display dot: feedback to user
                corename = subdir + sepch + dotchar
                if not os.path.isdir(corename):
                    break
                isCoreFound = True
                subdir = corename
                if j < 1:
                    print('')
                    print('>>', subdir)
        print('bottom of outer loop')
    print('')
    if not allvalid:
        print('%d invalid image file name(s) found!' % badcount)
    if isAddPicroFail:
        print('Final: Add Picro Failure occurred!')
    if isAddImgFail:
        print('Final: Add Img Failure occurred!')
    if not isCoreFound:
        print('No core subfolders found!')
    print ('%d bytros added' % bytrocount)
    return count
    
@app.route('/load/')
def loadroot():
    """Cannot access from menu, enter: localhost:6996/load"""
    count = 0
    print('Top of load')
    print('Are you sure?')
    print('> ', end='')
    inbuf = input()
    if (inbuf == 'Y' or inbuf == 'y'):
        count = gendircount(imgdir)
    print('%d image file count' % count)
    return render_template('load.html')

def outdot(seqno, filename):
    """Displays 100 dots per line, I/O is buffered so dots printed all at once"""
    if (seqno % 5) != 0:
        return
    seqno //= 5
    if (seqno % 20) > 0:
        print('.', end='')
    else:
        print('.')
    return

@app.route('/bytro/')
@app.route('/bytro/<adir>')
def bytro(adir=None):
    """Handle folder template: unordered list of bytros, contains 1 list of picros."""
    global bytroidx
    global picroidx
    global bytroimglist
    global picrolist
    global currimglist
    global currcorelist
    global isemptycorelist
    global propgidxlist
    global corepgidxlist
    global outerpgidx
    global savproidx
    global shuffleidx
    if debug:
        print('top of bytro')
    isshowgrid = False
    iszeroout = False
    shuffleidx = 0
    cmdstr = ''
    bytrono = bytroidx
    picrono = picroidx
    if adir != None:
        idir = int(adir)
    else:
        idir = 0
    if idir >= 0:
        bytrono = idir
        picrono = 0
    elif idir == -1:  # right arrow: next picro
        bytrono = bytroidx
        picrono = picroidx + 1
    elif idir == -2:  # left arrow: previous picro
        bytrono = bytroidx
        picrono = picroidx - 1
    elif idir == -4:
        # goto next bytro:
        isshowgrid = True
        bytrono = bytroidx + 1
        picrono = 0
        idir = 0
    elif idir == -10:
        # Reshuffle
        seedlistreinz()
        cmdstr = 'reshuffle'
        idir = 0
    elif idir == -11:
        # Zero out indices
        iszeroout = True
        cmdstr = 'zero-out'
        idir = 0
    elif idir == -12:
        # Sync bytro
        bytroname = bytrolist[bytroidx]
        count = syncbytrocur(bytroname)
        print('sync bytro: %d image file count' % count)
        idir = 0
    elif idir == -13:
        # Sync all bytros
        count = syncallbytros()
        print('sync all bytros: %d image file count' % count)
        bytrono = 0
        idir = 0
    else:  # idir == -3
        pass
    bytrocount = len(bytrolist)
    bytroidx = getpgidxofcount(bytrono, bytrocount)
    iscoremode = False
    if idir >= 0:
        currimglist = []
        currcorelist = []
        isemptycorelist = []
        bytroimglist = []
        propgidxlist = []
        corepgidxlist = []
    isdup = False
    udirlist = '<ul>'
    for i in range(bytrocount):
        bytroname = bytrolist[i]
        iscurrbytro = (i == bytroidx)
        innertag = ''
        if iscurrbytro:
            innertag = cr + '<ul>'
            rndseed = seedlist[i]
            random.seed(rndseed)
            if debug:
                print('bytro: i, seed =', i, rndseed)
            bytid = getbytroid(bytroname)
            picrolist = getpicrolist(bytid)
            picrocount = len(picrolist)
            picroidx = (picrono + picrocount) % picrocount
            for j in range(picrocount):
                picroname = picrolist[j]
                if idir >= 0:  # change bytroidx
                    initpgnamidx()
                    proid = getproid(bytid, picroname)
                    appendcurrlists(proid, iszeroout)
                    propgidxlist.append(0)
                    corepgidxlist.append(0)
                    imglist = currimglist[j]
                    imgcorelist = currcorelist[j]
                    # handle last grid having 18 images (cannot tell when at last grid)
                    # duplicate very last image so it appears on last grid by itself
                    isdup = isdup or picduponfull(imglist) or picduponfull(imgcorelist)
                    savproidx = j
                    imgidlist = getimgidlist(proid)
                    for imgid in imgidlist:
                        bytroimglist.append(imgid)
                iscurrpicro = (j == picroidx)
                if iscurrpicro:
                    picroname = '<a href="/igrid/">' + picroname + '</a>'
                    picroname = '[ ' + picroname + ' ]'
                m = len(currimglist[j])
                n = len(currcorelist[j])
                if isemptycorelist[j]:
                    countpair = ' - (%d)' % m
                else:
                    countpair = ' - (%d, %d)' % (m, n)
                picrotag = '<li>' + picroname + countpair + '</li>'
                innertag += cr + picrotag
            innertag += cr + '</ul>' + cr
            if idir >= 0 and not iszeroout:
                picshuffle(bytroimglist)
                isdup = isdup or picduponfull(bytroimglist)
        else:
            bytroname = ('<a href="/bytro/%d">' % i) + bytroname + '</a>'
        bytrotag = '<li>' + bytroname + innertag + '</li>'
        udirlist += cr + bytrotag
    udirlist += cr + '</ul>'
    udirlist = Markup(udirlist)
    if debug:
        print('bytroidx =', bytroidx)
        print('picrocount =', picrocount)
        print('picroidx =', picroidx)
        print('isdup =', isdup)
        if len(cmdstr) > 0:
            print('cmd =', cmdstr)
        print('btm of bytro')
    if isshowgrid:
        print('redirect: ogrid')
        return redirect(url_for('ogrid'))
    return render_template('bytro.html', udirlist=udirlist)

def proid2idx(proid):
    """Convert picroid (proid) to picroidx (idx to picrolist)"""
    picroname = getpicroname(proid)
    bytroname = bytrolist[bytroidx]
    bytid = getbytroid(bytroname)
    picrolist = getpicrolist(bytid)
    for i in range(len(picrolist)):
        name = picrolist[i]
        if name == picroname:
            return i
    return -1

def appendcurrlists(proid, iszeroout):
    global currimglist
    global currcorelist
    global isemptycorelist
    imgtuple = getimglistpair(proid)  ## , False)
    imglist = imgtuple[0]
    imgcorelist = imgtuple[1]
    isemptycore = imgtuple[2]
    if not iszeroout:
        picshuffle(imglist)
        picshuffle(imgcorelist)
    currimglist.append(imglist)
    currcorelist.append(imgcorelist)
    isemptycorelist.append(isemptycore)

def syncallbytros():
    """Sync internal database of all bytros w/ file system"""
    global bytrolist
    count = 0
    isAddBytroFail = False
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
            bytroidx = bytrolist.index(bytroname)
            bytrolist[bytroidx] = ''
        else:
            bytid = addbytro(bytroname)
        if bytid <= 0:
            isAddBytroFail = True
            print('Add/Get Bytro Failure occurred!')
            continue
        count += syncbytrocur(bytroname)
        print('bottom of bytro 1st outer loop')
    delcount = 0
    for bytroname in bytrolist:
        if len(bytroname) == 0:
            continue
        bytid = getbytroid(bytroname)
        proidlist = getallproidlist(bytid)
        for proid in proidlist:
            imgidlist = getallimgidlist(proid)
            for imgid in imgidlist:
                delimg(imgid)
            delpicro(proid)
        delbytro(bytid)
        delcount += 1
        print('bottom of bytro 2nd outer loop')
    print('bytro(s) deleted count = ', delcount)
    bytrolist = []
    absdirlist = glob.glob(imgdir + '*')
    absdirlist = sorted(absdirlist)
    for absdir in absdirlist:  # for all bytro folders
        bytroname = os.path.basename(absdir)
        if os.path.isdir(absdir):
            bytrolist.append(bytroname)
    bytrolist = sorted(bytrolist)
    print('bytro count = ', len(bytrolist))
    if isAddBytroFail:
        print('Final: Add/Get Bytro Failure occurred!')
    return count

def syncbytrocur(bytroname):
    """Sync internal database of current bytro w/ file system"""
    global currimglist
    global currcorelist
    global isemptycorelist
    bytid = getbytroid(bytroname)
    picrolist = getpicrolist(bytid)
    picrocount = len(picrolist)
    print('Sync bytro: bytro name =', bytroname)
    print('Sync bytro: picro count =', picrocount)
    currimglist = []
    currcorelist = []
    isemptycorelist = []
    for picroname in picrolist:
        proid = getproid(bytid, picroname)
        appendcurrlists(proid, True)
    count = 0
    badcount = 0
    isAddPicroFail = False
    isAddImgFail = False
    isGetImgFail = False
    allvalid = True
    imd = imgdir + bytroname
    absdirlist = glob.glob(imd + sepch + '*')
    absdirlist = sorted(absdirlist)
    for absdir in absdirlist:  # for all picro folders
        print('')
        print('>', absdir)
        picroname = os.path.basename(absdir)
        if not os.path.isdir(absdir):
            print('Picro Failure (unexpected file name) occurred!')
            continue
        if picroname in picrolist:
            proid = getproid(bytid, picroname)
            picroidx = picrolist.index(picroname)
            imgreclist = currimglist[picroidx]
            imgcorelist = currcorelist[picroidx]
            isemptycore = isemptycorelist[picroidx]
            if isemptycore:
                imgcorelist = []
            picrolist[picroidx] = ''
        else:
            proid = addpicro(bytid, picroname)
            picroidx = -1
            imgreclist = []
            imgcorelist = []
            isemptycore = True
        if proid <= 0:
            isAddPicroFail = True
            print('Add/Get Picro Failure occurred!')
            continue
        newreclist = []
        newcorelist = []
        subdir = absdir
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
            listsiz = len(imglist)
            count += listsiz
            print('%d images in folder' % listsiz)
            for i in range(len(imglist)):
                filename = imglist[i]
                iscore = (j > 0)
                if not iscore:
                    if filename in imgreclist:
                        imgreclist.remove(filename)
                    else:
                        newreclist.append(filename)
                elif isemptycore:
                    newcorelist.append(filename)
                elif filename in imgcorelist:
                    imgcorelist.remove(filename)
                else:
                    newcorelist.append(filename)
                outdot(i + 1, filename)
            corename = subdir + sepch + dotchar
            if not os.path.isdir(corename):
                break
            subdir = corename
            if j < 1:
                print('')
                print('>>', subdir)
            print('')
        addcount = 0
        for filename in newreclist:
            imgid = addimg(proid, filename, False)
            if imgid <= 0:
                isAddImgFail = True
                print('Add Img Failure occurred!')
                continue
            addcount += 1
        addcorecount = 0
        for filename in newcorelist:
            imgid = addimg(proid, filename, True)
            if imgid <= 0:
                isAddImgFail = True
                print('Add Core Img Failure occurred!')
                continue
            addcorecount += 1
        for filename in imgreclist:
            imgid = getimgidcore(proid, filename, False)
            if imgid <= 0:
                isGetImgFail = True
                print('Get Img (core = N) Failure occurred!')
                continue
            delimg(imgid)
        for filename in imgcorelist:
            imgid = getimgidcore(proid, filename, True)
            if imgid <= 0:
                isGetImgFail = True
                print('Get Img (core = Y) Failure occurred!')
                continue
            delimg(imgid)
        delcount = len(imgreclist)
        delcorecount = len(imgcorelist)
        print('')
        print('add counts = (%d, %d)' % (addcount, addcorecount))
        print('del counts = (%d, %d)' % (delcount, delcorecount))
        print('bottom of 1st outer loop')
    print('')
    delcount = 0
    for filename in picrolist:
        if len(filename) == 0:
            continue
        proid = getproid(bytid, filename)
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
    if isGetImgFail:
        print('Final: Get Img Failure occurred!')
    return count

@app.route('/igrid/')
@app.route('/igrid/<adir>')
def igrid(adir=None):
    global iscoremode
    global isproidchange
    iscoremode = False
    isproidchange = False
    return redirect(url_for('grid'))

@app.route('/cgrid/')
@app.route('/cgrid/<adir>')
def cgrid(adir=None):
    global iscoremode
    global isproidchange
    iscoremode = True
    isproidchange = (adir == "-3")
    return redirect(url_for('grid'))

@app.route('/grid/')
@app.route('/grid/<adir>')
def grid(adir=None):
    """Handle grid of images in current directory."""
    if debug:
        print('top of grid')
    global isouter
    global propgidxlist
    global corepgidxlist
    global nameidx
    global picroidx
    if isproidchange:
        picroidx = savproidx  # pass it down from omono, if changed
        print('savproidx =', savproidx)
        isdownarrow = True
    else:
        print('savproidx: ignored')
        isdownarrow = False
    foldridx = picroidx
    if iscoremode:
        namelist = currcorelist[foldridx]
        pageidx = corepgidxlist[foldridx]
    else:
        namelist = currimglist[foldridx]
        pageidx = propgidxlist[foldridx]
    pagecount = (len(namelist) - 1) // pagesize
    pagecount += 1     ### pagecount = 0 ??
    nameidx = 0
    isouter = False
    if adir != None:
        idir = int(adir)
    else:
        idir = -1
    if adir == None:
        pass
    elif adir == "-2":  # right arrow
        pageidx += 1
    elif adir == "-1":  # left arrow
        pageidx += pagecount - 1
    elif adir == "-3":  # down arrow
        pass
    #elif idir >= 0:  ### idir always -ve
    if debug:
        print('grid: pageidx =', pageidx)
        print('grid: pagecount =', pagecount)
    pageidx = getpgidxofcount(pageidx, pagecount)
    if iscoremode:
        corepgidxlist[foldridx] = pageidx
    else:
        propgidxlist[foldridx] = pageidx
    dirname = getpicrodir(foldridx, iscoremode)
    bytroname = bytrolist[bytroidx]
    fulldirname = staticdir + bytroname + sepch
    if debug:
        print('grid: fulldirname =', fulldirname)
    imgfilelist = ''
    j = 0
    for i in range(pagesize):
        k = (pageidx * pagesize) + i
        if k >= len(namelist):
            break
        j = k + 1
        filename = namelist[k]
        fullfilename = os.path.join(dirname, filename)
        fullfilename = fulldirname + fullfilename
        if debug:
            print(fullfilename)
            if not os.path.exists(picropath + fullfilename):
                print('Err: no such file!')
        imgtag = '<img id="monoimg%d" src="%s">' % (j, fullfilename)
        imgtag = ('<a href="/imono/%d">' % k) + imgtag + '</a>'
        s = '<div id="monodiv%d">' % j
        imgtag = s + imgtag + '</div>' 
        imgfilelist += imgtag + cr
    if debug:
        print('imgfilelist =', imgfilelist)
    imgfilelist = Markup(imgfilelist)
    if debug:
        print('btm of grid')
    rtfilename = 'grid.html'
    if iscoremode:
        rtfilename = 'c' + rtfilename
    else:
        rtfilename = 'i' + rtfilename
    return render_template(rtfilename, imgfilelist=imgfilelist, \
        a=(pageidx * pagesize), b=j)

def getpicrodir(picroidx, iscoremode):
    dirname = picrolist[picroidx]
    if iscoremode and not isemptycorelist[picroidx]:
        dirname += sepch + dotchar
    return dirname

@app.route('/ogrid/')
@app.route('/ogrid/<adir>')
def ogrid(adir=None):
    """Handle grid outer of images."""
    if debug:
        print('top of ogrid')
    global isouter
    global outerpgidx
    global nameidx
    pagecount = (len(bytroimglist) - 1) // pagesize
    pagecount += 1     ### pagecount = 0 ??
    nameidx = 0
    isouter = True
    if adir != None:
        idir = int(adir)
    else:
        idir = -1
    if adir == "-2":  # right arrow
        outerpgidx += 1
    elif adir == "-1":  # left arrow
        outerpgidx += pagecount - 1
    elif adir == "-3":  # down arrow
        print('savproidx =', savproidx)
    else:  # idir = -1
        print('ogrid: outerpgidx =', outerpgidx)
        print('ogrid: pagecount =', pagecount)
        print('ogrid: bytroidx =', bytroidx)
    outerpgidx = getpgidxofcount(outerpgidx, pagecount)
    bytroname = bytrolist[bytroidx]
    imgfilelist = ''
    j = 0
    for i in range(pagesize):
        k = (outerpgidx * pagesize) + i
        if k >= len(bytroimglist):
            break
        j = k + 1
        imgid = bytroimglist[k]
        imgtup = getimgname(imgid)
        proid = imgtup[0]
        filename = imgtup[1]
        dirname = getpicroname(proid)
        if filename == '' or dirname == '':
            print('ogrid: filename =', filename)
            print('ogrid: dirname =', dirname)
            print('ogrid: i =', i)
            continue
        fulldirname = staticdir + bytroname + sepch
        fullfilename = os.path.join(dirname, filename)
        fullfilename = fulldirname + fullfilename
        if debug:
            print(fullfilename)
        imgtag = '<img id="monoimg%d" src="%s">' % (j, fullfilename)
        imgtag = ('<a href="/omono/%d">' % k) + imgtag + '</a>'
        s = '<div id="monodiv%d">' % j
        imgtag = s + imgtag + '</div>' 
        imgfilelist += imgtag + cr
    if debug:
        pass
        #print('imgfilelist =', imgfilelist)
    imgfilelist = Markup(imgfilelist)
    if debug:
        print('btm of ogrid')
    rtfilename = 'ogrid.html'
    return render_template(rtfilename, imgfilelist=imgfilelist, \
        a=(outerpgidx * pagesize), b=j)

@app.route('/imono/')
@app.route('/imono/<adir>')
def imono(adir=None):
    """Handle mono template (single big image displayed)
    """
    if debug:
        print('top of mono')
    global isouter
    global propgidxlist
    global corepgidxlist
    global nameidx
    isouter = False
    foldridx = picroidx
    if iscoremode:
        namelist = currcorelist[foldridx]
    else:
        namelist = currimglist[foldridx]
    if adir != None:
        idir = int(adir)
    if adir == None:
        pass
    elif idir == -2:  # right arrow
        nameidx += 1
    elif idir == -1:  # left arrow
        nameidx += len(namelist) - 1
    elif idir >= 0:  # image in grid clicked on
        nameidx = idir
    nameidx = getpgidxofcount(nameidx, len(namelist))
    pageidx = nameidx // pagesize
    if iscoremode:
        corepgidxlist[foldridx] = pageidx
    else:
        propgidxlist[foldridx] = pageidx
    dirname = getpicrodir(foldridx, iscoremode)
    bytroname = bytrolist[bytroidx]
    fulldirname = staticdir + bytroname + sepch
    filename = namelist[nameidx]
    fullfilename = os.path.join(dirname, filename)
    fullfilename = fulldirname + fullfilename
    if debug:
        print('ffn', fullfilename)
        print('mono: pageidx =', pageidx)
        print('btm of mono')
    rtfilename = 'mono.html'
    if isouter:
        rtfilename = 'o' + rtfilename
    else:
        rtfilename = 'i' + rtfilename
    return render_template(rtfilename, filename=fullfilename)

@app.route('/omono/')
@app.route('/omono/<adir>')
def omono(adir=None):
    """Handle mono template (single big image displayed)
    """
    if debug:
        print('top of omono')
    global isouter
    global onameidx
    global outerpgidx
    global savproidx
    isouter = True
    namelist = bytroimglist
    idir = 0
    if adir != None:  # always the case
        idir = int(adir)
    if adir == None:
        pass
    elif idir == -2:  # right arrow
        onameidx += 1
    elif idir == -1:  # left arrow
        onameidx += len(namelist) - 1
    elif idir >= 0:  # image in grid clicked on
        onameidx = idir
    onameidx = getpgidxofcount(onameidx, len(namelist))
    outerpgidx = onameidx // pagesize
    imgid = bytroimglist[onameidx]
    imgtup = getimgname(imgid)
    proid = imgtup[0]
    filename = imgtup[1]
    dirname = getpicroname(proid)
    bytroname = bytrolist[bytroidx]
    fulldirname = staticdir + bytroname + sepch
    fullfilename = os.path.join(dirname, filename)
    fullfilename = fulldirname + fullfilename
    savproidx = proid2idx(proid)  # needs to be passed down to igrid
    if debug:
        print('ffn', fullfilename)
        print('omono: outerpgidx =', outerpgidx)
        print('savproidx =', savproidx)
        print('btm of omono')
    if savproidx < 0:  # proid2idx fails
        savproidx = 0
    rtfilename = 'omono.html'
    return render_template(rtfilename, filename=fullfilename)

def addbytro(bytroname):
    """Add new dir rec. & return its dirid
    """
    if len(bytroname) == 0:
        return 0
    db = get_db()
    db.execute('insert into bytrotab (bytroname) values (?)',
        [bytroname])
    db.commit()
    return getbytroid(bytroname)
    
def delbytro(bytid):
    """Del bytro rec"""
    db = get_db()
    db.execute('delete from bytrotab ' + \
        'where id = %d' % bytid)
    db.commit()

def getbytroid(bytroname):
    """Return id of bytrotab rec. having a given bytroname."""
    db = get_db()
    cur = db.execute('select id, bytroname from bytrotab ' + \
        'where bytroname = "' + bytroname + '"')
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    bytid = row[0]
    return bytid

def addpicro(bytid, picroname):
    """Add new picro rec. & return its proid
    """
    db = get_db()
    db.execute('insert into picrotab (bytid, picroname) values (?, ?)',
        [bytid, picroname])
    db.commit()
    return getproid(bytid, picroname)
    
def delpicro(proid):
    """Del picro rec"""
    db = get_db()
    db.execute('delete from picrotab ' + \
        'where id = %d' % proid)
    db.commit()

def getproid(bytid, picroname):
    """Return id of picrotab rec. having a given bytid & picroname."""
    db = get_db()
    cur = db.execute('select id, bytid, picroname from picrotab ' + \
        ('where bytid = %d and picroname = "' % bytid) + picroname + '"')
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    proid = row[0]
    return proid

def getpicroname(proid):
    """Return picroname of picrotab rec. having a given id."""
    db = get_db()
    cur = db.execute('select id, picroname from picrotab ' + \
        'where id = %d' % proid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return ''
    row = rows[0]
    picroname = row[1]
    return picroname

def addimg(proid, filename, iscore):
    """Add new img rec. & return its imgid."""
    db = get_db()
    db.execute('insert into imgtab (proid, filename, iscore) values (?, ?, ?)',
        [proid, filename, iscore])
    db.commit()
    return getimgid(proid, filename)

def delimg(imgid):
    """Del img rec"""
    db = get_db()
    db.execute('delete from imgtab ' + \
        'where id = %d' % imgid)
    db.commit()

def getimgid(proid, filename):
    """Return id of imgtab rec. having a given proid/filename."""
    db = get_db()
    cur = db.execute('select id, proid, filename from imgtab ' + \
        ('where proid = %d and filename = "' % proid) + filename + '"')
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    imgid = row[0]
    return imgid

def getimgidcore(proid, filename, iscore):
    """Return id of imgtab rec. having a given proid/filename/iscore."""
    if iscore:
        isflagbit = 1
    else:
        isflagbit = 0
    db = get_db()
    cur = db.execute('select id, proid, filename, iscore from imgtab ' + \
        ('where proid = %d and filename = "' % proid) + filename + '" ' + \
        'and iscore = %d' % isflagbit)
    rows = cur.fetchall()
    if len(rows) < 1:
        return 0
    row = rows[0]
    imgid = row[0]
    return imgid

def getimgname(imgid):
    """Return (proid, filename) of imgtab rec. having a given id."""
    db = get_db()
    cur = db.execute('select id, proid, filename from imgtab ' + \
        'where id = %d' % imgid)
    rows = cur.fetchall()
    if len(rows) < 1:
        return (0, '')
    row = rows[0]
    proid = row[1]
    filename = row[2]
    return (proid, filename)

def getbytrolist():
    """Return sorted list of bytrotab records = bytroname."""
    bytrolist = []
    db = get_db()
    cur = db.execute('select id, bytroname from bytrotab')
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        bytid = row[0]
        bytroname = row[1]
        bytrolist.append(bytroname)
    bytrolist = sorted(bytrolist)
    return bytrolist

def getpicrolist(bytid):
    """Return list of picro recs. all having same bytid."""
    picrolist = []
    db = get_db()
    cur = db.execute('select id, picroname from picrotab ' + \
        'where bytid = %d' % bytid)
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        proid = row[0]
        picroname = row[1]
        picrolist.append(picroname)
    picrolist = sorted(picrolist)
    return picrolist

def getimglistpair(proid):  ## , issync):
    """Return 2 lists of img recs. (iscore=F/T) all having same proid.
    issync parameter is unused
    """
    imglist = []
    imgcorelist = []
    filename = ''
    db = get_db()
    cur = db.execute('select id, filename, iscore from imgtab ' + \
        'where proid = %d' % proid)
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        imgid = row[0]
        filename = row[1]
        iscore = row[2]
        if iscore:
            imgcorelist.append(filename)
        else:
            imglist.append(filename)
    #if issync:
        #return (imglist, imgcorelist)
    if len(imgcorelist) == 0 and filename != '':
        imgcorelist.append(filename)
        isemptycore = True
    else:
        isemptycore = False
    return (imglist, imgcorelist, isemptycore)
    
def getimgidlist(proid):
    """Return list of imgid values"""
    imgidlist = []
    db = get_db()
    cur = db.execute('select id, iscore from imgtab ' + \
        'where proid = %d' % proid)
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        imgid = row[0]
        iscore = row[1]
        if not iscore:
            imgidlist.append(imgid)
    return imgidlist

def getallimgidlist(proid):
    """Return list of imgid values, ignore iscore value"""
    imgidlist = []
    db = get_db()
    cur = db.execute('select id from imgtab ' + \
        'where proid = %d' % proid)
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        imgid = row[0]
        imgidlist.append(imgid)
    return imgidlist

def getallproidlist(bytid):
    """Return list of proid values"""
    proidlist = []
    db = get_db()
    cur = db.execute('select id from picrotab ' + \
        'where bytid = %d' % bytid)
    rows = cur.fetchall()
    for i in range(len(rows)):
        row = rows[i]
        proid = row[0]
        proidlist.append(proid)
    return proidlist

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
    
def picduponfull(picrolist):
    """If last grid in picrolist has size 18, duplicate last image,
    lets user know when at end of grid list
    """
    n = len(picrolist)
    if n == 0 or (n % pagesize) > 0:
        return False
    picro = picrolist[n - 1]
    picrolist.append(picro)
    return True
    
def picshuffle(picrolist):
    """randomly shuffle images in picro, extra debug info"""
    global shuffleidx
    if not debug:
        return picshufflertn(picrolist)
    shuffleidx += 1
    count = 0
    n = len(picrolist)
    print('picshuffle, len =', shuffleidx, n)
    for i in range(3):
        if i < n:
            print(picrolist[i])
    for i in range(3):
        j = n - i - 1
        if j >= 0:
            print(picrolist[j])
    for i in range(n - 1):
        j = n - i
        k = n - random.randrange(j) - 1
        temp = picrolist[i]
        picrolist[i] = picrolist[k]
        picrolist[k] = temp
        if abs(i - k) > (j // 2):
            count += 1
    print('picshuffle: end')
    return count
    
def picshufflertn(picrolist):
    """randomly shuffle images in picro"""
    count = 0
    n = len(picrolist)
    for i in range(n - 1):
        j = n - i
        k = n - random.randrange(j) - 1
        #print('ijkn = ', i, j, k, n)
        temp = picrolist[i]
        picrolist[i] = picrolist[k]
        picrolist[k] = temp
        if abs(i - k) > (j // 2):
            count += 1
    return count
    
def seedlistreinz():
    global seedlist
    random.seed()
    for i in range(len(seedlist)):
        seed = seedlist[i]
        while True:
            newseed = random.randrange(1000000)
            if newseed != seed:
                break
        seedlist[i] = newseed
    
def initseedlist():
    global seedlist
    global bytrolist
    random.seed()
    seedlist = []
    bytrolist = getbytrolist()
    for bytroname in bytrolist:
        seed = random.randrange(1000000)
        seedlist.append(seed)
    return len(seedlist)

def initpgnamidx():
    global pageidx
    global nameidx
    global onameidx
    global outerpgidx
    global savproidx
    global griddir
    global monodir
    griddir = None
    monodir = None
    pageidx = 0
    nameidx = 0
    onameidx = 0
    outerpgidx = 0
    savproidx = 0
    
@app.route('/hello/')
def hello_world():
    global ishello
    ishello = not ishello
    print('Top of hello_world')
    if ishello:
        return 'Hello World!'
    return 'Goodbye ishello!'

@app.route('/')
def init_foldr():
    initpgnamidx()
    seedcount = initseedlist()
    print('%d bytros exist' % seedcount)
    return redirect(url_for('bytro'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PICRO_PORT)
