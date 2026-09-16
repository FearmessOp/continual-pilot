# Hat 2 — Onaylı önkayıt, revizyon 1

Durum: KULLANICI TARAFINDAN ONAYLANDI; içerik kilitlendi. Çalıştırma izni değildir.
Onay tarihi: 2026-09-16. SHA-256 ve Git kayıtları ayrı tarihli kilit özetinde tutulur.
Dosya adı taslak geçmişinden korunmuştur; geçerli durum bu başlıktadır.
Tarih: 2026-09-16.
Etiket: Keşiften türetilmiş, yeni veride önkayıtlı doğrulama.
Bu tur yalnızca belge üretir; eğitim, kabul, güç pilotu veya ana deney yoktur.

## 1. Amaç ve mevcut kanıtın sınırı

Amaç: yönlendirme ve yenilemenin birlikte, yalnızca güncelleme sıklığını
azaltarak elde edilen öğrenme–koruma ödünleşmesinden daha iyi sonuç
verip vermediğini sınamak. Düşük unutma tek başına başarı değildir.

v0.3 için seçilen keşif düzeni 40.000/10.000/1.024/4.000 örnektir.
Faz 3 bütçesi 64 adet 16-örnekli güncelleme fırsatı; faz 4 geçiş penceresi
480 örnek, 30 fırsattır. Fırsat sayısı ile gerçekleşen güncelleme ayrı sayılır.
v0.3 öğrenilebilirlik kapısı geçilmemiştir; bu veriyle onaylayıcı koşu başlatılamaz.
v0.4 filtrelenmiş dağılımında süre seçimi yeniden doğrulanmadan taşınamaz.

Çevrimiçi blok ortalaması hızlı değişimde blok sonu donmuş doğruluğu
temsil etmez. Eski ilk-blok %71,1 ile kısa pilotun son-durum %58,660–61,530
değerleri bu ayrımın önemini gösterir; farklı hazırlık süreleri ve tohumlar
nedeniyle farkın tamamı blok ortalamasına nedensel olarak yüklenmez.
Süre ve hasar kararı yalnızca bağımsız donmuş ölçümle alınır.

## 2. Veri erişimi ve ortak öğrenci

Faz sırası M1/R1 → M2/R1 → M2/R2 → M2/R1.
Temel öğrenci 32→64→4, ReLU; Adam, sabit öğrenme oranı 0,001.
Minibatch 16 yeni örnek. Adam katsayıları 0,9/0,999, epsilon 10^-8,
ağırlık cezası yok. Temiz etiketler ve gerçek faz/kural kimlikleri
öğrenilmiş yöntemlerin tahminine veya güncellemesine verilmez.
Her tahmin güncel gürültülü etiketten önce üretilir.

Bağlam: yalnızca son 64 gözlenmiş gürültülü etiketli çiftin dört sınıf
sıklığı ve dört sınıf-koşullu 32-boyut ortalaması; toplam 132 boyut.
Pencere faz sınırında sıfırlanmaz. Güncel gözlem uzmanların girdisidir.
Değerlendirici temiz R1/R2 hedeflerine erişebilir; eğitim kodundan ayrı tutulur.

## 3. Koşullar

| Koşul | Yönlendirme | Yenileme | Açıklama |
|---|---|---|---|
| A | Yok | Yok | Tek temel öğrenci |
| B | Var | Yok | İki uzman ve nedensel yönlendirici |
| C | Yok | Var | A + CPR-tarzı uyarlama |
| D | Var | Var | B + aynı CPR-tarzı uyarlama |
| Replay | Yok | Yok | Reservoir 512; her yeni örneğe en fazla 8 geçmiş örnek |
| Donmuş-F2 | Yok | Yok | A'nın faz-2 kopyası; faz 3–4'te güncelleme yok |
| Seyrek-A-50 | Yok | Yok | Faz 3–4'te her ikinci grupta güncelleme |
| Seyrek-A-25 | Yok | Yok | Faz 3–4'te her dördüncü grupta güncelleme |
| Seyrek-A-75 | Yok | Yok | Her dördüncü grup atlanır; yalnızca kalibrasyon tanısı, zarf noktası değil |
| Yakın k-NN | Yok | Yok | Son 256 gürültülü etiketli örnek |
| A+bağlam | Yok | Yok | 164→64→4; aynı 132 özete erişim tanısı |
| Rejim-bilen replay tanısı | Yok | Yok | Replay ile aynı öğrenci; değerlendiricide ek köken kaydı |

A/B/C/D birincil 2×2 ailesidir. Diğer koşullar ana faktörlere dahil edilmez.
Donmuş-F2 ve seyrek-A aynı A faz-2 model ve optimizer durumundan dallanır.
B/D uzman 0 başlangıcı A/C başlangıcıyla eşleştirilir; uzman 1 ayrı fakat
B/D arasında aynı başlangıcı alır. C/D CPR rastgeleliği eşleştirilir.
B/D daha fazla kapasiteye sahiptir: sonuç saf, kapasiteden bağımsız
yönlendirme etkisi olarak sunulmaz. A+bağlam da parametre sayısını değiştirir.

## 4. Yönlendirici — onaylı mekanik

İki uzman, her biri 32→64→4; kapasite büyütme veya uzman ekleme yok.
Yönlendirici 132→2 doğrusal skor üretir; başlangıç ağırlıkları ve bias sıfırdır.
Yönlendirici Adam öğrenme oranı 0,001; uzmanlarla aynı diğer Adam ayarları.
Girdilerde ileri veriyle normalizasyon yok; standart bağlam tanımı aynen kullanılır.

Her 16'lık grubun başında önceki geçmişin özetiyle bir uzman seçilir;
seçim grup boyunca sabittir. Eşitlikte küçük uzman indeksi alınır.
Her sekizinci global grupta keşif uygulanır: bu gruplarda uzman indeksi
0,1,0,1 biçiminde dönüşür. Global grup sayacı faz sınırını bilmez.
Keşif grupları faz 1'den itibaren işler; sonuca göre kapatılmaz.

Her örnekte iki uzmanın güncelleme öncesi skorları hesaplanır;
gerçek tahmini yalnızca seçilmiş uzman verir. Etiket geldikten sonra
iki uzmanın gürültülü çapraz entropileri değerlendirici olmayan eğitim
mantığında hesaplanır. Grup sonunda her uzmanın ortalama kaybı bulunur.
En düşük kayıplı uzman yönlendiricinin grup hedefidir; eşitlikte küçük indeks.
Yönlendirici grup başında saklanan özete bu hedefle bir adım uygular.
Yalnızca seçilmiş uzman aynı 16 gürültülü örnekle bir Adam adımı yapar.
Diğer uzman için optimizer adımı ve ağırlık cezası uygulanmaz.
Uzman kayıpları uzman güncellemesinden önce hesaplanır.
Aday algoritmanın kendiliğinden uzmanlaşacağı varsayılmaz; çökme,
uzman açlığı ve 64 fırsatta uyumsuzluk raporlanacak olası başarısızlıklardır.

### Doğru uzman eşleme kuralı

Gerçek kural kimliği yönlendirici hedefi değildir.
Birincil yönlendirme tanısı: güncelleme öncesi gürültülü grup kaybı en düşük
uzmana göre seçim isabeti; beraberlikte küçük indeks. Bu tanı
temiz kuralı öğrenmeyi kanıtlamaz.
Ayrı temiz uzman-kural eşlemesi yalnızca değerlendiricide yapılır:
faz-3 sonunda iki uzman, ana değerlendirmeden ayrı 20.000 M2 kalibrasyon
girdisinde R1/R2'ye karşı ölçülür. İki olası birebir eşlemeden toplam temiz
doğruluğu yüksek olan seçilir; beraberlikte uzman0→R1 alınır.
Eşleme bundan sonra sabit tutulur; faz-4 testinde yeniden optimize edilmez.
Bu post-eğitim tanısal eşleme eğitim yönlendirmesine geri beslenmez.
İdeal yönlendirme aynı donmuş uzmanlardan seçer; yeni uzman eğitmez.
Her iki uzman her iki kuralda kötü ise eşleme bunu gizlemez: dört doğruluk
ve en iyi-uzman hatası da yayımlanır.

### Uzmanlaşma ile arşiv benzeri korumayı ayıran tanılar

Durağan fazlarda yönlendiricinin sıfır kalacağı varsayılmaz: uzman kayıpları
farklıysa öğrenme hedefleri de farklı olabilir. Uzman 1'in yalnızca keşifle
güncelleneceği de bir sonuç değil, sınanacak olasılıktır.
Faz 3'teki 64 fırsatta 8 zorunlu keşif grubu, dönüşümlü kural gereği
her uzmana 4 zorunlu güncelleme verir; açgözlü seçim ek güncellemeler verebilir.

Her uzman için faz2 ve faz3 sonu R1/R2 temiz doğruluklarının tamamı,
faz4 ilk 480 örnek sonrası ve faz4 sonu doğrulukları, yerel güncelleme
sayıları, zorunlu keşif/açgözlü kullanım ayrımı raporlanır.
Özellikle uzman 1'in faz2 R1 doğruluğu atlanmaz.
Aynı uzmanların faz2 donmuş kopyaları da tanısal referans olarak korunur;
yeni eğitim yapılmaz ve bunlar ana seyrek-A referans noktalarını değiştirmez.

Önceden belirlenen yorum dalları:
- Uzmanlaşma ile tutarlı: bir uzmanda R2 öğrenimi artarken diğerinde R1
  korunur ve sistem seçimleri uygun uzmanı kullanır. R2 kazanımı ve R1
  kaybı her uzman için ayrı sayıyla verilir; yalnızca kullanım oranı yetmez.
- Arşiv benzeri korumayla tutarlı: faz4'te avantaj sağlayan uzman faz3'te
  az güncellenmiş, R2 kazanımı sınırlı ve R1 performansı kendi faz2
  kopyasına yakın kalmıştır. Bu, öğrenim/korumayı ayıran uzmanlaşmadan
  farklı, yönlendirilmiş bir arşiv açıklamasıdır.
- Karışık/belirsiz: tablolar bu açıklamaları ayırmıyorsa ikisinden biri
  kesin mekanizma ilan edilmez. R2 kazanımının sıfırdan ayırt edilememesi,
  hiç öğrenme olmadığının veya tam donmanın kanıtı değildir.

Bu dallar betimsel tanılardır; yeni bir başarı testi veya ana koşul eleme
kuralı değildir. B/D üstünlüğü otomatik olarak “gerçek uzmanlaşma” diye
adlandırılmaz.

## 5. CPR kaynağı ve deney uyarlaması

Kaynak: Luc McCutcheon, Evangelos Chatzaroulas, Saber Fallah,
Calibrated Partial Resets: Preventing Policy Collapse in Continual
Reinforcement Learning, arXiv:2607.24996v1, Bölüm 3, Denklemler 3/5/6/7 ve Ek A.
Kaynak: https://arxiv.org/html/2607.24996v1
Bu taslak makalenin RL deneyinin birebir yeniden üretimi değildir.

Kaynakta: giriş ağırlıklarının örnek başına gradyan normu ortalamasıyla
nöron faydası; katman ortalamasına göre normalizasyon; EMA;
faydaya göre dereceli katsayı; periyodik kısmi sıfırlama;
giriş ağırlıklarını başlangıç dağılımına doğru taşıma, çıkışları küçültme,
ardından EMA'yı 1'e sıfırlama yer alır.
EMA katsayısı, sıklık, norm seçimi, bias ve Adam momenti kararları
aşağıda deneye özgü tercihlerdir; kaynaktan alınmış varsayılmaz.

Yalnızca uzman/temel ağın 64 gizli nöronuna uygulanır; yönlendiriciye uygulanmaz.
Her uzman güncellemesinde, güncelleme öncesi gürültülü kayıp üzerinden:
S_i = minibatch içindeki giriş-ağırlığı gradyanlarının L2 normlarının ortalaması.
Ortalama gradyanın normu kullanılmaz. S_i katman ortalaması + 10^-8'e bölünür.
u_i başlangıçta 1; u_i ← 0,99 u_i + 0,01 normalize(S_i).
Her 8 yerel uzman güncellemesinin ardından Adam adımından sonra:
r_i = 0,01 × min(2 sigmoid[-4(u_i−1)], 1).
Giriş ağırlığı satırı ← (1−r_i) satır + r_i ξ_i.
ξ_i her müdahalede bağımsız, temel katmanın başlangıç uniform dağılımından çekilir.
Çıkış ağırlığı sütunu ← (1−r_i) sütun.
Biaslar ve Adam momentleri bu uyarlamada korunur; ayrıca sıfırlanmaz.
Ardından o katmanın u değerleri 1'e döner.
Tam reset, sabit ilk-ağırlığa çekme veya uniform weight decay kullanılmaz.

D'de yalnızca güncellenen uzmanın yerel saati/EMA'sı ilerler;
etkin olmayan uzman çekilmez. C'de tek ağın yerel saati işler.
Bu nedenle 64 global fırsat D'de uzman başına 64 adım demek değildir.
CPR ve yönlendirme faz 1–2 boyunca da aynı kurallarla çalışır.
Faz-3 başlangıcında müdahale durumu sıfırlanmaz. 3.125 hazırlık fırsatı
ve uzman başına gerçek ısınma sayısı ayrı raporlanır.
Kontroller başarısızsa bu değerler ana sonuçlara bakılarak değiştirilmez;
yeni protokol sürümü gerekir.

### Müdahale bütçesi ve yenileme etkinliği

C, 64 yerel güncellemede 8 müdahale yapar. Yalnızca CPR çarpanları
açısından eski bileşenin katsayısı en az 0,99^8 = 0,922745'tir;
en büyük çarpımsal azaltma yaklaşık %7,7255'tir.
D'de uzman j için müdahale sayısı, faz başındaki yerel sayaç k ve faz
içindeki güncelleme sayısı n kullanılarak
floor((k+n)/8) − floor(k/8) olarak hesaplanır; sıfırdan başlamış varsayılmaz.
Uzman başına azaltma sınırı 1−0,99^m ile ayrıca raporlanır.

Bu sınır, toplam ağırlık yer değiştirme normunun %7,73'ten küçük olduğu
anlamına gelmez. Rastgele ξ ve aradaki Adam adımları farklı etkiler üretir.
Sıfır I tek başına ne “etkileşim yok” ne de “yenileme ölçülemez” kanıtıdır.

Her CPR müdahalesinde Adam SONRASI/CPR ÖNCESİ ağırlıklar ile CPR SONRASI
ağırlıkların farkı kaydedilir. Her giriş satırı ve çıkış sütunu için:
L_i = sum_k ||w_i,k^sonra − w_i,k^önce||_2 /
      max(||w_i,faz-başı||_2, 10^-8).
Ham pay, payda, faz içi müdahale sayısı, r_i dağılımı, satır/sütun
medyanı ve nicelikleri birlikte verilir. L_i birikimli müdahale yolu
uzunluğudur; net yer değiştirme veya davranışsal fayda değildir.
Adam kaynaklı değişim bu paya dahil edilmez.
Faz2 başlangıcı sıfır normlu satırlar ayrıca işaretlenir.

Onaylı sayısal etkinlik kontrolü:
40.000 örneklik tek-rejim C ve ideal-yönlendirmeli D uzman kontrolünde,
son 64 yerel güncellemede giriş satırları L_i medyanı en az 0,001 olmalı;
tüm değerler sonlu, müdahale sayısı saat kuralıyla uyumlu olmalı.
Bu, ağırlık normunun %0,1'i büyüklüğünde birikimli hareket eşiğidir;
literatürden türetilmiş etkililik eşiği değil, deneysel mekanik alt sınırdır.
Üç kontrol çiftindeki her zorunlu kontrol sağlamazsa güç pilotuna geçilmez.
Öğrenilebilirlik ve diğer kontrol koşulları ayrıca geçerli kalır.
Ana deneyde aynı tanılar raporlanır; küçük hareket nedeniyle ana çift
çıkarılmaz ve hiperparametreler sonradan değiştirilmez.

## 6. Naif tabanlar ve tanılar

Seyrek-A faz 1–2'de A ile aynıdır; faz 3–4 ortak global grup sayacında
sırasıyla 2'ye veya 4'e bölünen gruplarda tek Adam adımı yapar.
Atlanan gruplar sonradan eğitilmez; optimizer momentleri ve adım sayacı
atlanan grupta ilerlemez. Tüm örneklerde tahmin üretilir.
Faz-3 gerçek adım sayıları 32 ve 16; ilk 480 faz-4 örneğinde 15 ve 7'dir.
Bu nedenle D480 tüm koşullarda aynı örnek penceresidir;
seyrek koşullarda 30 gerçek adım olduğu iddia edilmez.

Seyrek-A-75, diğer seyrek koşullar gibi A'nın faz2 model ve optimizer
durumundan dallanır. Faz 3–4'te global grup indeksi 4'e bölünen gruplar
atlanır, diğer gruplarda tek Adam adımı yapılır. Atlanan veri sonradan
kullanılmaz; optimizer momentleri ve adım sayacı ilerlemez.
40k/10k/1024/4k düzeninde faz3'te 48, faz4 ilk 480 örnekte 23
gerçek güncelleme vardır. Faz yapısı değişirse aynı takvimle yeniden sayılır.
Her güç-pilotu ve ana-deney çiftinde çalıştırılır; referans zarfına,
ana 2×2'ye veya birincil test ailesine eklenmez.
Güncelleme oranının ara değerde olması öğrenim doğruluğunun da
seyrek-A-50 ile A arasında kalacağını garanti etmez.

Donmuş-F2 faz 3–4'te tüm ağırlık ve optimizer durumunu korur.
Kendi referansına karşı aynı tahmin yordamıyla hasarı ve D480 tam sıfırdır.
R2 doğruluğu doğrudan ölçülür; öğretmen uyumuna eşit kabul edilmez.
Replay'in kendi faz-2 donmuş kopyası ayrıca eğitimsiz karşılaştırma olarak verilir.

Yakın k-NN: ham 32 gözlemde Öklid uzaklığı, son 256 çift, k=5,
eşit oyda küçük sınıf indeksi; eşit uzaklıkta daha yeni örnek öncelikli.
Yetersiz geçmişte mevcut örneklerin tamamı, boş geçmişte sınıf0.
Tahmin sonrası ekleme; faz sınırında pencere sıfırlanmaz.
Gürültülü etiket kullanılır, değerlendirme verisi pencereye girmez.
Pencerenin 256 örnekte yenilenmesi yüksek doğruluk garantisi değildir.

Replay tanısı: örnek kökeni, zaman indeksi ve değerlendirici için temiz
iki-kural hedefleri ayrı izlenir. Gerçek rejim öğrenme girdisi değildir.
Örneklenen temiz tarihsel kuralın güncel temiz kuralla uyuşmama payı
ve gürültü kaynaklı uyuşmazlık ayrı raporlanır.
Korelasyonlar tohum başına, sabit 16-örneklik gruplarda tanısaldır;
nedensel kanıt veya ana 2×2 ölçütü değildir.
Tanı açık/kapalı replay tahminleri birebir eşleşmelidir.

## 7. Ölçümler ve seyrek-A referansı

### Donmuş değerlendirme: tüm tahmin durumu korunur

Her faz sonunda ağırlıklar, bağlam penceresi, yönlendirici, uzmanlar,
yerel/global sayaçlar ve varsa k-NN belleği birlikte kopyalanır.
Değerlendirme boyunca bu kopyaların hiçbiri güncellenmez; değerlendirme
girdileri veya etiketleri geçmişe eklenmez. Test sırası sonucu değiştirmemelidir.

B/D'de faz sonunun gerçek 132-boyutlu bağlamı kullanılır. Yönlendiricinin
bu bağlamdaki en yüksek skorlu uzmanı seçilir; eşitlikte küçük indeks.
Donmuş ölçümde zorunlu keşif kapalıdır; uzman seçimi tüm testte sabittir.
Bu, çevrimiçi keşif içeren sistemden ayrı, açgözlü donmuş politika ölçümüdür.
İdeal uzman seçimi yalnızca ek tanıdır; gerçek sistem doğruluğunun yerine geçmez.
A+bağlam her test girdisini faz sonundaki aynı sabit bağlamla birleştirir.
k-NN faz sonundaki gerçek son-256 belleğiyle tahmin yapar; belleği
test örnekleriyle doldurmak veya gerçek kural etiketleriyle ısıtmak yasaktır.

Aynı test girdileri için bir kez üretilen tahmin dizisi, değerlendiricide
hem R1 hem R2 temiz hedefleriyle karşılaştırılır. Kural başına farklı
bağlam hazırlanmaz. Böylece faz3 modelini R1'de ölçmek yeniden R1
öğrenimine veya yönlendiriciye R1 kimliği vermeye dönüşmez.
Uzman-kural eşleme kalibrasyonu da uzman ağırlıkları veya bağlamı değiştirmez.

D480'in faz2 donmuş referansı da tüm faz2 tahmin durumunun kopyasıdır.
B/D referansında keşif kapalı, faz4 çevrimiçi sisteminde keşif protokoldeki
gibi açıktır; farkın bu politika ayrımını da içerdiği ayrıca raporlanır.
Donmuş-F2 tabanı bağlamsız A kopyasıdır; kendi referansıyla tam sıfır
hasar ve D480 kontrolü bu koşul için geçerlidir.

Keşif grupları dışlanmış ikincil D480:
faz4 ilk 480 örnekte global keşif takvimine düşen gruplar çıkarılır.
Aynı takvim maskesi bütün koşullara uygulanır; kalan örneklerin çevrimiçi
hataları ile o yöntemin faz2 donmuş referans hataları eşleştirilir.
Kalan örnek sayısı, toplam fark ve örnek başına fark birlikte raporlanır;
480'e bölünmez. Örnek kalmazsa metrik tanımsızdır.
Grup sayacı 1'den başlatıldığında mevcut 40k/10k/1024 düzeninde faz4
global grupları 3190–3219'dur: 3192, 3200, 3208 ve 3216 keşiftir.
Dolayısıyla 64 örnek dışlanır, 416 kalır. Değişen faz düzeninde maske
aynı global kuralla yeniden hesaplanır, bu sayılar sabit varsayılmaz.
Bu analiz önceki keşif güncellemelerinin modeldeki etkisini kaldırmaz;
keşifsiz eğitilmiş sistemin karşıolgusal sonucu değildir.
Birincil D480 ve I bütün 480 örneği kullanmaya devam eder.

Her yöntem/çift için aynı bağımsız 20.000 M2 girdisinde faz 2/3/4 sonunda
ve faz4'ün 480'inci örneğinin grup güncellemesi, varsa CPR müdahalesi ve
geçmiş/bellek güncellemesi tamamlandıktan hemen sonra alınan kopyada
R1 ve R2 doğrulukları; hasar, toparlanma, mutlak doğruluklar yayımlanır.
D480 ve D480/480, faz başına toplam/örnek başına kâhin pişmanlığı,
gerçek adım, işlenen örnek, bellek ve süre ayrıca verilir.

Birincil düzlem:
x = faz3 sonu donmuş R2 doğruluğu (öğrenim).
y = faz4'te 480 örnek işlendikten sonraki donmuş R1 doğruluğu (erken geri dönüş).
Her iki eksen aynı bağımsız değerlendirme girdilerinde, tüm tahmin durumu
donmuş olarak ölçülür. y bir toparlanma ölçüsüdür; yeniden öğrenme öncesi
koruma değildir. Faz3 sonu R1 ikinci zorunlu düzlem, faz4 sonu R1 yardımcı
ölçümdür. D480 ayrı çevrimiçi maliyettir ve yeniden tanımlanmaz.

Referans dört noktadır: donmuş-F2, seyrek-A-25, seyrek-A-50 ve A.
Her çiftte x_min ve x_max bu dört noktadan hesaplanır; x_max'ın A olduğu
varsayılmaz. Aynı x_max'taki referanslar arasında en yüksek y seçilir;
bu değere y_sağ denir. A'nın kendi koordinatları ayrıca yayımlanır.
F_i(x) üst konkav zarftır: negatif olmayan, toplamı 1 olan referans
karışımlarında ortalama x tam istenen değere eşitken en büyük y.
Bu bir raporlama referansıdır; eğitilmiş yeni yöntem değildir.

B ve D için her çift aşağıdaki ayrık kategorilerden birine atanır:
- Destek içi S: x_min ≤ x_m < x_max. G_i = y_m − F_i(x_m).
- Sağ taraf R: x_m ≥ x_max. P_i=1 ancak y_m ≥ y_sağ ve en az bir
  koordinatta kesin üstünlük varsa; aksi durumda P_i=0.
  Tam koordinat eşitliği “eşit”, daha yüksek öğrenim fakat daha düşük
  y “ödünleşme” altkategorisidir. Ödünleşmede G tanımsızdır.
- Sol taraf L: x_m < x_min. G ve Pareto başarı değerlendirmesi tanımsızdır.
Referans x değerlerinin hepsi eşitse S boştur, R kuralı yine uygulanır.
Kararlar yuvarlanmamış doğru tahmin sayılarıyla, aynı değerlendirme
büyüklüğü üzerinden alınır; toleransla sınır kaydırılmaz.
Sağda yalnızca uç referans noktasına Pareto baskınlığı ölçülür;
bu bütün referans zarfını baskıladığı iddiası değildir. Ekstrapolasyon yoktur.

İki ayrı koşullu birincil bileşen:
1. S çiftlerinde ortalama G. Pratik üstünlük sınırı 0,02'dir.
2. R çiftlerinde Pareto baskınlık oranı sum(P_i)/n_R.
   Payda yalnızca başarılı çiftler değil, eşitlik ve ödünleşme dahil tüm R'dir.
Her yöntemde n_S, n_R, n_L ve sağ altkategoriler N ile birlikte yayımlanır.
Altgruplar gerçekleşen sonuçlarla tanımlıdır; çıkarım bu altgruplara
koşulludur, tüm jeneratör popülasyonuna üstünlük değildir.
G ve P tek puanda birleştirilmez; sol/ödünleşme çiftleri sıfır G yapılmaz.

Onaylı karar eşikleri: ilgili altgrupta en az 10 çift varsa,
G için tek taraflı %98,75 bootstrap alt sınırı 0,02'den büyük olduğunda
“destek içinde pratik üstünlük”; P için tek taraflı %98,75
Clopper–Pearson alt sınırı 0,50'den büyük olduğunda
“sağ tarafta çoğunluk Pareto baskınlığı” raporlanır.
B/D × iki bileşen = dört iddia için Bonferroni toplam alfa 0,05.
Boş veya 10'dan küçük altgrupta ilgili iddia sonuçlandırılmaz;
diğer bileşen iptal edilmez. P tamamen 1 veya 0 olduğunda da kesin
binom aralığı kullanılır; sıfır genişlikli bootstrap aralığı kullanılmaz.
Bu eşikler onaylı tasarım tercihleridir; literatürün zorunlu eşikleri değildir.

C ve diğer koşulların konumları tanısaldır. Destek dışı gözlemler bütün
analizi iptal etmez; bütün çiftler raporda ve I analizinde korunur.
Bir bileşenin olumlu sonucu diğerindeki ödünleşmeyi örtmez.
Bu kural A+bağlam veya k-NN'yi geçmeyi garanti etmez; genel mimari
üstünlüğü için bu rakiplerin sonuçları da birlikte değerlendirilir.

### Seyrek-A-75 ile ampirik kalibrasyon

Dört referans noktası aynen korunur: donmuş-F2, seyrek-A-25,
seyrek-A-50 ve A. Seyrek-A-75 bu zarfı hesaplamaya katılmaz.
Aynı donmuş x/y eksenleri ve S/R/L sınıflandırması kullanılır.

S içinde G75_i = y75_i − F_i(x75_i) hesaplanır.
İşaretli ortalama G75, ortalama |G75|, çift başına değerler ve
n_S75/n_R75/n_L75 birlikte raporlanır; sağ ve sol gözlemlere sıfır G
atanmaz. R içinde aynı kesin baskınlık kuralıyla P75 oranı hesaplanır:
payda eşitlik ve ödünleşme dahil bütün R75 çiftleridir.
R75 boşsa oran tanımsızdır. Oran ve payda betimsel olarak verilir;
B/D'nin birincil alfa ailesine yeni bir test eklenmez.

G75 teorik olarak sıfır değildir. Dört noktalı enterpolasyonun eğriliği,
sonlu eğitim ve değerlendirme değişkenliği birlikte etkili olabilir.
İşaretli ortalama sıfırdan uzaksa sistematik zarf sapması açıklaması;
işaretli ortalama küçük, mutlak ortalama büyükse işaretleri değişen
sapma/gürültü açıklaması incelenir. Bu örüntüler nedenleri kesin ayırmaz;
karşıt sistematik sapmalar da ortalamada birbirini götürebilir.
G75, B/D'nin gerçek sıfır dağılımının kanıtı değil, ampirik duyarlılık tanısıdır.

Güç pilotu için onaylı durma kuralı:
- 12 çiftte en az 6 destek-içi Seyrek-A-75 çifti bulunmalıdır.
  Daha azsa kalibrasyon yetersizdir; ana deney başlamaz.
- Bu destek-içi çiftlerde ortalama |G75| ≥ 0,015 ise ana deney başlamaz.
  Sayılar yuvarlanmadan karşılaştırılır; eşitlik de durma koşuludur.
- 0,015, birincil 0,02 eşiği için önceden seçilmiş ihtiyat payıdır;
  üstünlüğün tam %75'inin hata olduğu şeklinde bir ayrıştırma değildir.
- Başarısızlıkta eşik otomatik artırılmaz veya azaltılmaz. Güç pilotu
  bulguları korunur; gerekçeli yeni önkayıt revizyonu ve kullanıcı onayı
  gerekir. Değişen başarı sınırı için güç planı da yeniden yazılır.
- Kalibrasyonun geçmesi enterpolasyon hatasının her çiftte küçük olduğunu
  veya B/D için sıfır dağılımının doğrulandığını göstermez.

Ana deneyde G75/P75 yalnızca raporlanır; ana sonuçlarla eşik, N veya
yöntem değiştirilmez ve deney sonradan seçilmiş bir durma kuralıyla kesilmez.
Birincil yorumlar büyük kalibrasyon sapmaları varsa bu sınırlamayı belirtir.

P için 0,50 sınırı, B≈A durumunda R'ye koşullama ve öğrenme–koruma
ödünleşmesi nedeniyle ihtiyatlı olabilir. Bu ihtiyatlılık matematiksel
garanti değildir. R75 içindeki P75 oranı ampirik karşılaştırma sağlar,
B/D sıfır oranıyla özdeş kabul edilmez; 0,50 sınırını otomatik değiştirmez.

## 8. Etkileşim ve güç

E_i,m = D480_i,m / 480.
I_i = (E_i,D − E_i,B) − (E_i,C − E_i,A).
Negatif I, yenilemenin yönlendirme altında göreli olarak daha çok
ek-hata azalması sağlamasıdır. Her E kendi faz2 referansına bağlıdır;
I salt mekanik yeniden kullanım veya kapasiteden arındırılmış etki değildir.
Faz3 R2 ve mutlak R1 ölçümleri olmadan I yorumlanmaz.

Mevcut A/replay verisi I varyansını vermez; hesaplanmış güç yoktur.
Kontroller geçtikten sonra, ana deneyden ayrı 12 eşleştirilmiş çiftte
Seyrek-A-75 dahil tüm koşulların güç pilotu yapılır. Bu tur çalıştırılmaz.
Ana N/tohum kilidinden önce Bölüm 7'deki Seyrek-A-75 kalibrasyon
koşulları sağlanmalıdır; sağlanmazsa ana deneye geçilmez.
Hedef etkileşim büyüklüğü |I|=0,05; iki taraflı alfa 0,05, güç hedefi %80.
Pilot çift düzeyinde I standart sapması s ile planlama:
N_I = ceil(((1,96+0,842) × 1,25s / 0,05)^2).
1,25 katsayısı küçük pilotta ihtiyat payıdır; kesin güç garantisi değildir.
Birincil çıkarım artık iki farklı altgrup parametresine aittir; sağ/sol
çiftleri çıkarıp destek-içi varyansı bütün popülasyonun varyansı saymak yasaktır.
Tek destek-dışı çiftte güç sürecini durduran revizyon-0 kuralı kaldırılmıştır.

G için hedef gerçek fark 0,05, sınır 0,02; tek taraflı alfa 0,0125'e
karşılık z=2,2414 kullanılır. Pilotun ilgili S altgrubunda en az 6 çift
ve pozitif standart sapma varsa koşullu gerekli sayı:
n_G = max(10, ceil(((2,2414+0,842) × 1,25s_G / 0,03)^2)).
Bu koşullar yoksa G için güç tahmini “hesaplanamadı” raporlanır; sıfır
varyansla düşük N üretilmez. Diğer bileşen ve I planı devam eder.

P için onaylı hedef gerçek baskınlık oranı 0,80, sıfır hipotezi 0,50.
n_P, n≥10 için şu kesin binom testinin gücü en az %80 olan en küçük sayıdır:
p=0,50 altında üst kuyruk olasılığı ≤0,0125 olan en küçük başarı sayısı
kritik değerdir; güç p=0,80 altında bu kritik değere ulaşma olasılığıdır.
Bu hedef gözlenen pilot baskınlık oranıyla değiştirilmez.

Her B/D için pilotta S ve R görülme oranlarının tek taraflı %80
Clopper–Pearson alt sınırları q_S ve q_R hesaplanır.
Hesaplanabilir bir G planı ve q_S>0 varsa toplam çift gereksinimi,
Binom(N,q_S) altında en az n_G S çifti elde etme olasılığı ≥%90
olan en küçük N'dir. R için aynı hesap n_P ve q_R ile yapılır.
Hiç görülmeyen altgrup için gereksinim bilinmiyor olarak raporlanır;
bu grubun ana deneyde oluşmayacağı veya yeterli güce sahip olduğu iddia edilmez.

Ana N, 20, N_I ve hesaplanabilir bütün B/D altgrup gereksinimlerinin
maksimumudur. Hesaplanan N>100 ise bütçe yetersizdir; ana koşu başlamaz.
B veya D için iki bileşenin de güç planı hesaplanamıyorsa ana koşu
başlamaz; tanım/örnekleme planı için yeni protokol revizyonu gerekir.
I varyansı sıfır veya sonlu değilse de süreç durur.
Ana sonuçlar görülmeden hangi bileşenlerin planlanabildiği açıklanır;
hesaplanamayan bileşen için güç yeterliliği ilan edilmez.
Ana deneyde ilgili altgrup 10'dan küçükse o iddia sonuçlandırılmaz;
sonradan çift eklenmez. Altgrup sayısı planı, hedef etki altında yaklaşık
koşullu güç planıdır; ortak veya gerçekleşen %80 güç garantisi değildir.

Ana N ve tam tohum listesi ana sonuçlar görülmeden ek kilit kaydına yazılır.
Ara sonuçlarla erken durma veya N artırma yoktur.

Ana çıkarım: 10.000 kez bağımsız çift indekslerini yerine koyarak örnekle;
aynı indeksler bütün yöntemlere, iki eksene ve referans noktalarına uygulanır.
Her tekrarda çiftin kendi zarfı ve kategori üyeliği birlikte taşınır;
G ortalaması o tekrarın S çiftlerinde hesaplanır. Önce tüm çiftlerin
noktalarını ortalayıp tek zarf kurmak farklı bir ölçüttür ve kullanılmaz.
S içermeyen tekrarda G tanımsızdır; boş tekrar oranı yayımlanır.
Boş olmayan tekrarlardan koşullu yüzdelik aralık hesaplanır; boş tekrar
oranı %1'i aşarsa G çıkarımı sonuçlandırılmaz. R oranı için birincil
çıkarım yukarıdaki kesin binom aralığıdır; bootstrap yalnızca yardımcıdır.
I için çift düzeyinde ortalama ve iki taraflı %95 yüzdelik aralık verilir;
etkileşim bu taslakta ikincil, doğrulayıcı aile dışı analizdir.
480 zaman adımı veya örtüşen bağlam satırları bağımsız tekrar sayılmaz.
Değerlendirme örnekleri üzerinden koşullu bootstrap verilirse ikincil
olarak etiketlenir; eğitim/jeneratör varyansının yerine geçmez.
Güç pilotu ana bootstrap örneklemine dahil edilmez.

## 9. Önkoşullar ve durma kuralları

Aşamalar: protokol onayı → jeneratör kabulü → tek-rejim kontrolleri/kapı →
gerekirse filtreli süre pilotu → güç pilotu → N/tohum kilidi → ana deney.
Bu belgeyi yazmak bu aşamaları geçmiş olmak değildir.

v0.4 adayı: normalize marj eşiği 0,25, her iki kural şartı birlikte;
normalizasyon filtresiz bağımsız eşit M1/M2 karışımında 20.000 örnek;
ofset yeniden ayarlanmaz. M1/M2 ayrı dışlama tavanı %30.
Kabulde her sınıf ve dört karışım/kural kesiti %18–35;
iki karışımda uyuşmazlık %40–70. Adaylar sırayla, en fazla 200.
Dışlama ve kabul ölçümü aynı eğitim verisinden yapılmaz.
Aday başına dışlama kontrolünde her karışım için 100.000 teklif;
denge/uyuşmazlık kontrolünde her karışım için 20.000 kabul edilmiş örnek.
Her karışımda 1.000.000 teklif bütçesi aşılırsa aday reddedilir.
Tek bir adayın reddi bütün sürümün otomatik reddi değildir; tavan sonunda
yeterli uygun jeneratör yoksa süreç durur. Bant veya ofset değiştirilmez.

Kapı: temel ağ R1/M1 ve R2/M2 tek-rejim kontrolleri; her biri 40.000
gürültülü eğitim, bağımsız 20.000 eşik kalibrasyonu ve 20.000 temiz test.
Eşik çoğunluk + 0,9 × (1−çoğunluk), Wilson alt sınırı eşiği aşmalı.
C'nin aynı kontrolü ve ideal uzman seçimiyle D uzman kontrolleri de verilir.
Üç ayrı kontrol çiftinde tüm zorunlu kontroller geçmeden güç pilotu yok.
C/D kontrolü başarısızsa ana model ayarları değiştirilmez; sürüm revizyonu gerekir.

Yönlendirici kontrolü: aynı girdilerde R1/R2 ayrımı için bağımsız
eğitim/test akışları; bunun rejim kimliğiyle denetlenen bir tanı olduğu
açık etiketlenir, kontrol ağırlıkları ana yönlendiriciye aktarılmaz.
Bu tanı temsilin yeterliliğini sınar, gerçek çevrimiçi yönlendirmeyi doğrulamaz.
Gerçek çevrimiçi B/D için ayrı pilotta uzman kullanım sayıları, karşıolgusal
kayıp, ideal-yönlendirme farkı ve uzmanlaşma tablosu incelenir.
Kontrol başarı ölçütü: bağımsız tanı bloklarında dengeli rejim doğruluğu
en az %90; B/D tek-rejim uçtan uca temiz doğruluk kaybı aynı uzman
referansından en fazla 2 puan. Bu eşikler onaylı tasarım seçimleridir.
Uzman açlığında veya çökmüş kullanımda bunu gizleyen yeniden eşleme yoktur.

v0.4 kapıyı geçerse 40k/10k hazırlık ve 4k toparlanma korunarak ayrı üç
pilot çiftinde 1024/1536 faz3 adayları sınanır. A faz2 ≥%86 ve üç çiftte
hasar 20–40 puan; en kısa uygun aday alınır. Hiçbiri uymazsa yeni sürüm,
otomatik aday araması yok. v0.3'ün seçimi filtre etkisini doğrulamaz.
Kapı başarısızlığı kapı tanımını sorgulamayı gerektirebilir, fakat sorunun
kesinlikle kapı olduğu anlamına gelmez. Formül ancak yeni önkayıtla değişir.

## 10. Ayrı veri bölümleri, kaynaklar ve kayıt

Kontrol, süre pilotu, güç pilotu ve ana deney farklı jeneratör aday
havuzları ve farklı eğitim/değerlendirme akışları kullanır.
Öğretmen havuz başlangıçları sırasıyla 10000/20000/30000/40000.
Her bölümde en fazla 200 aday, artan sırada ilk uygunlar;
kontroller için 3, süre için 3, güç için 12, ana için N farklı jeneratör.
Jeneratör seçimi öğrenci performansına göre yapılmaz.
Ana çift başına bir farklı başlangıç/eğitim tohumu; yöntemler çift içinde
aynı veri ve eşleşebilir başlangıçları paylaşır.
Ana başarısız koşullar performansa göre çıkarılmaz veya değiştirilmez.

Rastgelelik kök tohumu 20260916; bölüm, çift, rol, faz, uzman ve tekrar
indekslerinden hiyerarşik bağımsız akışlar türetilir. Etiketli roller:
öğretmen, ofset, ölçek, kabul, dışlama, model0, model1, eğitim,
CPR, reservoir-değiştirme, reservoir-örnekleme, eşleme, değerlendirme,
güç-hesabı, bootstrap. Türetilen sayısal tohumlar kilit manifestinde yazılır.
Mevcut jeneratörün örtük ofset tohumu açık rol tohumu ile değiştirilirse
bu veri üretim sürümü olarak kaydedilir; eski sonuçla bit eşitliği varsayılmaz.

Her eğitimde model, optimizer, yönlendirici, fayda EMA'sı, yerel saatler,
tamponlar ve RNG durumları; girdiler, gizli örnekler, temiz/gürültülü hedefler,
çevrimiçi tahminler, yönlendirme kararları ve tüm donmuş tahminler saklanır.
Kontrol noktaları faz sonları ile faz3/4 ilk 480 örnekte 16'lık aralıklarla alınır.
Kayıt yükleme ve ileri tahmin eşitliği test edilir. Dosyalar üzerine yazılmaz.
Protokol, kaynak, ortam, tohum ve dosya özetleri koşu öncesi arşivlenir.

Parametre, aktif/toplam uzman sayısı, ek gradyan maliyeti, optimizer adımı,
eğitim örneği sayısı, bellek ve süre ayrı raporlanır.
CPR örnek-başına gradyanları ve iki uzmanlı kayıp hesapları maliyete dahildir.
Kapasite/hesaplama eşitlenmediğinden sistem düzeyinde farklar saf yapısal
katkı olarak sunulmaz. Eşit-bütçe iddiası istenirse yeni kontrol gerekir.
Sayısal hata veya kayıt uyuşmazlığında dur; aynı tohumla yalnızca belgelenmiş
yazılım düzeltmesi sonrası yeniden üretim yapılabilir. İki sürüm de korunur.

## 11. Onay ve kilitleme

Revizyon 1, 2026-09-16 tarihinde kullanıcı tarafından onaylanmıştır.
Destek-içi/Pareto ayrımı, iki donmuş eksen, uzman/arşiv tanıları,
CPR etkinlik kontrolü ve keşif maskeli ikincil maliyet bu sürümde yer alır.
Son onayla Seyrek-A-75 kalibrasyon tanısı, en az 6 destek-içi pilot
çifti ve ortalama |G75| ≥0,015 durumunda durma kuralı eklenmiştir.

Onaylı sayısal tercihler:
- Sağ taraf koşullu baskınlık oranı sınırı 0,50; güç hedefi 0,80.
- Bileşen başına en az 10 ana çift, G varyansı için en az 6 pilot S çifti.
- Dört birincil iddia için alfa 0,0125.
- CPR kontrolünde son 64 yerel adımda medyan L_i ≥0,001.
- Bölüm 8'deki altgrup güç planı ve hesaplanamayan bileşen politikası.
- Bölüm 7'deki Seyrek-A-75 kalibrasyon durma kuralı.
Destek ve kategori sayıları raporlanmadan hiçbir üstünlük iddiası yapılmaz.

İçerik kilidi bu dosyanın son baytları üzerinden SHA-256 alınarak ve
tarihli ayrı kilit özetiyle kaydedilir. Git commit kimliği ayrıca doğrulanır;
hash veya commit tarihi geçmiş tarihe ayarlanmaz. Yerel Git kaydı
bağımsız bir önkayıt deposu veya güvenilir üçüncü taraf zaman damgası değildir.
Tarihsel taslak dosya adı korunur; sürümü başlık ve kilit özeti belirler.

Kilit sonrası bu turdaki tek işler tarihli özet ve ilk Git commit'idir.
Uygulama, eğitim, jeneratör kabulü ve güç pilotu başlatılmaz.
Gelecekte uygulama testlerinin protokole uyumu denetlenmeden veri üreten
hiçbir koşu başlatılmaz. Güç ve süre pilotundan sonra revizyon 1 içindeki
izinli ek kilitler N/tohum listesi ve yazılı kuralla seçilmiş süredir.
G75 kalibrasyonu nedeniyle eşik değişmesi gerekirse bu, izinli bir sessiz
ek değil yeni revizyon ve yeniden onay gerektirir; revizyon 1 korunur.