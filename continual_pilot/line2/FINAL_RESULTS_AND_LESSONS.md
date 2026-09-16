# Sonuç ve öğrenilenler — araştırma hattı kapatıldı

Tarih: 2026-09-16.
**Durum: v0.5 son denemesi tamamlandı; yeni bilimsel koşu yapılmayacak.**

## Kısa sonuç

v0.5 jeneratör kabulü geçti, ancak ilk kontrol çiftinin R1/M1
öğrenilebilirlik kapısı geçilmedi. Kullanıcının sonuç öncesinde
belirlediği kesin kapanış kuralı uygulandı. Başka eşik, havuz,
eğitim ayarı veya bilimsel revizyon denenmedi.

Bu çalışma yönlendirme ve yenilemenin sürekli öğrenmede üstünlüğünü
kanıtlamadı veya çürütmedi: bu sorunun ana deneyine ulaşılmadı.
Sonuç, sabit bütçe ve önkayıtlı kapı altında bir kontrol başarısızlığıdır.

## 1. Kabul

Tek eşik τ = 0,1; dışlama tavanı her karışımda %30.
Sınıf payı bandı %18–35, uyuşmazlık bandı %40–70.
Ofsetler filtre sonrasında değiştirilmedi.

| Öğretmen | M1 dışlama (%) | M2 dışlama (%) | Karar |
|---|---:|---:|---|
| 11000 | 27,577 | 27,612 | Denge nedeniyle red |
| 11001 | 23,615 | 21,065 | M2 dengesi nedeniyle red |
| 11002 | 23,352 | 22,305 | Kabul; çift 0 |
| 11003 | 17,526 | 16,732 | Kabul; çift 1 |
| 11004 | 21,435 | 21,301 | Kabul; çift 2 |

İlk üç uygun jeneratör bulunduğunda arama durdu: 5 aday, 3 kabul,
2 red. Kalan 195 aday incelenmedi. Hiçbir aday dışlama, uyuşmazlık
veya teklif bütçesi nedeniyle reddedilmedi.

Beş aday üzerinden dışlama medyanları M1 %23,352 ve M2 %21,301.
Yaklaşık %22,9 beklentisiyle aynı ölçektedir; %28'i aşma işareti
iki karışımda da tetiklenmedi. Bu, bağımsızlık varsayımının veya
ofset etkisinin doğrulanması değildir. İlk üç kabulde duran küçük
örneklemden popülasyon kabul oranı çıkarılmaz.

Tam kayıt: [kabul özeti](results_control_v05_01/acceptance_summary.json).

## 2. Çalıştırılan kapı: yalnızca çift 0, öğretmen 11002, R1/M1

Her benzersiz koşu aynı 40.000 gürültülü örneği aldı.
Eşik kalibrasyonu ve donmuş test ayrı ayrı 20.000 örnektir.
Kalibrasyondaki sınıf sayıları: 5146, 6505, 4370, 3979.

Çoğunluk = 0,32525.
**Ölçülen eşik = 0,32525 + 0,9 × (1 − 0,32525) = 0,932525.**
Geçiş için Wilson %95 alt sınırı bu eşiği kesin olarak aşmalıdır.

| Koşul | Temiz doğruluk (%) | Wilson %95 (%) | Kapı karşılaştırması |
|---|---:|---|---|
| A, uzman-0 başlangıcı | 92,835 | [92,469272; 93,184276] | Geçmedi |
| C, uzman-0 başlangıcı | 90,990 | [90,585262; 91,378994] | Geçmedi |
| A, uzman-1 referansı | 92,880 | [92,515301; 93,228230] | Geçmedi; tanısal |
| C, uzman-1 referansı | 90,875 | [90,468013; 91,266287] | Geçmedi |
| B sistemi | 92,790 | [92,423247; 93,140318] | Eşiğin altında; ek karşılaştırma |
| D sistemi | 90,910 | [90,503696; 91,300591] | Eşiğin altında; ek karşılaştırma |

A'nın nokta doğruluğu eşiğin 0,4175 yüzde puanı altındadır;
Wilson üst sınırı da eşikten düşüktür. Yakınlık, geçiş sayılmadı.
Aralıklar eğitilmiş modele koşulludur; eğitim-tohumu değişkenliği
ve eşik kalibrasyonu belirsizliğini kapsamaz.
Uzman-1 referansı A'nın yerine geçirilmedi.

Önkayıtta belirtildiği üzere ilk durağan koşulun altı benzersiz koşusu
tanı tablosu için tamamlandı. Zorunlu başarısızlık sonraki koşula
geçişi durdurdu. D'nin birincil tek-ağ referansı için C tekrar eğitilmedi.

## 3. CPR hareketi ve B/D sistem kontrolü

| Kontrol | Ölçüm | Karar |
|---|---:|---|
| C giriş satırları son-64-adım medyan L | 0,1010321379 | ≥0,001; geçti |
| Uzman-1 CPR referansı medyan L | 0,1011665240 | ≥0,001; geçti |
| A eksi B temiz doğruluk kaybı | 0,045 yüzde puanı | ≤2 puan; geçti |
| C eksi D temiz doğruluk kaybı | 0,080 yüzde puanı | ≤2 puan; geçti |

Her iki izole CPR kontrolünde son 64 yerel adımda 8 müdahale,
sonlu değerler ve saat eşleşmesi kaydedildi.
L, faz başlangıç normuna bölünmüş birikimli müdahale yoludur;
net ağırlık yer değiştirmesi veya davranışsal yarar değildir.
C kaydı ideal-D uzman-0 izole kontrolünde de kullanıldı;
bunlar bağımsız tekrarlar değildir.

B ve D'de kullanım tablosu aynıdır:

| Uzman | Yerel güncelleme | Zorunlu keşif | Açgözlü kullanım |
|---|---:|---:|---:|
| 0 | 2343 | 156 | 2187 |
| 1 | 157 | 156 | 1 |

B uzmanlarının R1 doğrulukları %92,790 ve %88,025;
D uzmanlarınınki %90,910 ve %87,655'tir.
Bu tek durağan rejimde kullanım uzman 0'da yoğunlaşmıştır.
Bu gözlem kural uzmanlaşması, arşivleme veya sürekli öğrenme
avantajını kanıtlamaz. Kullanım sayıları yönlendirme ve güncelleme
bölünmesi maliyetlerini tek başına nedensel olarak ayıramaz.

## 4. Karışıklık matrisleri ve öğrenme eğrileri

Matrislerde satırlar gerçek, sütunlar tahmin sınıfıdır; sıra 0–3.

| Koşul | Gerçek sınıf 0 satırı | Gerçek sınıf 1 satırı | Gerçek sınıf 2 satırı | Gerçek sınıf 3 satırı |
|---|---|---|---|---|
| A | 4507,142,147,227 | 89,6259,132,75 | 90,75,4197,8 | 264,127,57,3604 |
| C | 4401,168,224,230 | 136,6158,202,59 | 104,138,4113,15 | 321,123,82,3526 |
| A uzman-1 | 4502,142,144,235 | 93,6261,128,73 | 87,72,4203,8 | 266,120,56,3610 |
| C uzman-1 | 4379,170,237,237 | 132,6154,205,64 | 98,132,4126,14 | 322,135,79,3516 |
| B | 4547,138,119,219 | 96,6258,121,80 | 112,77,4173,8 | 290,127,55,3580 |
| D | 4452,157,198,216 | 146,6157,194,58 | 129,151,4078,12 | 341,130,86,3495 |

| Koşul | İlk 1000 çevrimiçi temiz (%) | Son 1000 çevrimiçi temiz (%) |
|---|---:|---:|
| A | 60,3 | 93,6 |
| C | 60,3 | 91,4 |
| A uzman-1 | 62,8 | 93,5 |
| C uzman-1 | 62,9 | 90,8 |
| B | 58,6 | 93,3 |
| D | 58,5 | 91,4 |

Tam 40 blokluk eğriler, sınıf geri çağırımları ve uzmanların iki
kurala karşı ölçümleri [kontrol raporundadır](results_control_v05_01/controls/pair0/condition0/condition_summary.json).
Çevrimiçi blok ortalamaları donmuş kapı doğruluğunun yerine geçmez.
Son bloktan yakınsama veya daha uzun eğitimle başarı garantisi çıkarılmaz.

## 5. Çalıştırılmayanlar

R2/M2 durağan eğitimi, çift 1 ve çift 2 kontrolleri, temsil tanısı
ve onun ≥%90 başarı kontrolü çalıştırılmadı.
**Temsil tanısı doğruluğu yoktur; eski prob değerleri taşınmadı.**
R1'de eğitilmiş ağların aynı M1 girdilerinde R2 etiketlerine karşı
tanısal ölçümleri, R2/M2 öğrenilebilirlik kapısı değildir.

Süre pilotu, güç pilotu, ana deney, seyrek zarf üstünlük testleri
ve yönlendirme×yenileme etkileşim çıkarımı yapılmadı.
Başarısızlık yalnızca gerçekleşen ilk kontrol çiftine koşulludur;
diğer öğretmenlerde de başarısız olunacağı iddia edilmez.

## 6. Süre, hesaplama ve kayıtlar

- Kabul: 13,4702069 saniye.
- İlk durağan koşul, kayıt ve değerlendirme dahil: 93,8466542 saniye.
- Yürütücü duvar süresi: 111,2644011 saniye; yaklaşık 1 dakika 51 saniye.
  Başlatma ve son manifest işlemleri bu ölçümün dışında kalabilir.
- Eğitim döngüleri: A 6,330; C 13,426; A uzman-1 7,205;
  C uzman-1 12,159; B 14,941; D 17,526 saniye.
- Altı koşuda 240.000 örnek sunumu; bunlar 40.000 ortak girdinin
  yöntemler arasında tekrar kullanımıdır, bağımsız veri sayısı değildir.
- Her koşulda 2500 uzman güncellemesi; B/D'de ayrıca 2500 yönlendirici adımı.
- C, C uzman-1 ve D toplam 120.000 örnek-başına CPR gradyan hesabı yaptı.
- CPU kullanıldı. Enerji, parasal CPU maliyeti ve süreç tepe belleği
  ölçülmedi. Arayüzdeki birikimli API tutarı deney maliyeti değildir.
- 209 dosyanın SHA-256 ve boyutları manifestle yeniden doğrulandı.
  Manifest hariç toplam 192.751.253 bayt; en büyük dosya 7.838.555 bayt.
- [Manifest](results_control_v05_01/manifest.json) SHA-256:
  143f42ef5c780559cfe0a07eb1a8c46cf77cd89fed43633c18be16ac4ce435a4
- [Yürütme kaydı](results_control_v05_01/execution.json).
- [v0.5 test kanıtı](validation_v05_2026-09-16_01.json):
  113 mekanik test geçti. Test başarısı bilimsel kapı başarısı değildir.

## 7. Öğrenilenler

1. **Bağlı tasarım parametreleri birlikte denetlenmeli.**
   v0.4'te marj eşiği ile dışlama tavanı ayrı makul sayılar olarak
   seçilmişti; 200 adayda kabul bulunamadı. Sonlu havuz başarısızlığı
   matematiksel imkânsızlık değildir.
2. **Jeneratör kabulü öğrenilebilirlik değildir.**
   v0.5 kabulü çözmesine rağmen sabit ağ/bütçe kapıyı geçmedi.
   Farklı öğretmen ve dağılımlardan gelen eski/yeni doğruluk farkları
   filtrenin yalıtılmış nedensel etkisi değildir.
3. **Mekanik hareket davranışsal yarar değildir.**
   CPR hareketi ölçüldü, fakat C bu koşulda A'dan 1,845 puan düşüktü.
   Bu tek çift genel CPR zararı veya sürekli öğrenme başarısızlığı kanıtı değildir.
4. **Göreli kayıp kontrolü mutlak başarı değildir.**
   B/D tek-ağ referanslarına yakındı; referansların kendisi kapıyı geçmedi.
5. **Kayıt, iddia düzeyine uygun olmalı.**
   Ağırlık, optimizer, yerel saat, bellek, RNG ve örnek sıraları
   saklanmadan tam yeniden üretim iddiası kurulamaz.
   Eski marj raporundaki tarihsel tahmin eşitliği iddiası,
   özgün tahmin dizisi yoksa kanıtlanmış sayılmaz.
6. **Önkayıt sadece eşik değil durma disiplinidir.**
   Başarısızlık görüldükten sonra yeni ayar denenmedi.
   Tam ana deney sonucu yerine dürüst bir fizibilite sınırı raporlandı.

Tarihsel notlarda yer alan tam unutma, kesin neden, sıfır kabul olasılığı
veya etkileşimin zorunlu kaybolması gibi güçlü ifadeler güncel sonuç
olarak okunmamalıdır. Gözlemler bu iddiaları tek başına desteklemez.

## 8. Arşiv ve gelecek iş etiketi

[v0.4 ham dış yedeği](BACKUP_V04_VERIFICATION_2026-09-16.json)
11 GitHub sürüm eki geri indirilerek, manifest dahil 3651 dosyada
doğrulandı. Ham veriler Git geçmişine eklenmedi.

[Özgün protokolün Bitcoin tasdiki](OTS_VERIFICATION_2026-09-16.json)
967295 numaralı blokta doğrulandı. İş ispatı/Merkle kontrolü yerelde,
zincir konumu iki HTTPS gezgininde yapıldı; tam düğüm doğrulaması değildir.
Bu makbuz v0.5 belgesinin zaman damgası olarak sunulmaz.

[Kilitli kapsamlı protokol](PREREGISTRATION_DRAFT.md) korunur.
**Gelecek iş — uygulanmayan kapsam:** filtreli süre doğrulaması,
güç pilotu ve ana faktöriyel deney. Bu etiket devam kararı veya
yeniden çalıştırma izni değildir. Hattın kapanışı sonuçlara göre açılmaz.

Önkayıt: [v0.5 son deneme](PREREGISTRATION_V05_2026-09-16.md).
Kilit commit'i: 721aa62c7c1aa6b589f9b051caf7a2f15c74d717.
Koşu kaynak commit'i: b3f43f8f25d36796ccaff64676e4e98c70092057.