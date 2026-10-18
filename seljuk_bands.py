# -*- coding: utf-8 -*-
"""
Selcuklu geometrik desen -> kahverengi / mavi seritler + hucreler (parametrik)
GhPython (Rhino 7, IronPython 2.7) ve Rhino 8 Script (Python 3) ile calisir.

GIRISLER (hepsi istege bagli; eklemediginiz giris varsayilan degeri alir)
  Lines        : (List) Kendi desen ORTA cizgileriniz (Line/Polyline/Curve). Bos ise
                 desen asagidaki Pattern ile otomatik uretilir.
  Pattern      : 8  = 8'li rozet modulu (4 uzun altigen halka, ortada 8'li yildiz)
                 10 = 10'lu girih deseni, 88 = sekizgen-kare (4.8.8) yildiz deseni
  Size         : 8'li modulde rozet yaricapi (merkez -> yaprak ucu); digerlerinde karo kenari
  PetalW       : (8) Yaprak yarim genisligi / Size  (varsayilan 0.25)
  Shoulder     : (8) Yaprak omzu / Size; ucun sivriligi (varsayilan 0.91)
  Spacing      : (8) Moduller arasi mesafe / Size (2.0 = yaprak uclari degiyor)
  Octagon      : (8) True = dort rozet arasindaki boslukta sekizgen. Capraz yapraklarin uc
                 kenarlari ucta capraz gecip sekizgenin kenarlari olur (orguye katilir)
  OctR         : (8) 0 = sekizgen yaprak uclarindan turetilir; >0 = bu yaricapta (x Size)
                 serbest duzgun sekizgen halka, yapraklarla orulur
  Cols, Rows   : Tekrar sayisi
  Angle        : Yildiz acisi (derece). 10'lu icin 54, 8'li icin 67.5 klasik
  Rosette      : 10'lu desende ongen icindeki rozet: 1 = tek yildiz, 2 = rozet (varsayilan)
  BandW        : Toplam serit genisligi (kahve + mavi + kahve)
  BlueW        : Ortadaki mavi serit genisligi
  BlueOffset   : Mavi seridin merkezden kaymasi (+ sola, - saga)
  Joint        : Parcalar arasi derz (kahve-mavi, serit-hucre arasi)
  Gap          : Alttan gecen seridin ustten gecen seride olan bosluk mesafesi
  Interlace    : True = ust/alt orgu gecisleri (Gap kadar bosluk),
                 False = kesisimde parcalar bosluksuz alin alina birlesir
  SplitCorners : True = serit koselerde gonye (miter) derziyle parcalara ayrilir
  Plane        : Taban duzlemi

CIKISLAR
  Brown, Blue      : Kahverengi / mavi serit yuzeyleri (Brep listesi)
  BrownCrv, BlueCrv: Ayni parcalarin kapali sinir egrileri
  Cells            : Seritlerin arasindaki hucre yuzeyleri (Tree: her dal bir hucre tipi)
  CellInfo         : Dal numarasi -> kose sayisi / alan (hangi dal hangi sekil)
  Strands          : Serit orta cizgileri (ardisik polyline)
  Tiles            : Desenin uretildigi taban karolari
"""
import math

# ----------------------------------------------------------------------------
# kucuk 2B vektor yardimcilari (Rhino'dan bagimsiz, test edilebilir)
# ----------------------------------------------------------------------------
EPS = 1e-9


def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, s): return (a[0] * s, a[1] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]
def cross(a, b): return a[0] * b[1] - a[1] * b[0]
def length(a): return math.hypot(a[0], a[1])
def left(a): return (-a[1], a[0])


def unit(a):
    l = length(a)
    return (a[0] / l, a[1] / l) if l > EPS else (0.0, 0.0)


def line_x(p, d, q, e):
    """p + t d = q + u e  ->  (t, u) ya da paralelse None"""
    den = cross(d, e)
    if abs(den) < 1e-12:
        return None
    w = sub(q, p)
    return cross(w, e) / den, cross(w, d) / den


def seg_x(a, b, c, d, tol=1e-9):
    r = line_x(a, sub(b, a), c, sub(d, c))
    if r is None:
        return None
    t, u = r
    if -tol <= t <= 1 + tol and -tol <= u <= 1 + tol:
        return t, u
    return None


def area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        s += cross(poly[i], poly[(i + 1) % n])
    return 0.5 * s


def point_in_poly(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return inside


def key(p, q=1e-5):
    return (int(round(p[0] / q)), int(round(p[1] / q)))


# ----------------------------------------------------------------------------
# 1) TABAN KAROLARI
# ----------------------------------------------------------------------------
def reg_poly(c, n, R, a0):
    return [(c[0] + R * math.cos(a0 + 2 * math.pi * k / n),
             c[1] + R * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


def girih_tiles(s, cols, rows):
    """Periyodik girih karolama: ongen + uzun altigen + papyon (kenar = s)."""
    R = s / (2 * math.sin(math.pi / 10))
    r = s / (2 * math.tan(math.pi / 10))
    c36, s36 = R * math.cos(math.radians(36)), R * math.sin(math.radians(36))
    c72, s72 = R * math.cos(math.radians(72)), R * math.sin(math.radians(72))
    W = 2 * c72 + (2 * (c36 - c72) + s)  # uc-uca altigen boyu + iki yarim kenar
    H = 2 * r
    tiles = []
    for i in range(cols + 1):
        for j in range(rows + 1):
            ox, oy = i * W, j * H
            tiles.append(reg_poly((ox, oy), 10, R, 0.0))
            if i < cols:
                # papyon (bowtie) yatay komsu ongenler arasinda
                tiles.append([(ox + c36, oy - s36), (ox + W - c36, oy - s36), (ox + W - R, oy),
                              (ox + W - c36, oy + s36), (ox + c36, oy + s36), (ox + R, oy)])
                if j < rows:
                    tiles.append([(ox + c72, oy + s72), (ox + c36, oy + s36), (ox + W - c36, oy + s36),
                                  (ox + W - c72, oy + s72), (ox + W - c36, oy + H - s36), (ox + c36, oy + H - s36)])
    return tiles


def oct_tiles(s, cols, rows):
    """4.8.8 karolama: sekizgen + kare (8'li yildiz desenleri icin)."""
    R = s / (2 * math.sin(math.pi / 8))
    a = s * (1 + math.sqrt(2))
    h = s / math.sqrt(2)
    tiles = []
    for i in range(cols + 1):
        for j in range(rows + 1):
            c = (i * a, j * a)
            tiles.append(reg_poly(c, 8, R, math.pi / 8))
            if i < cols and j < rows:
                q = (c[0] + a / 2, c[1] + a / 2)
                tiles.append([(q[0] + h, q[1]), (q[0], q[1] + h), (q[0] - h, q[1]), (q[0], q[1] - h)])
    return tiles


def gap_octagon(g, centers, R, a, sh):
    """4 rozetin arasindaki boslukta sekizgen: bosluga bakan capraz yapraklarin uc
    kenarlari, ucta capraz gecip (X) duz devam ederek sekizgenin kenarlarini olusturur.
    Kose sirasi: yaprak ucu, iki komsu yapragin kenar uzantilarinin kesisimi, ..."""
    ang = lambda p: math.atan2(p[1] - g[1], p[0] - g[0])
    centers = sorted(centers, key=ang)
    tips, sides = [], []
    for c in centers:
        u = unit(sub(g, c))
        tip = add(c, mul(u, R))
        s1 = add(add(c, mul(u, sh)), mul(left(u), a))
        s2 = add(add(c, mul(u, sh)), mul(left(u), -a))
        tips.append(tip)
        sides.append((s1, s2))
    poly = []
    n = len(tips)
    for k in range(n):
        t0, t1 = tips[k], tips[(k + 1) % n]
        # kenarlar ucta capraz gecer: bir sonraki uca dogru uzanan, ondan UZAK olan kenardir
        sa = max(sides[k], key=lambda p: length(sub(p, t1)))
        sb = max(sides[(k + 1) % n], key=lambda p: length(sub(p, t0)))
        r = line_x(t0, sub(t0, sa), t1, sub(t1, sb))
        if r is None or r[0] <= 0 or r[1] <= 0:
            return None
        poly.append(t0)
        poly.append(add(t0, mul(sub(t0, sa), r[0])))
    return poly


def rosette8_segs(R, cols, rows, petal_w=0.25, shoulder=0.91, spacing=2.0, octagon=True, oct_r=0.0):
    """Kullanicinin 8'li modulu: 45 derece donuk 4 uzun altigen halka -> ortada
    8 koseli yildiz, cevrede 8 yaprak. Moduller kare izgarada, yaprak uclari degecek
    sekilde (spacing = 2R). Dort rozetin arasindaki bosluga sekizgen (gap_octagon)."""
    a, sh = petal_w * R, shoulder * R
    c = a * (math.sqrt(2) - 1)  # uzun kenarin capraz halka ile ilk kesisimi
    # her halkanin uzun kenarlarinin ortasi (yildizin icinde kalan kisim) cizilmez:
    # boylece merkezde iki karenin birlesimi olan 8 koseli yildiz olusur
    chains = [[(a, c), (a, sh), (0.0, R), (-a, sh), (-a, c)],
              [(-a, -c), (-a, -sh), (0.0, -R), (a, -sh), (a, -c)]]
    D = spacing * R
    segs, loops = [], []
    for i in range(cols):
        for j in range(rows):
            c = (i * D, j * D)
            o = (i * D, j * D)
            for k in range(4):
                t = k * math.pi / 4
                ct, st = math.cos(t), math.sin(t)
                for ch in chains:
                    pts = [(o[0] + x * ct - y * st, o[1] + x * st + y * ct) for x, y in ch]
                    loops.append(pts)
                    segs.extend(zip(pts[:-1], pts[1:]))
            if octagon and i < cols - 1 and j < rows - 1:
                g = (o[0] + D / 2, o[1] + D / 2)
                if oct_r:
                    # serbest duzgun sekizgen halka (koseler eksenlerde), yapraklarla orulur
                    oc = reg_poly(g, 8, oct_r * R, math.pi / 2)
                else:
                    oc = gap_octagon(g, [(o[0] + dx * D, o[1] + dy * D) for dx, dy in ((0, 0), (1, 0), (1, 1), (0, 1))],
                                     R, a, sh)
                if oc:
                    loops.append(oc + [oc[0]])
                    segs.extend(zip(oc, oc[1:] + oc[:1]))
    return segs, loops


# ----------------------------------------------------------------------------
# 2) HANKIN / "polygons in contact" yontemi: her karoda kenar ortalarindan
#    Angle acisiyla isinlar; isinlar en kisa yoldan eslestirilir.
# ----------------------------------------------------------------------------
def _seg_inside(p, q, poly):
    n = len(poly)
    for i in range(n):
        r = seg_x(p, q, poly[i], poly[(i + 1) % n], 0.0)
        if r and 1e-6 < r[0] < 1 - 1e-6 and 1e-6 < r[1] < 1 - 1e-6:
            return False
    return point_in_poly(mul(add(p, q), 0.5), poly)


def hankin(tiles, ang_deg, skip=1):
    th = math.radians(ang_deg)
    segs = []
    for poly in tiles:
        if area(poly) < 0:
            poly = poly[::-1]
        n = len(poly)
        F, B = [], []
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            m = mul(add(a, b), 0.5)
            e = unit(sub(b, a))
            nn = left(e)
            F.append((m, add(mul(e, math.cos(th)), mul(nn, math.sin(th)))))
            B.append((m, add(mul(e, -math.cos(th)), mul(nn, math.sin(th)))))
        cands = []
        if skip > 1 and n >= 8:
            # rozet: isin, komsu kenarin isinini KESIP 'skip' sonraki kenarin isiniyle bulusur
            for i in range(n):
                j = (i + skip) % n
                (p, d), (q, e) = F[i], B[j]
                r = line_x(p, d, q, e)
                if r and r[0] > 0 and r[1] > 0:
                    segs.append((p, add(p, mul(d, r[0]))))
                    segs.append((add(p, mul(d, r[0])), q))
                elif r is None and abs(cross(sub(q, p), d)) < 1e-9 * max(1.0, length(sub(q, p))):
                    segs.append((p, q))  # ayni dogru: kiris (girih ongeni, skip=3)
            continue
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                (p, d), (q, e) = F[i], B[j]
                r = line_x(p, d, q, e)
                if r is None:
                    # ayni dogru uzerinde karsi karsiya (72/90 derece koseler)
                    w = sub(q, p)
                    if abs(cross(w, d)) < 1e-9 * max(1.0, length(w)) and dot(w, d) > 0 and dot(e, d) < 0:
                        x = mul(add(p, q), 0.5)
                        L = length(w)
                        if _seg_inside(p, q, poly):
                            cands.append((L, i, j, x))
                    continue
                t, u = r
                if t <= 1e-9 or u <= 1e-9:
                    continue
                x = add(p, mul(d, t))
                if _seg_inside(p, x, poly) and _seg_inside(q, x, poly):
                    cands.append((t + u + 1e-6 * abs(t - u), i, j, x))
        cands.sort(key=lambda c: c[0])
        usedF, usedB = set(), set()
        for L, i, j, x in cands:
            if i in usedF or j in usedB:
                continue
            usedF.add(i)
            usedB.add(j)
            segs.append((F[i][0], x))
            segs.append((x, B[j][0]))
    return segs


# ----------------------------------------------------------------------------
# 3) CIZGI AGI -> duzlemsel graf (kesisimlerden bolunmus)
# ----------------------------------------------------------------------------
def planar_graph(segs, tol=1e-6):
    segs = [s for s in segs if length(sub(s[1], s[0])) > tol]
    cuts = [[0.0, 1.0] for _ in segs]
    # basit izgara hizlandirma
    cell = max(1e-6, sum(length(sub(b, a)) for a, b in segs) / max(1, len(segs)))
    grid = {}
    for idx, (a, b) in enumerate(segs):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for gx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
            for gy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                grid.setdefault((gx, gy), []).append(idx)
    done = set()
    for lst in grid.values():
        for ii in range(len(lst)):
            for jj in range(ii + 1, len(lst)):
                i, j = lst[ii], lst[jj]
                if (i, j) in done:
                    continue
                done.add((i, j))
                a, b = segs[i]
                c, d = segs[j]
                r = seg_x(a, b, c, d, 1e-9)
                if r:
                    cuts[i].append(r[0])
                    cuts[j].append(r[1])
    nodes, nid = [], {}

    def node(p):
        k = key(p, tol)
        if k not in nid:
            nid[k] = len(nodes)
            nodes.append(p)
        return nid[k]

    edges = set()
    for (a, b), ts in zip(segs, cuts):
        ts = sorted(set(round(t, 12) for t in ts))
        pts = [add(a, mul(sub(b, a), t)) for t in ts]
        for p, q in zip(pts[:-1], pts[1:]):
            u, v = node(p), node(q)
            if u != v:
                edges.add((min(u, v), max(u, v)))
    adj = [[] for _ in nodes]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return nodes, adj


# ----------------------------------------------------------------------------
# 4) SERITLER (strand): dugumde en duz devam eden kenari izle
# ----------------------------------------------------------------------------
def trace_strands(nodes, adj, straight_tol=0.2):
    def nxt(prev, cur):
        din = unit(sub(nodes[cur], nodes[prev]))
        cand = [w for w in adj[cur] if w != prev]
        if len(adj[cur]) == 2:
            return cand[0]
        best, bd = None, -2
        for w in cand:
            dd = dot(din, unit(sub(nodes[w], nodes[cur])))
            if dd > bd:
                best, bd = w, dd
        return best if bd > 1 - straight_tol else None

    used = set()
    strands = []
    order = sorted(range(len(nodes)), key=lambda i: (len(adj[i]) != 1, i))  # once uclar
    for s in order:
        for w in adj[s]:
            if (s, w) in used:
                continue
            path = [s, w]
            used.add((s, w)); used.add((w, s))
            closed = False
            while True:
                n2 = nxt(path[-2], path[-1])
                if n2 is None:
                    break
                if (path[-1], n2) in used:
                    break
                used.add((path[-1], n2)); used.add((n2, path[-1]))
                path.append(n2)
            if len(path) > 2 and path[-1] == path[0]:
                closed = True
                path.pop()
            if not closed and len(adj[s]) != 1:
                # geriye dogru da uzat
                back = [w, s]
                while True:
                    n2 = nxt(back[-2], back[-1])
                    if n2 is None or (back[-1], n2) in used:
                        break
                    used.add((back[-1], n2)); used.add((n2, back[-1]))
                    back.append(n2)
                path = back[::-1][:-2] + path
            strands.append((path, closed))
    return strands


# ----------------------------------------------------------------------------
# 5) ORGU (ust / alt) ataması
# ----------------------------------------------------------------------------
def halfedge_faces(nodes, adj):
    """Her yonlu kenarin (u,v) sol yuzu -> yuz indeksi; yuz dongulerini de dondurur."""
    order = {}
    for u in range(len(nodes)):
        order[u] = sorted(adj[u], key=lambda v: math.atan2(nodes[v][1] - nodes[u][1],
                                                          nodes[v][0] - nodes[u][0]))
    fid, cycles = {}, []
    for u in range(len(nodes)):
        for v in adj[u]:
            if (u, v) in fid:
                continue
            cyc = []
            a, b = u, v
            while (a, b) not in fid:
                fid[(a, b)] = len(cycles)
                cyc.append(a)
                lst = order[b]
                c = lst[(lst.index(a) - 1) % len(lst)]
                a, b = b, c
            cycles.append(cyc)
    return fid, cycles


def assign_over(nodes, adj, strands):
    """Yuzler dama tahtasi gibi 2 renge boyanir; kesisimde seridin sol-on yuzu
    0 renkliyse serit USTTEN gecer. Boylece her serit boyunca ust/alt sirayla degisir."""
    fid, cycles = halfedge_faces(nodes, adj)
    color = {}
    nbr = {}
    for (u, v), f in fid.items():
        nbr.setdefault(f, []).append(fid[(v, u)])
    for f0 in range(len(cycles)):
        if f0 in color:
            continue
        color[f0] = 0
        stack = [f0]
        while stack:
            f = stack.pop()
            for g in nbr.get(f, []):
                if g not in color:
                    color[g] = 1 - color[f]
                    stack.append(g)
    xing, state = {}, {}
    for si, (path, closed) in enumerate(strands):
        L = len(path)
        rng = range(L) if closed else range(1, L - 1)
        for k in rng:
            n = path[k]
            if len(adj[n]) < 4:
                continue
            w = path[(k + 1) % L]
            xing.setdefault(n, []).append((si, k))
            state[(si, k)] = (color[fid[(n, w)]] == 0)
    xing = dict((n, p) for n, p in xing.items() if len(p) == 2)
    return xing, state


# ----------------------------------------------------------------------------
# 6) SERIT PARCALARI ve OFSET SERITLER
# ----------------------------------------------------------------------------
def _offset_chain(pts, caps, d):
    """pts acik polyline, caps=(baslangic_dogru, bitis_dogru) (nokta, yon). d sola."""
    n = len(pts)
    dirs = [unit(sub(pts[i + 1], pts[i])) for i in range(n - 1)]
    lines = [(add(pts[i], mul(left(dirs[i]), d)), dirs[i]) for i in range(n - 1)]
    out = []
    (cp, cd) = caps[0]
    r = line_x(lines[0][0], lines[0][1], cp, cd)
    out.append(add(lines[0][0], mul(lines[0][1], r[0])) if r else lines[0][0])
    for i in range(1, n - 1):
        r = line_x(lines[i - 1][0], lines[i - 1][1], lines[i][0], lines[i][1])
        out.append(add(lines[i - 1][0], mul(lines[i - 1][1], r[0])) if r else lines[i][0])
    (cp, cd) = caps[1]
    r = line_x(lines[-1][0], lines[-1][1], cp, cd)
    out.append(add(lines[-1][0], mul(lines[-1][1], r[0])) if r else add(lines[-1][0], mul(lines[-1][1], length(sub(pts[-1], pts[-2])))))
    return out


def _offset_closed(pts, d):
    n = len(pts)
    dirs = [unit(sub(pts[(i + 1) % n], pts[i])) for i in range(n)]
    lines = [(add(pts[i], mul(left(dirs[i]), d)), dirs[i]) for i in range(n)]
    out = []
    for i in range(n):
        a, b = lines[i - 1], lines[i]
        r = line_x(a[0], a[1], b[0], b[1])
        out.append(add(a[0], mul(a[1], r[0])) if r else b[0])
    return out


def _clean(pts, closed, tol=1e-7):
    out = []
    for p in pts:
        if not out or length(sub(p, out[-1])) > tol:
            out.append(p)
    changed = True
    while changed and len(out) > 2:
        changed = False
        n = len(out)
        rng = range(n) if closed else range(1, n - 1)
        for i in rng:
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            if abs(cross(unit(sub(b, a)), unit(sub(c, b)))) < 1e-7 and dot(sub(b, a), sub(c, b)) > 0:
                del out[i]
                changed = True
                break
    return out


def _shift_cap(cap, d_along, amount):
    """cap dogrusunu parca icine dogru 'amount' kadar dik kaydir"""
    p, c = cap
    sn = abs(cross(d_along, c))
    if sn < 1e-6:
        return cap
    return (add(p, mul(d_along, amount / sn)), c)


def _cap(p, v, segdir):
    """kesim kapagi ustteki serite paralel; serit neredeyse paralelse dik kapak"""
    d = unit(segdir)
    if abs(cross(d, v)) < 0.35:
        return (p, left(d))
    return (p, v)


def band_pieces(nodes, strands, xing, state, P):
    """Her serit icin (polyline, bas_kapak, son_kapak) parcalari; ya da kapali halka."""
    W, gap, joint = P['BandW'], P['Gap'], P['Joint']
    if not P['Interlace']:
        gap = 0.0  # orgu yok: parcalar kesisimde alin alina birlesir, ust uste binmez
    pieces, rings = [], []
    for si, (path, closed) in enumerate(strands):
        pts = [nodes[k] for k in path]
        # kesim olaylari: (konum indeksi, tip, veri)
        events = []
        if True:
            for k, n in enumerate(path):
                if n in xing and state.get((si, k)) is False:
                    a, b = xing[n]
                    oth = b if a == (si, k) else a
                    op = strands[oth[0]][0]
                    u = unit(sub(nodes[op[(oth[1] + 1) % len(op)]], nodes[op[oth[1] - 1]]))
                    events.append((k, 'x', u))
        if P['SplitCorners']:
            rng = range(len(path)) if closed else range(1, len(path) - 1)
            for k in rng:
                a, b, c = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
                d0, d1 = unit(sub(b, a)), unit(sub(c, b))
                if abs(cross(d0, d1)) > 1e-6 and path[k] not in xing:
                    events.append((k, 'c', unit(add(left(d0), left(d1)))))
        if closed and not events:
            rings.append(_clean(pts, True))
            continue
        if closed:
            events.sort()
            k0 = events[0][0]
            pts = pts[k0:] + pts[:k0] + [pts[k0]]
            L = len(path)
            events = sorted(((k - k0) % L, t, v) for k, t, v in events)
            events.append((L, events[0][1], events[0][2]))
        else:
            events.sort()
        # parcala. Alttan gecis: ustteki seridin eksenine (X, v) dik uzakligi h olan
        # noktaya kadar serit polyline'i boyunca yurunur (kose atlasa bile dogru kesilir).
        def walk(k, step, X, v, h):
            nv = left(v)
            i = k
            while 0 <= i + step < len(pts):
                p, q = pts[i], pts[i + step]
                dp, dq = abs(dot(sub(p, X), nv)), abs(dot(sub(q, X), nv))
                if dq >= h:
                    t = (h - dp) / (dq - dp) if dq - dp > 1e-12 else 0.0
                    return i, add(p, mul(sub(q, p), t))
                i += step
            return None

        # kesim bolgesine dusen koseleri at (orada serit zaten yok)
        if P['SplitCorners']:
            zones = []
            for k, typ, v in events:
                if typ == 'x':
                    h = W / 2.0 + gap
                    wb = walk(k, -1, X=pts[k], v=v, h=h) if k > 0 else None
                    wf = walk(k, 1, X=pts[k], v=v, h=h) if k + 1 < len(pts) else None
                    zones.append((wb[0] if wb else 0, wf[0] if wf else len(pts)))
            events = [e for e in events if e[1] == 'x' or not any(z0 <= e[0] <= z1 for z0, z1 in zones)]

        cur_start = None  # (sonraki tepe indeksi, baslangic noktasi, kapak)
        if not closed:
            d0 = unit(sub(pts[1], pts[0]))
            cur_start = (1, pts[0], (pts[0], left(d0)))
        for k, typ, v in events:
            X = pts[k]
            dprev = unit(sub(X, pts[k - 1])) if k > 0 else unit(sub(pts[1], pts[0]))
            dnext = unit(sub(pts[k + 1], X)) if k + 1 < len(pts) else dprev
            if typ == 'x':
                h = W / 2.0 + gap
                wb = walk(k, -1, X, v, h) if k > 0 else None
                wf = walk(k, 1, X, v, h) if k + 1 < len(pts) else None
                end = (wb[0] - 1, wb[1], _cap(wb[1], v, sub(pts[wb[0]], pts[wb[0] - 1]))) if wb else None
                beg = (wf[0] + 1, wf[1], _cap(wf[1], v, sub(pts[wf[0] + 1], pts[wf[0]]))) if wf else None
            else:
                end = (k - 1, X, _shift_cap((X, v), mul(dprev, -1), joint / 2.0))
                beg = (k + 1, X, _shift_cap((X, v), dnext, joint / 2.0))
            if cur_start is not None and end is not None:
                i0, p0, cap0 = cur_start
                seg = [p0] + pts[i0:end[0] + 1] + [end[1]]
                if len(seg) >= 2 and end[0] + 1 >= i0:
                    d = sub(pts[i0], pts[i0 - 1]) if 0 < i0 < len(pts) else sub(seg[-1], seg[0])
                    if len(seg) > 2 or dot(sub(seg[1], seg[0]), d) > 1e-9:
                        pieces.append((seg, cap0, end[2]))
            cur_start = beg
        if not closed and cur_start is not None:
            i0, p0, cap0 = cur_start
            seg = [p0] + pts[i0:]
            dl = unit(sub(pts[-1], pts[-2]))
            if len(seg) >= 2:
                pieces.append((seg, cap0, (pts[-1], left(dl))))
    return pieces, rings


def _simple(poly):
    """kendini kesen (cok kisa kalmis) parcalari ele"""
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            r = seg_x(a, b, poly[j], poly[(j + 1) % n], -1e-9)
            if r:
                return False
    return True


def strip_polys(pieces, rings, P):
    W, b, o, j = P['BandW'], P['BlueW'], P['BlueOffset'], P['Joint']
    bands = {
        'brown': [(o + b / 2.0 + j / 2.0, W / 2.0), (-W / 2.0, o - b / 2.0 - j / 2.0)],
        'blue': [(o - b / 2.0 + j / 2.0, o + b / 2.0 - j / 2.0)],
    }
    out = {'brown': [], 'blue': []}
    for col, lst in bands.items():
        for d1, d2 in lst:
            if d2 - d1 <= 1e-9:
                continue
            for seg, c0, c1 in pieces:
                seg2 = _clean(seg, False)
                if len(seg2) < 2:
                    continue
                A = _offset_chain(seg2, (c0, c1), d1)
                Bp = _offset_chain(seg2, (c0, c1), d2)
                poly = A + Bp[::-1]
                if abs(area(poly)) > 1e-9 and _simple(poly):
                    out[col].append([poly])
            for ring in rings:
                A = _offset_closed(ring, d1)
                Bp = _offset_closed(ring, d2)
                out[col].append([A, Bp])
    return out


# ----------------------------------------------------------------------------
# 7) HUCRELER: graf yuzleri, serit yarim genisligi + derz kadar iceri
# ----------------------------------------------------------------------------
def faces(nodes, adj):
    fid, cycles = halfedge_faces(nodes, adj)
    polys = []
    for cyc in cycles:
        p = [nodes[k] for k in cyc]
        if area(p) > 1e-9 and len(set(cyc)) == len(cyc):
            polys.append(p)
    return polys


def inset(poly, d):
    p = _clean(poly, True)
    if len(p) < 3:
        return None
    q = _offset_closed(p, d)
    # gecerlilik: ayni yon, kenarlar ters donmemis
    n = len(p)
    for i in range(n):
        e0 = sub(p[(i + 1) % n], p[i])
        e1 = sub(q[(i + 1) % n], q[i])
        if dot(e0, e1) <= 0:
            return None
    if area(q) <= 1e-9:
        return None
    return q


def cells(nodes, adj, P):
    d = P['BandW'] / 2.0 + P['Joint']
    groups = {}
    for f in faces(nodes, adj):
        c = _clean(f, True)
        q = inset(f, d)
        if q is None:
            continue
        k = (len(c), round(area(c), 3))
        groups.setdefault(k, []).append(q)
    keys = sorted(groups, key=lambda k: -k[1])
    return [(k, groups[k]) for k in keys]


# ----------------------------------------------------------------------------
# ANA FONKSIYON
# ----------------------------------------------------------------------------
DEFAULTS = dict(Pattern=8, Size=100.0, Cols=3, Rows=2, Angle=None, BandW=6.0, BlueW=2.0,
                BlueOffset=0.0, Joint=0.5, Gap=1.5, Interlace=True, SplitCorners=False,
                Rosette=None, PetalW=0.25, Shoulder=0.91, Spacing=2.0, Octagon=True, OctR=0.0)


def build(P, segs=None, tol=None):
    P = dict(DEFAULTS, **dict((k, v) for k, v in P.items() if v is not None))
    tiles = []
    if not segs:
        if int(P['Pattern']) == 8:
            segs, tiles = rosette8_segs(P['Size'], int(P['Cols']), int(P['Rows']), P['PetalW'],
                                        P['Shoulder'], P['Spacing'], P['Octagon'], P['OctR'])
        elif int(P['Pattern']) == 88:
            tiles = oct_tiles(P['Size'], int(P['Cols']), int(P['Rows']))
            ang = P['Angle'] if P['Angle'] is not None else 67.5
        else:
            tiles = girih_tiles(P['Size'], int(P['Cols']), int(P['Rows']))
            ang = P['Angle'] if P['Angle'] is not None else 54.0
        if int(P['Pattern']) != 8:
            ros = P['Rosette'] if P['Rosette'] is not None else (2 if int(P['Pattern']) == 10 else 1)
            segs = hankin(tiles, ang, int(ros))
    tol = max(tol or 0.0, 1e-6 * max(1.0, max(max(abs(c) for c in p) for s in segs for p in s)))
    nodes, adj = planar_graph(segs, tol)
    strands = trace_strands(nodes, adj)
    xing, state = assign_over(nodes, adj, strands)
    pieces, rings = band_pieces(nodes, strands, xing, state, P)
    strips = strip_polys(pieces, rings, P)
    cl = cells(nodes, adj, P)
    strand_pts = [([nodes[k] for k in path], closed) for path, closed in strands]
    return dict(tiles=tiles, strands=strand_pts, brown=strips['brown'], blue=strips['blue'],
                cells=cl, nodes=nodes, adj=adj, xing=xing)


# ----------------------------------------------------------------------------
# GRASSHOPPER KISMI
# ----------------------------------------------------------------------------
def _gh_main():
    import Rhino
    import Rhino.Geometry as rg
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path

    g = globals()
    P = {}
    for k in DEFAULTS:
        P[k] = g.get(k, None)
    for k in ('Cols', 'Rows', 'Pattern'):
        if P[k] is not None:
            P[k] = int(P[k])
    pl = g.get('Plane', None) or rg.Plane.WorldXY
    try:
        tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
    except Exception:
        tol = 0.001

    # kullanici cizgileri -> plan duzleminde 2B parcalar
    segs = []
    src = g.get('Lines', None)
    if src:
        if not isinstance(src, (list, tuple)):
            src = [src]
        for c in src:
            if c is None:
                continue
            if not isinstance(c, (rg.GeometryBase, rg.Line, rg.Polyline)):
                # tip ipucu verilmemisse (ghdoc Object) egri GUID olarak gelir
                import rhinoscriptsyntax as rs
                c = rs.coercecurve(c)
                if c is None:
                    continue
            if isinstance(c, rg.Line):
                c = rg.LineCurve(c)
            elif isinstance(c, rg.Polyline):
                c = rg.PolylineCurve(c)
            ok, poly = c.TryGetPolyline()
            if not ok:
                poly = c.ToPolyline(tol, math.radians(2), 0, 0).ToPolyline()
            ptsl = []
            for p in poly:
                okp, u, v = pl.ClosestParameter(p)
                ptsl.append((u, v))
            for a, b in zip(ptsl[:-1], ptsl[1:]):
                segs.append((a, b))

    R = build(P, segs, tol * 0.5 if segs else None)

    def P3(p):
        return pl.PointAt(p[0], p[1])

    def crv(poly):
        pts = [P3(p) for p in poly] + [P3(poly[0])]
        return rg.PolylineCurve(pts)

    def breps(lst):
        bs, cs = [], []
        for loops in lst:
            cc = [crv(l) for l in loops]
            cs.extend(cc)
            b = rg.Brep.CreatePlanarBreps(cc, tol)
            if b:
                bs.extend(b)
        return bs, cs

    br, brc = breps(R['brown'])
    bl, blc = breps(R['blue'])
    tree = DataTree[object]()
    info = []
    for i, (k, polys) in enumerate(R['cells']):
        for poly in polys:
            b = rg.Brep.CreatePlanarBreps([crv(poly)], tol)
            if b:
                tree.Add(b[0], GH_Path(i))
        info.append("{%d}: %d kose, alan %.3f, adet %d" % (i, k[0], k[1], len(polys)))
    strands = []
    for pts, closed in R['strands']:
        q = [P3(p) for p in pts]
        if closed:
            q.append(q[0])
        strands.append(rg.PolylineCurve(q))
    tiles = [crv(t) for t in R['tiles']]

    # tani: kahverengi bos kalirsa nedenini CellInfo panelinin basina yaz
    Q = dict(DEFAULTS, **dict((k, v) for k, v in P.items() if v is not None))
    W, b, o, j = Q['BandW'], Q['BlueW'], Q['BlueOffset'], Q['Joint']
    msg = ["BandW=%.3f BlueW=%.3f BlueOffset=%.3f Joint=%.3f" % (W, b, o, j),
           "kahverengi: %d serit, %d yuzey | mavi: %d serit, %d yuzey"
           % (len(R['brown']), len(br), len(R['blue']), len(bl))]
    sag = W / 2.0 - (o + b / 2.0 + j / 2.0)
    sol = (o - b / 2.0 - j / 2.0) + W / 2.0
    if sag <= 0 and sol <= 0:
        msg.append("UYARI: BlueW + Joint, BandW'den buyuk/esit; kahverengiye yer "
                   "kalmiyor. BandW'yi buyutun veya BlueW/Joint'i kucultun "
                   "(or. BandW 6, BlueW 2, Joint 0.5).")
    elif len(R['brown']) and not br:
        msg.append("UYARI: kahverengi egriler var ama yuzey olusmadi; BrownCrv "
                   "cikisina bakin, tolerans/olcek sorunu olabilir.")
    for m in msg:
        print(m)
    info = msg + info
    return br, bl, brc, blc, tree, info, strands, tiles


try:
    import Rhino  # noqa
    _IN_RHINO = True
except ImportError:
    _IN_RHINO = False

if _IN_RHINO and __name__ != 'seljuk_bands':
    Brown, Blue, BrownCrv, BlueCrv, Cells, CellInfo, Strands, Tiles = _gh_main()
