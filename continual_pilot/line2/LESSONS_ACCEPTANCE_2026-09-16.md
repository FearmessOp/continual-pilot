# v0.4 kabul sonrası tasarım dersi

Tarih: 2026-09-16.
Durum: Sonuç sonrası değerlendirme; yeni önkayıt veya çalıştırma izni değildir.

## Gözlem ve tasarım sorumluluğu

[Sonuç raporunda](REPORT_CONTROL_V04_01.md) kayıtlı 200 adayın tamamı
M1 için %30 dışlama tavanını aştı. En düşük dışlama %30,080,
medyan %46,2445 idi. Normalize marj eşiği 0,25 ve dışlama tavanı %30
bu havuzda birlikte sağlanamadı. Tavan gevşetilmeden süreç durduruldu.

Bu sonucu yalnızca jeneratör aramasının başarısızlığı olarak adlandırmak
tasarım sorununu eksik anlatır: filtre eşiği ile dışlama tavanı birbirine
bağlıdır ve kilitlemeden önce mevcut marj tanısıyla birlikte incelenmeliydi.
Bu uyum kontrolü yapılmadı. Ancak sonlu bir havuzdaki başarısızlık,
iki sayının bütün olası jeneratörlerde matematiksel olarak tutarsız
olduğunu kanıtlamaz.

## Kilit öncesinde yapılması gereken yaklaşık hesap

Bir girdinin R1 veya R2 altında eşik altı marja sahip olması ortak
filtreden dışlanması için yeterlidir. Dolayısıyla:

Ortak dışlama = p1 + p2 − iki düşük-marj olayının kesişim olasılığı.

İki olayın bağımsız olduğu ve p1 = p2 = p varsayımı altında:

Ortak dışlama ≈ 1 − (1 − p)².

Kullanıcının belirttiği yaklaşık p = %27 değeriyle bu hesap
yaklaşık %46,71 verir; gözlenen yaklaşık %46 medyanla uyumludur.
Buradaki %27, bu not hazırlanırken eski rapordan yeniden doğrulanmış
bir ölçüm değil, kullanıcının yaklaşık hesabında kullandığı değerdir.

[Önceki marj raporunda](../results_margin_v03/summary.json) v0.3 için
normalize marj <0,1 payı %12,17 olarak raporlanmıştı.
Aynı bağımsızlık ve eşit marjinal olasılık yaklaşımı bunun için
yaklaşık %22,86 ortak dışlama öngörür.

Bu hesaplar kilit öncesi bir uyarı ve uyum kontrolü sağlayabilirdi.
İki kural ortak öğretmen bileşenini paylaşır; bağımsızlık varsayılamaz.
Eski tek-kural/dağılım ölçümü yeni öğretmen havuzunun iki kuralına ve
iki karışımına doğrudan taşınamaz. %22,86 bir kabul garantisi değildir.

## Dengeye ilişkin ikinci sinyal

156 aday denge ve dışlama nedeniyle, ayrıca 5 aday denge, uyuşmazlık
ve dışlama nedeniyle reddedildi. Toplam 161 adayda denge ihlali vardır.

Marja göre koşullama sınıf paylarını değiştirebilir; düşük-marj kütlesi
sınıflar arasında eşit dağılmak zorunda değildir. Gözlem bu açıklamayla
tutarlıdır. Bununla birlikte aynı adayların filtresiz sınıf paylarıyla
eşleştirilmiş karşılaştırma olmadan her denge ihlalinin filtre tarafından
oluşturulduğu kesinleştirilemez. Daha düşük eşik denge sorununu
hafifletebilir, fakat bunu garanti etmez.

## Kayda geçirilen ders

Birbirine bağlı önkayıt parametreleri, mevcut tanı verisiyle ortak
uyum kontrolünden geçmeden ayrı ayrı “makul sayılar” olarak kilitlenmez.

Kontrol; varsayımları, kullanılan veri bölümünü, ortak olay olasılığını,
karışımlar arasındaki farkları ve belirsizliği açıkça belirtmelidir.
Mevcut tanı verisinden tasarım yapmak ile sonuç görüldükten sonra
aynı sürümün başarı sınırını değiştirmek birbirinden ayrılmalıdır.

## Yalnızca kullanıcı kararıyla değerlendirilebilecek sonraki sürüm

Kullanıcının önerdiği tek aday normalize marj eşiği 0,1'dir.
Seçimin gerekçesi öğrenci eğitim sonucu değil, mevcut jeneratör marj
tanısıdır. Deneme-yanılmalı eşik araması önerilmemektedir.

Yeni revizyon onaylanırsa sınıf bandı ve %30 dışlama tavanı korunur.
Kabul yine başarısızsa filtre yaklaşımını terk etme ve kapı tanımını
yeniden değerlendirme önerisi gündeme gelir; otomatik kapı değişikliği
veya kapı çalıştırması yapılmaz.

Önceki kontrol havuzunun sonuçları artık görülmüştür. Gelecekteki revizyon,
havuzun yeniden kullanımını ya da yeni havuz seçimini açıkça belirtmeli;
görülmüş havuz bağımsız yeni doğrulama verisi olarak sunulmamalıdır.

Bu not eşiği değiştirmez, yeni revizyonu onaylamaz ve tohum seçmez.
Bu turda kabul, eğitim, test, tanı, süre pilotu, güç pilotu veya ana deney
çalıştırılmaz. Bilimsel çalışma kullanıcı kararında durmaktadır.