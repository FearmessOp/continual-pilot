# Hat 2 — Onaylı kontrol uygulama eki

Tarih: 2026-09-16.
Kullanıcı onayının alındığı oturum zamanı: 2026-09-16T15:22:57.470Z.
Bu zaman yerel oturum kaydıdır; bağımsız zaman damgası değildir.

## 1. Durum ve kapsam

Kullanıcı, sonuç üretilmeden sunulan birinci kontrol önerisini aşağıdaki
netleştirmelerle onayladı. Bu belge o onayın uygulama kaydıdır.
[Kilitli revizyon 1](PREREGISTRATION_DRAFT.md) değiştirilmez.
Kilitli belgenin SHA-256 özeti:
0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

Bu ek, temsil tanısının bütçesini ve durağan sistem karşılaştırmasındaki
referansı açıklar; kabul bantlarını, öğrenilebilirlik eşiğini, öğrenci
mimarisini, yönlendirme veya CPR mekaniğini değiştirmez.

## 2. Rejim kimliğiyle denetlenen temsil tanısı

- Girdiler filtrelenmiş v0.4 M2 dağılımından gelir.
- Her veri bölümünde aynı girdiler R1 ve R2 ile ayrı gürültülü etiketlenir.
- Eğitim ve test, bağımsız tohumlu akışlardan oluşturulur.
  Aynı akışın ayrık pencereleri eğitim/test bağımsızlığının yerine geçmez.
- Eğitimde kural başına 512 adet 64 örneklik bağlam bloğu vardır.
- Testte de kural başına 512 adet 64 örneklik bağlam bloğu vardır.
- Bloklar örtüşmez. Her blok yalnızca kendi 64 gözlenmiş gürültülü
  etiketli çiftinden tek bir 132 boyutlu özet üretir.
- Temsil tanısının hedefi gerçek rejim kimliğidir. Bu, yalnızca
  değerlendiriciye ait denetimli bir tanıdır; öğrenilmiş yöntemlerin
  yönlendirici hedefinin tanımını değiştirmez.
- Tanı ağı 132→2 doğrusaldır; ağırlıklar ve bias sıfırdan başlar.
- Adam öğrenme oranı 0,001; diğer Adam ayarları kilitli protokolle aynıdır.
- Eğitim bütçesi 300 tam-batch güncellemedir; erken durma veya arama yoktur.
- Başarı ölçütü, bağımsız testte dengeli rejim doğruluğunun en az %90 olmasıdır.
- Dengeli doğruluk, her kuralın 512 test bloğundaki doğruluğunun ortalamasıdır.
  Ham doğruluk, iki kuralın doğrulukları, blok sayıları ve tahminleri de kaydedilir.
- Kontrol ağırlıkları B/D yönlendiricisine aktarılmaz.
  Bu kontrolün başarısı gerçek çevrimiçi yönlendirmenin başarısını kanıtlamaz.

## 3. Durağan B/D sistem kaybının birincil referansı

Her kontrol çiftinde R1/M1 ve R2/M2 ayrı durağan koşullardır.
Her koşulda yöntemler aynı 40.000 gürültülü eğitim örneğini paylaşır.

B'nin birincil referansı, uzman 0 ile aynı başlangıca sahip,
her 16 yeni örnekte güncellenen CPR'siz tek ağdır: A kontrolü.
D'nin birincil referansı, uzman 0 ile aynı başlangıca sahip,
her 16 yeni örnekte güncellenen CPR'li tek ağdır: C kontrolü.

D referansı ile C aynı koşudur; yeniden eğitilmez, aynı kayıt kullanılır.
Başlangıç, eğitim akışı ve CPR rastgeleliği eşleşmesi kayıtlarla doğrulanır.

Birincil kayıp = tek-ağ referansının donmuş temiz doğruluğu
eksi B/D sisteminin donmuş temiz doğruluğu.
Kayıp en fazla 0,02 olmalıdır; tam eşitlik geçer, yuvarlama uygulanmaz.
Aynı bağımsız değerlendirme girdileri ve hedefleri kullanılır.

Uzman 1 başlangıcıyla tam güncellenen ikinci tek-ağ referansı da
CPR'siz ve CPR'li olarak ayrıca raporlanır.
Bu ikinci referans, birincil uzman 0 referansını sonuçlara göre değiştirmez.

Bu karşılaştırma hem yönlendirme hatasını hem güncellemelerin iki uzmana
bölünmesinin, zorunlu keşif dahil, maliyetini kapsar.
Tek-ağ referansı her global grupta bir güncelleme alır;
B/D'de yalnızca o grupta seçilmiş uzman güncellenir.

## 4. Ayrı ideal-seçim tanısı ve kullanım tablosu

Aynı donmuş uzmanlardan ideal seçim tanısı ayrı tutulur.
Bağımsız tam güncellenen tek-ağ referansının yerine kullanılmaz.

B/D için her uzmanın yerel güncelleme sayısı, zorunlu keşif kullanım sayısı
ve açgözlü kullanım sayısı tabloda verilir.
Donmuş uzman doğrulukları ve ideal seçim farkı birlikte raporlanır.
Bu tanılar kaybın kaynağını incelemeye yardımcı olur; kullanım sayıları
tek başına yönlendirme ve bölünme maliyetlerini nedensel olarak ayrıştırmaz.

## 5. Çalıştırma sırası ve Bitcoin durumu

Kullanıcının bu onayındaki talimatı: kabul ve kapı, ek tarihlenip
ilgili uygulama testleri geçtikten sonra başlatılabilir.
GitHub'a gönderilmiş özgün OpenTimestamps makbuzunun Bitcoin onayını
beklemesi tek başına bu koşular için durdurucu önkoşul değildir.

Son kontrol: 2026-09-16T15:16:01.565462Z.
Takvim yanıtı: “Pending confirmation in Bitcoin blockchain”.
Bitcoin blok tasdiki alınmadı; bağımsız zincir doğrulaması yapılmadı.
Özgün makbuz korundu; yükseltilmiş makbuz oluşturulmadı.
Bu durum doğrulanmış Bitcoin zaman damgası olarak sunulmaz.

Uygulama, kaynak, ortam, tohum ve dosya kayıtları koşu öncesinde korunur.
Kabul başarısızsa veya zorunlu kapı/kontrol sağlanmazsa sonuçlar korunur;
sonuç görülüp ayar değiştirilmez, kullanıcı kararına dönülür.
Süre pilotu, güç pilotu ve ana deney bu turun izni dışındadır.

Bu ek yazılırken 59 mekanik test geçmişti.
Bu sayı henüz bu ekteki yeni kontrol yürütücüsünün test edildiği anlamına gelmez.
Gerçek v0.4 aday kabulü veya öğrenilebilirlik kapısı henüz çalıştırılmamıştır.