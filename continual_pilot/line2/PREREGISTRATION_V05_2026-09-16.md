# Hat 2 — v0.5 son deneme önkayıt eki

Tarih: 2026-09-16.
Kullanıcı kararı oturum zamanı: 2026-09-16T16:14:01.679Z.
Durum: Kullanıcının onayladığı son denemenin sonuç öncesi kaydı.
Bu belgenin ham bayt özeti ayrı kilit kaydında tutulur ve koşudan önce
Git commit'i oluşturulur. Yerel tarih bağımsız zaman damgası değildir.

## 1. Geçerli belgeler ve sınırlı değişiklik

[Kilitli revizyon 1](PREREGISTRATION_DRAFT.md) ile
[onaylı kontrol uygulama eki](IMPLEMENTATION_ADDENDUM_2026-09-16.md)
aşağıdaki açık değişiklikler dışında geçerlidir. Özgün belgeler değiştirilmez.

Bilimsel parametre değişikliği yalnızca normalize marj eşiğidir:
τ = 0,25 yerine **τ = 0,1**. Başka aday eşik denenmez.
Tükenmiş 10000 havuzu yerine yeni öğretmen havuzu **11000–11199**
kullanılır; havuz başlangıcı kullanıcı tarafından sonuç öncesinde belirlenmiştir.

Bu izin kabul ve durağan kapı/kontrolleri kapsar.
Süre pilotu, güç pilotu veya ana deney başlatılmaz.
Bu turdan sonra sonuç ne olursa olsun bu araştırma hattı kapatılır.

## 2. Veriden türetilmiş gerekçe ve sınırları

[Eski v0.3 marj raporunda](../results_margin_v03/summary.json:121)
normalize marj <0,1 payı **0,1217** olarak kayıtlıdır.
Bu, v0.3 öğretmen tohumu 1000 için önceki tek-kural M1 tanısıdır;
yeni havuzun iki kuralı ve iki karışımı için ortak olasılık ölçümü değildir.
Seçim öğrenci eğitim başarısına değil, önceden var olan jeneratör
marj tanısına dayanır. v0.4 kabul başarısızlığı sonrasında yeni sürüm
oluşturulduğu açıkça belirtilir; aynı sürümde eşik gevşetmesi yapılmaz.

Eşit marjinal olasılık ve bağımsız düşük-marj olayları yaklaşımı altında:
ortak dışlama ≈ 1 − (1 − 0,1217)² = 0,22858911 ≈ %22,9.
Bu değer %30 tavanının altındadır, ancak kabul garantisi değildir.
Gerçek ortak dışlama p1 + p2 − kesişim olasılığıdır.
Ortak öğretmen bileşeni nedeniyle iki olay bağımsız olmak zorunda değildir.

Tarihsel düzeltme: eski raporda <0,25 payı yaklaşık %27 değil,
**%29,04** olarak kayıtlıdır. Bu değer v0.5 eşik seçiminin dayanağı değildir.

## 3. Değişmeyen kabul kuralları

- Her iki kuralın normalize marjı birlikte en az 0,1 olmalıdır.
- Normalizasyon, aday başına bağımsız filtresiz eşit M1/M2 karışımında
  toplam 20.000 örnekte hesaplanır; kural başına tüm skor elemanlarının
  popülasyon standart sapması kullanılır ve ölçekler sabit tutulur.
- Ofsetler filtre sonrasında yeniden ayarlanmaz.
- M1 ve M2 dışlama tavanı ayrı ayrı %30'dur.
- Her aday/karışımda dışlama 100.000 bağımsız teklif üzerinde ölçülür.
- Kabul dağılımındaki dört karışım/kural kesitinin her sınıf payı %18–35;
  her iki karışımda kural uyuşmazlığı %40–70 olmalıdır.
- Denge/uyuşmazlık için karışım başına ayrı akışta 20.000 kabul edilmiş
  örnek kullanılır; teklif bütçesi karışım başına 1.000.000'dur.
- En fazla 200 aday artan sırayla değerlendirilir; ilk üç uygun
  jeneratör seçildiğinde arama durur. Öğrenci başarısı seçime girmez.
- Kök tohum ve rol türetme yordamı korunur. Öğretmenler doğrudan
  11000 + aday indeksiyle, ofset/ölçek/kabul/dışlama akışları bu
  öğretmen kimliğinin rol tohumlarıyla belirlenir.
- Kabul edilen çiftler kabul sırasıyla 0, 1, 2 indekslerini alır.
  Eğitim/değerlendirme/model/CPR tohumları mevcut çift-rol yordamını
  korur. v0.4'te bu kontrol eğitimleri hiç çalıştırılmamıştır.
- Sayısal hata ve kayıt uyuşmazlığı kabul reddi olarak gizlenmez.

## 4. Sonuç öncesi tanısal okuma

Sınanan bütün adaylar üzerinden M1 ve M2 dışlama medyanları ayrı
raporlanır; yaklaşık beklenti %23'tür. Herhangi bir medyan **%28'i
kesin olarak aşarsa** beklentiden yüksek dışlama işareti raporlanır.
Tam %28 bu işareti tetiklemez. Bu yalnızca betimsel bir işarettir;
kabul, seçim veya durma kriteri değildir ve yeni örnek talep etmez.

Sapma; öğretmenler arası değişkenlik, farklı marjinal olasılıklar,
iki olayın bağımlılığı ve ofset/dağılım ilişkisiyle tutarlı olabilir.
Tek başına ofsetin nedensel etkisini kanıtlamaz.
İlk üç kabulde durulduğundan aday medyanı tüm olası havuzun
tarafsız popülasyon tahmini olarak sunulmaz.

## 5. Kabul geçerse aynı turdaki kontroller

Üç kontrol çiftinde R1/M1 ve R2/M2 ayrı durağan koşullardır.
Temel mimari 32→64→4, Adam 0,001 ve diğer kilitli ayarlar korunur.
Her koşulda 40.000 gürültülü eğitim, bağımsız 20.000 eşik kalibrasyonu
ve 20.000 donmuş temiz değerlendirme örneği kullanılır.
Kapı: Wilson %95 alt sınırı, çoğunluk + 0,9 × (1 − çoğunluk)
eşiğini kesin olarak aşmalıdır. Nokta doğruluğunun aşması yetmez.

C ve ideal-D izole uzman kontrolleri aynı kurallarla değerlendirilir.
CPR son 64 yerel güncellemede giriş satırı L_i medyanı en az 0,001,
değerler sonlu ve müdahale sayısı yerel saatle uyumlu olmalıdır.
Payda durağan faz başlangıcındaki ağırlık normudur.

Temsil tanısı: bağımsız eğitim/test rol akışları, kural başına 512
örtüşmesiz 64 örneklik blok, ortak M2 girdileri ve ayrı gürültülü
etiketler; sıfır başlangıçlı 132→2 doğrusal ağ ve 300 tam-batch adımı.
Dengeli test doğruluğu en az %90; ham ve kural başına doğruluk da verilir.

B/D kaybı uzman-0 başlangıcını paylaşan tam güncellenen tek ağa karşı
en fazla 2 puandır. B referansı A; D referansı mevcut C kaydıdır,
C tekrar eğitilmez. Uzman-1 referansları ayrıca raporlanır;
birincil referansın yerine geçirilmez. İdeal donmuş uzman seçimi
bu karşılaştırmadan ayrı tanıdır. Zorunlu keşif/açgözlü kullanım
ve yerel uzman güncellemeleri raporlanır.

Mevcut yürütme sırası korunur: bir durağan koşulun altı benzersiz
koşusu tanı tablosu için tamamlanır; zorunlu başarısızlık başka
koşula/çifte geçişi durdurur. İki durağan koşul geçerse temsil tanısı
yapılır. Gerçekleşmeyen ölçümler açıkça çalıştırılmadı olarak yazılır.

## 6. Koşu öncesi dış kayıt önkoşulları

v0.4 ham arşivinin dış yedeği alınmış ve geri indirilerek
manifest dahil 3.651 dosyanın tamamında SHA-256/boyut eşleşmesi
doğrulanmıştır: [yedek kanıtı](BACKUP_V04_VERIFICATION_2026-09-16.json).
Ham arşiv Git geçmişine eklenmemiştir; GitHub sürüm eklerindedir.

Özgün protokolün Bitcoin tasdiki 967295 numaralı blokta doğrulanmıştır:
[doğrulama kaydı](OTS_VERIFICATION_2026-09-16.json).
Merkle taahhüdü, başlık özeti ve iş ispatı yerelde; zincirdeki konumu
iki HTTPS gezgininde kontrol edilmiştir. Yerel tam zincir doğrulaması
yapılmamıştır. Bu tasdik yeni v0.5 belgesinin zaman damgası değildir.

Bu ek kilitlenip commit edilmeden ve v0.5'e bağlı mekanik test kanıtı
geçmeden kabul koşusu başlamaz. Eski kaynaklar ve sonuçlar korunur.

## 7. Kesin kapanış kuralı — kullanıcı kararı

Kabul başarısızsa yeni τ, tavan veya havuz denenmez.
Kapı veya zorunlu kontroller başarısızsa yeni bilimsel revizyon yazılmaz.
Başarısız sonuçlar korunur; tur durur ve öğrenilenler yazısıyla
açık depo olarak sonuçlandırılır. Kural sonuçlara göre yeniden açılmaz.

Bütün kontroller geçse dahi bu hattın son denemesi tamamlanmıştır;
süre/güç pilotu veya ana deney başlamaz.
Kilitli kapsamlı protokolün uygulanmayan sonraki aşamaları, özgün
belgeyi değiştirmeden ayrı kapanış belgesinde gelecek iş olarak işaretlenir.
Bu etiket yeni çalışma izni veya devam taahhüdü değildir.

Sayısal/altyapı hatasında otomatik tekrar yapılmaz; hata kayıtları
korunur ve bilimsel başarısızlıkla karıştırılmaz.
Rapor; kabul kaydı, dışlama oranları, gerçekleşen kapı tabloları,
karışıklık matrisleri, öğrenme eğrileri, CPR etkinliği, yönlendirici
kontrolleri, süre ve ölçülebilen maliyeti içerir.
Ölçülmemiş parasal işlem maliyeti veya çalıştırılmamış sonuç uydurulmaz.