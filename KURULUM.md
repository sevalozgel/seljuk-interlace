# Selçuklu şerit deseni: Grasshopper kurulumu

## En kolay yol: hazır .gh dosyasını oluştur
1. Rhino'da komut satırına `EditPythonScript` yaz, Enter.
2. File > Open ile `seljuk_bands_gh_olustur.py` dosyasını aç, yeşil **Run** (F5).
3. Grasshopper açılır: bileşen, sliderlar, açma/kapama düğmeleri, kahve/mavi renkli önizleme
   ve CellInfo paneli bağlı gelir. Tanım Masaüstüne `seljuk_bands.gh` olarak kaydedilir.
   Sonraki seferlerde doğrudan bu .gh dosyasını açman yeterli.

Aşağıdaki adımlar elle kurmak istersen içindir.

Dosya: `seljuk_bands.py` (Rhino 7 GhPython ve Rhino 8 Script ile çalışır).

## 1. Bileşeni kur
1. Grasshopper'da **Maths > Script > GhPython Script** bileşenini koy (Rhino 8'de "Python 3 Script" de olur).
2. Çift tıkla, içindeki kodu sil, `seljuk_bands.py` dosyasının tamamını yapıştır, OK.
3. Bileşene yakınlaş, **+** ile girişleri ekle. Hepsi isteğe bağlı; eklemediğin giriş varsayılanı kullanır.
   İsimler birebir aynı olmalı (büyük/küçük harf dahil):

| Giriş | Tip ipucu | Varsayılan | Ne yapar |
|---|---|---|---|
| `Lines` | **List Access**, Type hint: **Curve** (önemli, yoksa GUID gelir) | boş | Kendi desen orta çizgilerin. Boşsa desen otomatik üretilir |
| `Pattern` | int | 8 | 8 = senin 8'li rozet modülün, 10 = 10'lu girih, 88 = sekizgen-kare yıldız |
| `Size` | float | 100 | 8'li modülde rozet yarıçapı (merkez → yaprak ucu) |
| `Cols`, `Rows` | int | 3, 2 | Modül sayısı (yatay, dikey) |
| `PetalW` | float | 0.25 | Yaprak yarım genişliği / Size |
| `Shoulder` | float | 0.91 | Yaprak omzu / Size (ucun sivriliği) |
| `Spacing` | float | 2.0 | Modül aralığı / Size. 2.0 = yaprak uçları değiyor (ekran görüntündeki gibi) |
| `Octagon` | bool | True | Dört rozet arasındaki boşlukta sekizgen. Çapraz yaprakların uç kenarları uçta çapraz geçip sekizgenin kenarları olur; boyutu PetalW/Shoulder'dan gelir |
| `OctR` | float | 0 | 0 = sekizgen yaprak uçlarından türetilir. >0 = bu yarıçapta (× Size) serbest düzgün sekizgen halka, yapraklarla örülür. 0.5 ve üstü temiz çalışır; 0.46 civarında sekizgen yaprak uçlarına paralel geçtiği için şeritler birbirini yutar |
| `Angle`, `Rosette` | | | Sadece 10 ve 88 desenleri için |
| `BandW` | float | 6 | Toplam şerit genişliği (kahve+mavi+kahve) |
| `BlueW` | float | 2 | Ortadaki mavi şerit |
| `BlueOffset` | float | 0 | Mavinin merkezden kayması (asimetrik şerit) |
| `Joint` | float | 0.5 | Derz: kahve-mavi arası ve şerit-hücre arası |
| `Gap` | float | 1.5 | Örgüde alttan geçen şeridin üstteki şeride boşluğu |
| `Interlace` | bool | True | Üst/alt örgü. False: parçalar kesişimde alın alına birleşir |
| `SplitCorners` | bool | False | Şeritleri köşelerde gönye derziyle ayrı karolara böler |
| `Plane` | Plane | WorldXY | Taban düzlemi |

4. Çıkışları da **+** ile ekle ve şu isimleri ver:
   `Brown`, `Blue`, `BrownCrv`, `BlueCrv`, `Cells`, `CellInfo`, `Strands`, `Tiles`

## 2. Çıkışlar
- **Brown / Blue**: kahverengi ve mavi yüzeyler, ayrı listeler. Her biri ayrı parça, üst üste binme yok.
- **BrownCrv / BlueCrv**: aynı parçaların kapalı sınır eğrileri (Extrude, lazer kesim vb. için).
- **Cells**: şeritlerin arasında kalan hücreler. Ağaç yapısında, her dal bir hücre tipi
  (büyük rozet, yıldız, altıgen ...). `CellInfo`'yu Panel'e bağla, hangi dalın ne olduğunu yazar.
  Tek tip seçmek için **Tree Branch** (veya List Item) kullan.
- **Strands**: şerit orta çizgileri. **Tiles**: desenin üretildiği taban karoları.

Renkli görmek için: Brown → **Custom Preview** (kahve), Blue → Custom Preview (turkuaz).
Rhino'ya ayrı katmanlara bake etmek için her çıkışı ayrı Bake et (ya da Elefront/Human ile katman ata).

## 3. Kendi çizgilerinle kullanmak
Şeritleri offset'lemeden önceki **orta çizgileri** (çizgi ağı) `Lines` girişine ver
(Explode etmene gerek yok, polyline de olur). Bileşen:
1. Bütün kesişimleri bulur ve ağı böler,
2. Her şeridi kesişimden düz devam ederek izler,
3. Kesişimlerde sırayla üst/alt atar (dama tahtası kuralı, her şerit boyunca alternatif),
4. Alttan geçen şeridi üstteki şeridin kenarına paralel keser (`Gap` kadar boşlukla),
5. Kahve-mavi-kahve şeritleri gönye köşeli ofsetlerle ayrı kapalı bölgeler olarak üretir,
6. Aradaki hücreleri ağın yüzlerinden bulup `BandW/2 + Joint` kadar içeri alır.

Yani ortada oluşan karışık bölgeyi Region Union/Difference ile ayırmaya çalışmana gerek kalmıyor;
her parça doğrudan ayrı kapalı bölge olarak çıkıyor.

## Sınırlar
- `BandW` desenin en kısa çizgi parçasına göre çok büyükse köşelerde kesimler birbirine girer;
  o zaman BandW'yi küçült ya da Size'ı büyüt.
- Fotoğraftaki pandantif eğrisel bir yüzey; bu bileşen düzlemsel deseni üretir. Eğri yüzeye taşımak için
  çıkışları **Map to Surface** / **Surface Morph** ile sarabilirsin.

## Fotoğraftaki şerit görünümü (hazır ayar)
Duvardaki karolara en yakın görünüm için (Size=100 iken):
`BandW=10, BlueW=3.6, BlueOffset=0.6, Joint=0.9, Interlace=False, SplitCorners=True`
- Interlace=False: kesişimde şeritler boşluksuz, alın alına birleşir (duvardaki gibi).
- SplitCorners=True: şeritler köşelerde gönye derziyle ayrı karo parçalarına bölünür.
- Joint: parçalar arasındaki derz (beyaz harç çizgisi).
